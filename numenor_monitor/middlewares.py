import logging
import queue
import threading

from django.utils import timezone

from .models import Request


class RequestLogger:
    """Asynchronous logger for Request instances using a queue and background thread.

    This class manages a queue of request data and processes them in a separate thread
    to avoid blocking the main request-response cycle. It batches inserts for better performance
    and flushes periodically based on time to ensure data is not held indefinitely.

    Attributes:
        queue (queue.Queue): Thread-safe queue for storing request data.
        batch_size (int): Number of records to accumulate before bulk inserting.
        flush_interval (int): Time in seconds to wait before flushing even if batch not full.
        thread (threading.Thread): Background daemon thread for processing the queue.
    """

    def __init__(self, batch_size=10, use_thread=True, flush_interval=60):
        """Initialize the RequestLogger with a queue and optionally start the background
        thread.

        Args:
            batch_size (int): Number of records to batch before inserting into the database.
            use_thread (bool): Whether to use a background thread for processing.
            flush_interval (int): Time in seconds to wait before flushing the batch even if not full.
        """
        self.queue = queue.Queue()
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.last_flush = timezone.now()
        if use_thread:
            self.thread = threading.Thread(
                target=self._process_queue, daemon=True
            )
            self.thread.start()
        else:
            self.thread = None

    def log_request(
        self,
        scheme,
        host,
        path,
        query,
        method,
        ip_address,
        user_agent,
        user,
        username,
        start_at,
        end_at,
        status_code,
        error,
        request_size,
        response_size,
    ):
        """Add request data to the queue for asynchronous processing.

        Args:
            scheme (str): URL scheme.
            host (str): URL host.
            path (str): URL path.
            query (str): Query string.
            method (str): HTTP method.
            ip_address (str): Client IP address.
            user_agent (str): User agent string.
            user (User): Authenticated user, if any.
            username (str): Username of the user.
            start_at (datetime): Start timestamp.
            end_at (datetime): End timestamp.
            status_code (int): HTTP status code.
            error (str): Error response body.
            request_size (int): Request body size.
            response_size (int): Response body size.
        """
        self.queue.put(
            {
                "scheme": scheme,
                "host": host,
                "path": path,
                "query": query,
                "method": method,
                "ip_address": ip_address,
                "user_agent": user_agent,
                "user": user,
                "username": username,
                "start_at": start_at,
                "end_at": end_at,
                "status_code": status_code,
                "error": error,
                "request_size": request_size,
                "response_size": response_size,
            }
        )

    def process_batch(self):
        """Synchronously process the current batch in the queue.

        Useful for tests or manual processing.
        """
        batch = []
        while not self.queue.empty():
            item = self.queue.get()
            batch.append(Request(**item))
            if len(batch) >= self.batch_size:
                Request.objects.bulk_create(batch)
                batch = []
        if batch:
            Request.objects.bulk_create(batch)

    def _process_queue(self):
        """Background thread method to process the queue.

        Continuously checks the queue, accumulates records up to batch_size, and
        performs bulk inserts into the database. Also flushes based on time interval.
        """
        from django.db import connection

        connection.ensure_connection()
        batch = []
        while True:
            try:
                item = self.queue.get(timeout=1)
                batch.append(Request(**item))
                if len(batch) >= self.batch_size:
                    self._flush_batch(batch)
            except queue.Empty:
                pass
            # Check for time-based flush
            if (
                batch
                and (timezone.now() - self.last_flush).total_seconds()
                > self.flush_interval
            ):
                self._flush_batch(batch)

    def _flush_batch(self, batch):
        """Flush the current batch to the database and reset."""
        try:
            Request.objects.bulk_create(batch)
            batch.clear()
            self.last_flush = timezone.now()
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error("Error bulk creating records: %s", e)
            batch.clear()


request_logger = RequestLogger(batch_size=50, flush_interval=5)


class RequestLoggingMiddleware:
    """Middleware to log HTTP requests asynchronously by queuing Request data.

    This middleware intercepts every HTTP request processed by the Django application and queues
    the request details for background processing using a RequestLogger. It is useful for
    monitoring and analyzing web traffic patterns without blocking responses.

    The middleware captures the following information:
    - URL components: scheme, host, path, query string, HTTP method
    - Client details: IP address, user agent
    - Timestamps: start and end processing times
    - Response details: status code, sizes, errors

    Records are batched and inserted asynchronously to handle high traffic efficiently.
    """

    def __init__(self, get_response):
        """Initialize the middleware with the get_response callable.

        Args:
            get_response (callable): The next middleware or view in the chain.
        """
        self.get_response = get_response

    def __call__(self, request):
        """Process the incoming request and response.

        This method is called for each request. It records the start time, calls the next
        middleware/view, records the end time, and then saves a Request.

        Args:
            request (HttpRequest): The incoming HTTP request object.

        Returns:
            HttpResponse: The HTTP response object.
        """
        start_at = timezone.now()
        response = self.get_response(request)
        try:
            end_at = timezone.now()
            status_code = response.status_code
            request_size, response_size = self._calculate_sizes(
                request, response
            )
            error = self._get_error_content(response)
            user, username = self._get_user_info(request)
            # Use asynchronous logging to avoid blocking
            request_logger.log_request(
                scheme=request.scheme,
                host=request.get_host(),
                path=request.path,
                query=request.GET.urlencode(),
                method=request.method,
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get("HTTP_USER_AGENT", ""),
                user=user,
                username=username,
                start_at=start_at,
                end_at=end_at,
                status_code=status_code,
                error=error,
                request_size=request_size,
                response_size=response_size,
            )
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error("Error in RequestLoggingMiddleware: %s", e)
        return response

    def get_client_ip(self, request):
        """Retrieve the client's IP address from the request.

        This method checks for the 'HTTP_X_FORWARDED_FOR' header first (for proxies),
        and falls back to 'REMOTE_ADDR' if not present.

        Args:
            request (HttpRequest): The HTTP request object.

        Returns:
            str: The client's IP address.
        """
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR")
        return ip

    def _calculate_sizes(self, request, response):
        """Calculate request and response sizes.

        Args:
            request (HttpRequest): The HTTP request.
            response (HttpResponse): The HTTP response.

        Returns:
            tuple: (request_size, response_size)
        """
        content_length = request.META.get("CONTENT_LENGTH")
        request_size = (
            int(content_length) if content_length else len(request.body)
        )
        response_size = (
            len(response.content) if hasattr(response, "content") else 0
        )
        return request_size, response_size

    def _get_error_content(self, response):
        """Extract error content from response if status >= 400.

        Args:
            response (HttpResponse): The HTTP response.

        Returns:
            str: Error content or empty string.
        """
        if response.status_code >= 400:
            try:
                return response.content.decode("utf-8")
            except (AttributeError, UnicodeDecodeError):
                return str(response.content)
        return ""

    def _get_user_info(self, request):
        """Get user and username from request.

        Args:
            request (HttpRequest): The HTTP request.

        Returns:
            tuple: (user, username)
        """
        if (
            hasattr(request, "user")
            and request.user
            and request.user.is_authenticated
        ):
            return request.user, request.user.username
        return None, ""
