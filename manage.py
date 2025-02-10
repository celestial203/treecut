#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    # Add the current directory to Python path
    current_path = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, current_path)
    
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'base.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
