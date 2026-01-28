from django.urls import path
from .views import UploadAndAnalyzeView, HistoryView, RegisterView, CustomLoginView, RetrieveAnalysisView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', CustomLoginView.as_view(), name='login'),
    
    # Endpoint for uploading and getting analysis
    path('upload/', UploadAndAnalyzeView.as_view(), name='upload_analyze'),
    
    # Endpoint for fetching history
    path('history/', HistoryView.as_view(), name='history'),
    path('history/<int:pk>/', RetrieveAnalysisView.as_view(), name='history_detail'),
]