from django.db import models


class Request(models.Model):
    """Model to store records of HTTP requests in the Numenor Monitor web application.

    This model captures details of each HTTP request, including the URL components and client information.
    It is designed to log and analyze request patterns for monitoring purposes.

    Attributes:
        scheme (str): The scheme of the URL (e.g., 'http' or 'https').
        host (str): The host part of the URL (e.g., 'example.com').
        path (str): The path part of the URL (e.g., '/path/to/resource').
        query (str): The query string of the URL (e.g., 'param1=value1&param2=value2').
        method (str): The HTTP method used in the request (e.g., 'GET', 'POST', 'PUT', 'DELETE').
        ip_address (str): The IP address of the client making the request.
        user_agent (str): The user agent string from the request headers.
        user (User): The authenticated user making the request, if any.
        username (str): The username of the authenticated user, if any.
        start_at (datetime): The timestamp when the request started processing.
        end_at (datetime): The timestamp when the response was sent.
        status_code (int): The HTTP status code of the response.
        error (str): The response body if an error occurred (status >= 400).
        request_size (int): The size of the request body in bytes.
        response_size (int): The size of the response body in bytes.
        created_at (datetime): The timestamp when the record was created.
    """

    scheme = models.CharField(
        max_length=10,
        help_text="The protocol scheme of the URL, such as 'http' or 'https'.",
    )
    host = models.CharField(
        max_length=255,
        help_text="The host or domain name of the URL, e.g., 'example.com'.",
    )
    path = models.CharField(
        max_length=2048,
        help_text="The path component of the URL, e.g., '/api/v1/users'.",
    )
    query = models.TextField(
        blank=True,
        help_text="The query string of the URL, e.g., 'key1=value1&key2=value2'. Leave blank if none.",
    )
    method = models.CharField(
        max_length=10,
        null=True,
        blank=True,
        help_text="The HTTP method used in the request, e.g., 'GET', 'POST', 'PUT', 'DELETE'.",
    )
    ip_address = models.GenericIPAddressField(
        help_text="The IP address of the client that accessed the URL."
    )
    user_agent = models.TextField(
        blank=True,
        help_text="The user agent string from the HTTP request headers.",
    )
    user = models.ForeignKey(
        "auth.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="The authenticated user making the request, if any.",
    )
    username = models.CharField(
        max_length=150,
        blank=True,
        help_text="The username of the authenticated user, copied for logging purposes.",
    )
    start_at = models.DateTimeField(
        help_text="The timestamp when the request started processing."
    )
    end_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="The timestamp when the response was sent.",
    )
    status_code = models.IntegerField(
        help_text="The HTTP status code of the response (e.g., 200, 404)."
    )
    error = models.TextField(
        blank=True,
        help_text="The response body content if an error occurred (status >= 400).",
    )
    request_size = models.PositiveIntegerField(
        default=0, help_text="The size of the request body in bytes."
    )
    response_size = models.PositiveIntegerField(
        default=0, help_text="The size of the response body in bytes."
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="The date and time when this record was first created.",
    )

    class Meta:
        """Meta options for the Request model.

        Provides ordering and verbose names for better admin interface and queries.
        """

        ordering = ["-created_at"]
        verbose_name = "Request"
        verbose_name_plural = "Requests"

    def __str__(self):
        """String representation of the Request instance.

        Returns a formatted string showing the full URL.
        """
        query_part = f"?{self.query}" if self.query else ""
        return f"{self.scheme}://{self.host}{self.path}{query_part}"
