"""URL configuration for project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import include, path

from . import test_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("numenor_monitor.urls")),
    # Test views
    path("test/simple/", test_views.simple_get, name="simple_get"),
    path("test/query/", test_views.get_with_query, name="get_with_query"),
    path("test/post/", test_views.post_with_data, name="post_with_data"),
    path("test/404/", test_views.cause_404, name="cause_404"),
    path("test/500/", test_views.cause_500, name="cause_500"),
    path(
        "test/large-response/", test_views.large_response, name="large_response"
    ),
    path("test/large-request/", test_views.large_request, name="large_request"),
]
