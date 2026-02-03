from django.http import JsonResponse
from django.shortcuts import redirect
from django.conf import settings

def home(request):
    url = getattr(settings, "FRONTEND_URL", "")
    if url:
        return redirect(url)
    return JsonResponse({"message": "Chemical Equipment Visualizer API is running.", "status": "online", "documentation": "/api/", "admin": "/admin/"})
