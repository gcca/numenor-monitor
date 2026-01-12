import json

from django.http import Http404, JsonResponse
from django.views.decorators.csrf import csrf_exempt


def simple_get(request):
    """Simple GET view returning JSON."""
    return JsonResponse({"message": "Simple GET request", "status": "success"})


def get_with_query(request):
    """GET view that processes query parameters."""
    q = request.GET.get("q", "default")
    return JsonResponse({"message": f"Query: {q}", "status": "success"})


@csrf_exempt
def post_with_data(request):
    """POST view that processes JSON data."""
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            return JsonResponse(
                {"message": "Data received", "data": data, "status": "success"}
            )
        except json.JSONDecodeError:
            return JsonResponse(
                {"message": "Invalid JSON", "status": "error"}, status=400
            )
    return JsonResponse(
        {"message": "Method not allowed", "status": "error"}, status=405
    )


def cause_404(request):
    """View that raises 404 error."""
    raise Http404("Page not found")


def cause_500(request):
    """View that causes 500 error."""
    raise Exception("Internal server error")


def large_response(request):
    """View that returns a large response."""
    large_data = {"data": "x" * 10000}  # Large content
    return JsonResponse(large_data)


@csrf_exempt
def large_request(request):
    """POST view expecting large request body."""
    if request.method == "POST":
        body_size = len(request.body)
        return JsonResponse(
            {"message": f"Received {body_size} bytes", "status": "success"}
        )
    return JsonResponse(
        {"message": "Method not allowed", "status": "error"}, status=405
    )
