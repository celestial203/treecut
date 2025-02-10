import os
import sys
from pathlib import Path

# Get the absolute path of the project root directory
current_path = Path(__file__).resolve().parent
project_path = current_path.parent

# Add the project root directory to Python path
if str(project_path) not in sys.path:
    sys.path.append(str(project_path))

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'base.settings')

application = get_wsgi_application() 