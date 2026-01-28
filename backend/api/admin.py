from django.contrib import admin
from .models import EquipmentDataset

@admin.register(EquipmentDataset)
class EquipmentDatasetAdmin(admin.ModelAdmin):
    list_display = ('id', 'uploaded_at', 'file')
    ordering = ('-uploaded_at',)