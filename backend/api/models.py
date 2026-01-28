from django.db import models
from django.contrib.auth.models import User

class EquipmentDataset(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    # Stores the uploaded CSV file
    file = models.FileField(upload_to='uploads/')
    # Automatically records when the file was uploaded
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Dataset uploaded at {self.uploaded_at}"