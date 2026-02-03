from django.http import JsonResponse

def home(request):
    return JsonResponse({
        "message": "Chemical Equipment Visualizer API is running.",
        "status": "online",
        "documentation": "/api/",
        "admin": "/admin/"
    })
