#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
from threading import Thread
from ngrok_scripts.start_ngrok import start_ngrok  # Import the ngrok function

def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myproject.settings")

    # Start ngrok in a separate thread, but prevent duplicate runs with autoreload
    if os.environ.get("RUN_MAIN") != "true":
        ngrok_thread = Thread(target=start_ngrok)
        ngrok_thread.daemon = True
        ngrok_thread.start()

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)

if __name__ == "__main__":
    main()
# 
# def main():
#     """Run administrative tasks."""
#     os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
#     try:
#         from django.core.management import execute_from_command_line
#     except ImportError as exc:
#         raise ImportError(
#             "Couldn't import Django. Are you sure it's installed and "
#             "available on your PYTHONPATH environment variable? Did you "
#             "forget to activate a virtual environment?"
#         ) from exc
#     execute_from_command_line(sys.argv)


# if __name__ == '__main__':
#     main()
