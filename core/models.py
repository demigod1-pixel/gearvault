from django.db import models
from django.contrib.auth.models import User
import requests

class Asset(models.Model):
    ASSET_TYPES = [('CAR', 'Car'), ('BOAT', 'Boat'), ('MOTORCYCLE', 'Motorcycle'), ('EQUIP', 'Equipment')]
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assets')
    name = models.CharField(max_length=100)
    asset_type = models.CharField(max_length=15, choices=ASSET_TYPES)
    vin_hin = models.CharField(max_length=50, verbose_name="VIN / HIN / Serial")
    year = models.CharField(max_length=4, blank=True, null=True)
    make = models.CharField(max_length=50, blank=True, null=True)
    model = models.CharField(max_length=50, blank=True, null=True)
    current_reading = models.FloatField(default=0, verbose_name="Current Odometer/Hours")
    
    # Paint & Appearance
    primary_color = models.CharField(max_length=30, blank=True, null=True)
    primary_paint_code = models.CharField(max_length=30, blank=True, null=True, help_text="Manufacturer Paint Code")
    secondary_color = models.CharField(max_length=30, blank=True, null=True)
    secondary_paint_code = models.CharField(max_length=30, blank=True, null=True, help_text="Secondary/Trim Paint Code")
    
    def save(self, *args, **kwargs):
        # Automated VIN Decoding Logic
        if self.asset_type in ['CAR', 'MOTORCYCLE'] and self.vin_hin and not self.make:
            try:
                url = f"https://vpic.nhtsa.dot.gov/api/vehicles/decodevin/{self.vin_hin}?format=json"
                response = requests.get(url, timeout=5).json()
                data = {item['Variable']: item['Value'] for item in response.get('Results', []) if item['Value']}
                self.make = data.get('Make')
                self.model = data.get('Model')
                self.year = data.get('Model Year')
            except:
                pass
        super().save(*args, **kwargs)

    def __str__(self):
        # Safeguard against None values during display
        return f"{self.name} ({self.year or ''} {self.make or ''} {self.model or ''})"

class MaintenanceTask(models.Model):
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='tasks')
    task_name = models.CharField(max_length=100)
    interval_miles = models.IntegerField(default=0, help_text="Repeat every X miles/hours")
    last_completed_mileage = models.IntegerField(default=0)

    @property
    def miles_until_due(self):
        # SAFEGUARD: Use 'or 0' to prevent NoneType math errors
        interval = self.interval_miles or 0
        last_done = self.last_completed_mileage or 0
        current = self.asset.current_reading or 0
        return (last_done + interval) - current

    def __str__(self):
        return f"{self.task_name} (Every {self.interval_miles or 0})"

class ServiceLog(models.Model):
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='logs')
    date = models.DateField(auto_now_add=True) # Now uses Eastern Time
    meter_reading = models.FloatField()
    description = models.TextField()
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)

class ServiceImage(models.Model):
    log = models.ForeignKey(ServiceLog, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='service_photos/')