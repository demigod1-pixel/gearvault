import os
import sys

# cPanel/Passenger needs to know where the app is
sys.path.insert(0, os.path.dirname(__file__))

from gearvault.wsgi import application
