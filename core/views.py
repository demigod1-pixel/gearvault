from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.http import HttpResponse
from .models import Asset, MaintenanceTask, ServiceLog
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import LETTER

def mark_task_completed(request, task_id):
    task = get_object_or_404(MaintenanceTask, id=task_id)
    asset = task.asset

    if request.method == 'POST':
        cost = request.POST.get('cost', 0)
        notes = request.POST.get('notes', f"Completed: {task.task_name}")
        
        ServiceLog.objects.create(
            asset=asset,
            meter_reading=asset.current_reading,
            description=notes,
            total_cost=cost
        )
        task.last_completed_mileage = asset.current_reading
        task.save()
        messages.success(request, f"Task '{task.task_name}' logged with cost ${cost}.")
        return redirect(f'/admin/core/asset/{asset.id}/change/')

    return render(request, 'core/complete_task.html', {'task': task})

def generate_full_dossier(request, asset_id):
    asset = get_object_or_404(Asset, id=asset_id)
    logs = asset.logs.all().order_by('-date')
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{asset.make}_{asset.model}_Dossier.pdf"'
    p = canvas.Canvas(response, pagesize=LETTER)
    width, height = LETTER
    p.setFont("Helvetica-Bold", 20)
    p.drawString(50, height - 50, f"Vehicle Maintenance Dossier")
    p.setFont("Helvetica", 12)
    p.drawString(50, height - 70, f"{asset.year} {asset.make} {asset.model} | VIN: {asset.vin_hin}")
    p.line(50, height - 80, 550, height - 80)
    y = height - 120
    for log in logs:
        p.drawString(50, y, f"{log.date} - {log.meter_reading} miles: {log.description}")
        y -= 25
        if y < 60: 
            p.showPage()
            y = height - 50
    p.showPage()
    p.save()
    return response

def landing_page(request):
    return render(request, 'landing.html')