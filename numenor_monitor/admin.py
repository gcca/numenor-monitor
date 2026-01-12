from django.contrib import admin

from .models import Request


@admin.register(Request)
class RequestAdmin(admin.ModelAdmin):
    """Admin configuration for Request model to provide a descriptive interface for
    monitoring HTTP requests.

    This admin class customizes the display and filtering options to make request
    records easily searchable and analyzable. All fields are read-only to prevent
    accidental modifications to logged data.
    """

    # Display fields in the list view
    list_display = (
        "__str__",  # Full URL representation
        "ip_address",
        "username",
        "status_code",
        "method",
        "format_start_at",
        "format_end_at",
        "request_size",
        "response_size",
        "created_at",
    )

    # Fields that can be filtered in the list view
    list_filter = (
        "status_code",
        "scheme",
        "host",
        "start_at",
        "end_at",
        "created_at",
    )

    # Fields that can be searched
    search_fields = (
        "path",
        "query",
        "ip_address",
        "user_agent",
        "username",
        "error",
    )

    # Date hierarchy for easy navigation by date
    date_hierarchy = "created_at"

    # All fields are read-only since this is a log model
    readonly_fields = (
        "scheme",
        "host",
        "path",
        "query",
        "ip_address",
        "user_agent",
        "user",
        "username",
        "start_at",
        "end_at",
        "format_start_at",
        "format_end_at",
        "status_code",
        "error",
        "request_size",
        "response_size",
        "created_at",
    )

    # Fieldsets for organizing the detail view
    fieldsets = (
        (
            "URL Information",
            {
                "fields": ("scheme", "host", "path", "query"),
                "description": "Components of the requested URL.",
            },
        ),
        (
            "Client Information",
            {
                "fields": ("ip_address", "user_agent", "user", "username"),
                "description": "Details about the client making the request.",
            },
        ),
        (
            "Timing and Status",
            {
                "fields": (
                    "format_start_at",
                    "format_end_at",
                    "status_code",
                    "method",
                ),
                "description": "Timestamps and response status.",
            },
        ),
        (
            "Data Sizes and Errors",
            {
                "fields": ("request_size", "response_size", "error"),
                "description": "Sizes of request/response bodies and any error content.",
            },
        ),
        (
            "Metadata",
            {
                "fields": ("created_at",),
                "description": "When this record was logged.",
            },
        ),
    )

    # Custom formatting methods for timestamps with seconds and microseconds
    def format_start_at(self, obj):
        """Format start_at timestamp with seconds and microseconds."""
        return (
            obj.start_at.strftime("%Y-%m-%d %H:%M:%S.%f")
            if obj.start_at
            else ""
        )

    format_start_at.short_description = "Start Time"
    format_start_at.admin_order_field = "start_at"

    def format_end_at(self, obj):
        """Format end_at timestamp with seconds and microseconds."""
        return obj.end_at.strftime("%Y-%m-%d %H:%M:%S.%f") if obj.end_at else ""

    format_end_at.short_description = "End Time"
    format_end_at.admin_order_field = "end_at"

    # Ordering in list view
    ordering = ("-created_at",)

    # Disable add, change, and delete permissions since this is a read-only log
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
