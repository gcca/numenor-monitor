from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase
from django.utils import timezone

from numenor_monitor.middlewares import RequestLogger, RequestLoggingMiddleware
from numenor_monitor.models import Request


class RequestModelTest(TestCase):
    """Test cases for the Request model."""

    def test_request_creation(self):
        """Test creating a Request instance with all fields."""
        user = User.objects.create_user(username="testuser")
        start_time = timezone.now()
        end_time = timezone.now()
        record = Request.objects.create(
            scheme="https",
            host="example.com",
            path="/test",
            query="param=value",
            method="GET",
            remote_addr="192.168.1.1",
            x_forwarded_for="10.0.0.1, 192.168.1.1",
            cf_connecting_ip="10.0.0.1",
            user_agent="Test Agent",
            user=user,
            username=user.username,
            start_at=start_time,
            end_at=end_time,
            status_code=200,
            error="",
            request_size=100,
            response_size=500,
        )
        self.assertEqual(record.scheme, "https")
        self.assertEqual(record.host, "example.com")
        self.assertEqual(record.path, "/test")
        self.assertEqual(record.query, "param=value")
        self.assertEqual(record.method, "GET")
        self.assertEqual(record.remote_addr, "192.168.1.1")
        self.assertEqual(record.x_forwarded_for, "10.0.0.1, 192.168.1.1")
        self.assertEqual(record.cf_connecting_ip, "10.0.0.1")
        self.assertEqual(record.user_agent, "Test Agent")
        self.assertEqual(record.user, user)
        self.assertEqual(record.username, user.username)
        self.assertEqual(record.start_at, start_time)
        self.assertEqual(record.end_at, end_time)
        self.assertEqual(record.status_code, 200)
        self.assertEqual(record.error, "")
        self.assertEqual(record.request_size, 100)
        self.assertEqual(record.response_size, 500)
        self.assertIsNotNone(record.created_at)

    def test_request_str(self):
        """Test the string representation of Request."""
        start_time = timezone.now()
        record = Request.objects.create(
            scheme="http",
            host="test.com",
            path="/path",
            query="",
            remote_addr="127.0.0.1",
            x_forwarded_for=None,
            cf_connecting_ip=None,
            user_agent="",
            start_at=start_time,
            status_code=200,
            error="",
            request_size=0,
            response_size=100,
        )
        self.assertEqual(str(record), "http://test.com/path")

    def test_request_str_with_query(self):
        """Test the string representation with query string."""
        start_time = timezone.now()
        record = Request.objects.create(
            scheme="https",
            host="example.com",
            path="/search",
            query="q=test",
            remote_addr="127.0.0.1",
            x_forwarded_for=None,
            cf_connecting_ip=None,
            user_agent="",
            start_at=start_time,
            status_code=200,
            error="",
            request_size=0,
            response_size=200,
        )
        self.assertEqual(str(record), "https://example.com/search?q=test")


class RequestLoggerTest(TestCase):
    """Test cases for the RequestLogger class."""

    def setUp(self):
        """Set up test fixtures."""
        self.logger = RequestLogger(batch_size=2, use_thread=False)

    def tearDown(self):
        """Clean up after tests."""
        pass

    def test_log_request_queues_data(self):
        """Test that log_request adds data to the queue."""
        start_time = timezone.now()
        end_time = timezone.now()
        self.logger.log_request(
            "http",
            "test.com",
            "/path",
            "q=1",
            "GET",
            "127.0.0.1",
            "10.0.0.1, 192.168.1.1",
            "10.0.0.1",
            "Agent",
            None,
            "",
            start_time,
            end_time,
            200,
            "",
            0,
            100,
        )
        self.assertEqual(self.logger.queue.qsize(), 1)

    def test_batch_processing(self):
        """Test that batch processing works and creates records."""
        start_time = timezone.now()
        end_time = timezone.now()
        self.logger.log_request(
            "http",
            "test.com",
            "/path1",
            "",
            "GET",
            "127.0.0.1",
            None,
            None,
            "",
            None,
            "",
            start_time,
            end_time,
            200,
            "",
            0,
            100,
        )
        self.logger.log_request(
            "http",
            "test.com",
            "/path2",
            "",
            "POST",
            "127.0.0.1",
            None,
            None,
            "",
            None,
            "",
            start_time,
            end_time,
            200,
            "",
            0,
            100,
        )
        self.logger.process_batch()
        self.assertEqual(Request.objects.count(), 2)

    def test_flush_batch_success(self):
        """Test that _flush_batch works on success."""
        batch = [
            Request(
                scheme="http",
                host="test.com",
                path="/",
                query="",
                method="GET",
                remote_addr="127.0.0.1",
                x_forwarded_for=None,
                cf_connecting_ip=None,
                user_agent="",
                start_at=timezone.now(),
                status_code=200,
                error="",
                request_size=0,
                response_size=0,
            )
        ]
        initial_count = Request.objects.count()
        self.logger._flush_batch(batch)
        self.assertEqual(len(batch), 0)
        self.assertEqual(Request.objects.count(), initial_count + 1)

    @patch("numenor_monitor.models.Request.objects.bulk_create")
    def test_flush_batch_exception_handling(self, mock_bulk_create):
        """Test that _flush_batch handles exceptions gracefully."""
        mock_bulk_create.side_effect = Exception("DB error")
        batch = [
            Request(
                scheme="http",
                host="test.com",
                path="/",
                query="",
                method="GET",
                remote_addr="127.0.0.1",
                x_forwarded_for=None,
                cf_connecting_ip=None,
                user_agent="",
                start_at=timezone.now(),
                status_code=200,
                error="",
                request_size=0,
                response_size=0,
            )
        ]
        self.logger._flush_batch(batch)
        self.assertEqual(len(batch), 0)
        mock_bulk_create.assert_called_once()

    def test_batch_size_flush(self):
        """Test that process_batch flushes when batch size is reached."""
        self.logger.batch_size = 1
        start_time = timezone.now()
        self.logger.log_request(
            "http",
            "test.com",
            "/path",
            "",
            "GET",
            "127.0.0.1",
            None,
            None,
            "",
            None,
            "",
            start_time,
            start_time,
            200,
            "",
            0,
            100,
        )
        self.logger.process_batch()
        self.assertEqual(Request.objects.count(), 1)


