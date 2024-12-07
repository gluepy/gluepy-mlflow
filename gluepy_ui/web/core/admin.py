from django.contrib import admin
from .models import Run


@admin.register(Run)
class RunAdmin(admin.ModelAdmin):
    list_display = ('run_id', 'dag', 'username', 'created_at', 'updated_at')
    search_fields = ('run_id', 'dag', 'username')
    list_filter = ('dag', 'username', 'created_at')
