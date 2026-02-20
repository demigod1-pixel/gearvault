from django.test import TestCase, Client
from django.contrib.auth.models import User
from core.models import Asset, MaintenanceTask, ServiceLog
from unittest.mock import patch

class AssetTests(TestCase):
    def setUp(self):
        # Create a user to own assets
        self.user = User.objects.create_user(username='testuser', password='password')
        self.client = Client()
        self.client.login(username='testuser', password='password')

    @patch('requests.get')
    def test_vin_decoding(self, mock_get):
        # Mock NHTSA API response
        mock_response = {
            'Results': [
                {'Variable': 'Make', 'Value': 'HONDA'},
                {'Variable': 'Model', 'Value': 'ACCORD'},
                {'Variable': 'Model Year', 'Value': '2003'}
            ]
        }
        mock_get.return_value.json.return_value = mock_response
        
        asset = Asset.objects.create(
            owner=self.user,
            name='Test Car',
            asset_type='CAR',
            vin_hin='1HGCM82633A004352',
            current_reading=100000
        )
        
        # Verify that VIN decoding populated the fields
        self.assertEqual(asset.make, 'HONDA')
        self.assertEqual(asset.model, 'ACCORD')
        self.assertEqual(asset.year, '2003')

    def test_paint_codes(self):
        asset = Asset.objects.create(
            owner=self.user,
            name='Blue Truck',
            asset_type='CAR',
            current_reading=500,
            primary_color='Blue',
            primary_paint_code='B-500',
            secondary_color='Silver',
            secondary_paint_code='S-200'
        )
        self.assertEqual(asset.primary_color, 'Blue')
        self.assertEqual(asset.primary_paint_code, 'B-500')
        self.assertEqual(asset.secondary_color, 'Silver')

    def test_maintenance_math(self):
        asset = Asset.objects.create(
            owner=self.user,
            name='Test Bike',
            asset_type='MOTORCYCLE',
            current_reading=1000
        )
        task = MaintenanceTask.objects.create(
            asset=asset,
            task_name='Chain Lube',
            interval_miles=500,
            last_completed_mileage=800
        )
        # Due at 800 + 500 = 1300. Current is 1000. Remaining = 300.
        self.assertEqual(task.miles_until_due, 300)

    def test_task_completion_view(self):
        asset = Asset.objects.create(
            owner=self.user,
            name='Test Boat',
            asset_type='BOAT',
            current_reading=500
        )
        task = MaintenanceTask.objects.create(
            asset=asset,
            task_name='Oil Change',
            interval_miles=100,
            last_completed_mileage=0
        )
        
        # 1. GET request should return 200 (render form)
        response_get = self.client.get(f'/complete-task/{task.id}/')
        self.assertEqual(response_get.status_code, 200)

        # 2. POST request with cost
        response_post = self.client.post(f'/complete-task/{task.id}/', {
            'cost': '150.50',
            'notes': 'Oil and Filter'
        })
        
        # Should redirect back to admin asset page
        self.assertEqual(response_post.status_code, 302)
        
        # Verify task updated
        task.refresh_from_db()
        self.assertEqual(task.last_completed_mileage, 500)
        
        # Verify log created with correct cost
        log = ServiceLog.objects.get(asset=asset, description__contains='Oil and Filter')
        self.assertEqual(float(log.total_cost), 150.50)

    def test_dossier_generation(self):
        asset = Asset.objects.create(
            owner=self.user,
            name='Test PDF',
            asset_type='EQUIP',
            current_reading=0
        )
        ServiceLog.objects.create(
            asset=asset,
            meter_reading=100,
            description="Test Log",
            total_cost=50.00
        )
        
        response = self.client.get(f'/dossier/{asset.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