class RequestLoggingMiddlewareTest(TestCase):
    """Test cases for the RequestLoggingMiddleware."""

    def setUp(self):
        """Set up test fixtures."""
        self.factory = RequestFactory()
        self.middleware = RequestLoggingMiddleware(lambda r: None)

    def test_middleware_call(self):
        """Test the __call__ method of the middleware."""
        request = self.factory.get("/test/")
        request.user = None
        from django.http import HttpResponse
        self.middleware.get_response = lambda r: HttpResponse(status=200)
        response = self.middleware(request)
        self.assertEqual(response.status_code, 200)

    def test_middleware_call_with_user(self):
        """Test the __call__ method with authenticated user."""
        user = User.objects.create_user(username="testuser")
        request = self.factory.get("/test/")
        request.user = user
        from django.http import HttpResponse
        self.middleware.get_response = lambda r: HttpResponse(status=200)
        response = self.middleware(request)
        self.assertEqual(response.status_code, 200)

    def test_middleware_call_with_error(self):
        """Test the __call__ method with error response."""
        request = self.factory.get("/test/")
        request.user = None
        from django.http import HttpResponse
        self.middleware.get_response = lambda r: HttpResponse(
            status=404, content=b"Error"
        )
        response = self.middleware(request)
        self.assertEqual(response.status_code, 404)

    @patch("numenor_monitor.middlewares.request_logger.log_request")
    def test_middleware_exception_handling(self, mock_log_request):
        """Test that middleware handles exceptions in logging gracefully."""
        mock_log_request.side_effect = Exception("Logging error")
        request = self.factory.get("/test/")
        request.user = None
        from django.http import HttpResponse
        self.middleware.get_response = lambda r: HttpResponse(status=200)
        with self.assertLogs(
            "numenor_monitor.middlewares", level="ERROR"
        ) as cm:
            response = self.middleware(request)
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "Error in RequestLoggingMiddleware: Logging error", cm.output[0]
        )

    @patch("numenor_monitor.middlewares.request_logger.log_request")
    def test_x_forwarded_for(self, mock_log):
        """Test X-Forwarded-For header is passed correctly."""
        request = self.factory.get("/")
        request.META["HTTP_X_FORWARDED_FOR"] = "10.0.0.1, 192.168.1.1"
        request.META["REMOTE_ADDR"] = "192.168.1.1"
        from django.http import HttpResponse
        self.middleware.get_response = lambda r: HttpResponse(status=200)
        self.middleware(request)
        mock_log.assert_called_once()
        call_args = mock_log.call_args[1]
        self.assertEqual(call_args["x_forwarded_for"], "10.0.0.1, 192.168.1.1")
        self.assertEqual(call_args["remote_addr"], "192.168.1.1")

    @patch("numenor_monitor.middlewares.request_logger.log_request")
    def test_cf_connecting_ip(self, mock_log):
        """Test CF-Connecting-IP header is passed correctly."""
        request = self.factory.get("/")
        request.META["HTTP_CF_CONNECTING_IP"] = "203.0.113.5"
        request.META["REMOTE_ADDR"] = "192.168.1.1"
        from django.http import HttpResponse
        self.middleware.get_response = lambda r: HttpResponse(status=200)
        self.middleware(request)
        mock_log.assert_called_once()
        call_args = mock_log.call_args[1]
        self.assertEqual(call_args["cf_connecting_ip"], "203.0.113.5")
        self.assertEqual(call_args["remote_addr"], "192.168.1.1")

    @patch("numenor_monitor.middlewares.request_logger.log_request")
    def test_remote_addr_fallback(self, mock_log):
        """Test REMOTE_ADDR is used when no proxy headers present."""
        request = self.factory.get("/")
        request.META["REMOTE_ADDR"] = "192.168.1.100"
        from django.http import HttpResponse
        self.middleware.get_response = lambda r: HttpResponse(status=200)
        self.middleware(request)
        call_args = mock_log.call_args[1]
        self.assertEqual(call_args["remote_addr"], "192.168.1.100")
        self.assertIsNone(call_args["x_forwarded_for"])
        self.assertIsNone(call_args.get("cf_connecting_ip"))
