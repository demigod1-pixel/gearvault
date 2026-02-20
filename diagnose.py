import os
import sys
import django
from django.conf import settings
from django.core.management import call_command

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gearvault.settings')
django.setup()

try:
    print("Attempting makemigrations...")
    call_command('makemigrations', 'core', verbosity=3)
    print("Makemigrations finished.")
except Exception as e:
    print(f"Error: {e}")
