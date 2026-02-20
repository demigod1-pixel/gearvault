from django.contrib import admin, messages
from django.utils.safestring import mark_safe
from .models import Asset, ServiceLog, ServiceImage, MaintenanceTask
from unfold.admin import ModelAdmin, TabularInline
from django.urls import reverse

class MaintenanceTaskInline(TabularInline):
    model = MaintenanceTask
    extra = 0
    readonly_fields = ('miles_until_due', 'completion_button')
    fields = ('task_name', 'interval_miles', 'last_completed_mileage', 'miles_until_due', 'completion_button')

    def completion_button(self, obj):
        if obj.id:
            return mark_safe(f'<a href="/complete-task/{obj.id}/" class="bg-green-600 px-2 py-1 rounded text-white text-xs">✅ Done</a>')
        return ""
    completion_button.short_description = "Action"

@admin.register(Asset)
class AssetAdmin(ModelAdmin):
    inlines = [MaintenanceTaskInline]
    # The 'dossier_preview' is now the first field
    readonly_fields = ('dossier_preview', 'year', 'make', 'model')
    list_display = ('name', 'make', 'model', 'current_reading', 'next_service_alert', 'big_dossier_button')
    actions = ['fetch_ai_maintenance_schedule']

    fieldsets = (
        ('Dossier Snapshot', {
            'fields': ('dossier_preview',),
        }),
        ('Vehicle Information', {
            'fields': (('name', 'asset_type'), ('vin_hin', 'current_reading'), ('year', 'make', 'model')),
        }),
        ('Appearance & Paint', {
            'fields': (('primary_color', 'primary_paint_code'), ('secondary_color', 'secondary_paint_code')),
        }),
    )

    def dossier_preview(self, obj):
        if not obj.pk: return "Save asset to generate preview."
        
        logs = obj.logs.all()
        total_investment = sum(log.total_cost for log in logs)
        tasks = obj.tasks.all()
        
        # Calculate Grade
        if tasks.exists():
            up_to_date = sum(1 for t in tasks if t.miles_until_due >= 0)
            score = (up_to_date / tasks.count()) * 100
            grade = "A+" if score == 100 else "A" if score >= 80 else "B" if score >= 60 else "C" if score >= 40 else "F"
            color = "#4ADE80" if score >= 80 else "#FACC15" if score >= 60 else "#F87171"
        else:
            grade, color = "N/A", "#9CA3AF"

        return mark_safe(f'''
            <div style="background: #1e293b; padding: 20px; border-radius: 12px; border: 1px solid #334155; display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <h3 style="color: #94a3b8; margin: 0; font-size: 12px; text-transform: uppercase;">Total Investment</h3>
                    <p style="color: white; font-size: 24px; font-weight: bold; margin: 5px 0;">${total_investment:,.2f}</p>
                    <span style="color: #64748b; font-size: 11px;">{logs.count()} Verified Records</span>
                </div>
                <div style="text-align: center; border-left: 1px solid #334155; padding-left: 40px;">
                    <h3 style="color: #94a3b8; margin: 0; font-size: 12px; text-transform: uppercase;">Health Grade</h3>
                    <p style="color: {color}; font-size: 32px; font-weight: bold; margin: 5px 0;">{grade}</p>
                </div>
            </div>
        ''')
    dossier_preview.short_description = "Live Status"

    def big_dossier_button(self, obj):
        url = reverse('dossier', args=[obj.id])
        return mark_safe(f'<a href="{url}" style="background-color: #2563eb; color: white; padding: 6px 14px; border-radius: 6px; font-weight: bold; text-decoration: none; display: inline-block; font-size: 11px;">📄 DOWNLOAD DOSSIER</a>')
    big_dossier_button.short_description = "Quick Export"

    def next_service_alert(self, obj):
        tasks = obj.tasks.all()
        if not tasks: return "No Tasks"
        urgent = sorted(tasks, key=lambda t: t.miles_until_due)[0]
        color = "#F87171" if urgent.miles_until_due < 500 else "#4ADE80"
        return mark_safe(f'<b style="color: {color};">{urgent.task_name}</b>')

@admin.register(ServiceLog)
class ServiceLogAdmin(ModelAdmin):
    list_display = ('asset', 'date', 'meter_reading', 'total_cost')

admin.site.register(MaintenanceTask)