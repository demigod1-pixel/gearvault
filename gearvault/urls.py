from django.contrib import admin
from django.urls import path
from core.views import landing_page, generate_full_dossier, mark_task_completed

urlpatterns = [
    path('', landing_page, name='landing'),
    path('admin/', admin.site.urls),
    path('dossier/<int:asset_id>/', generate_full_dossier, name='dossier'),
    path('complete-task/<int:task_id>/', mark_task_completed, name='complete_task'),
]