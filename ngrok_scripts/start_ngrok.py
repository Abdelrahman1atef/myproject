# ngrok_scripts.py

from pyngrok import ngrok, conf
import time
import os
from django.core.management.commands.runserver import Command as Runserver

# Configuration (keep these at the top for easy modification)
NGROK_CONFIG = {
    "auth_token": "2paDIwMr0BtDPRstSyqMbislEuw_2rKpoLBvWZtiGjV2DRj9c",  # Replace with your token
    "domain": "locust-eminent-urchin.ngrok-free.app",
    "region": "us",  # ngrok server region
    "port": 8000     # Django runserver port
}

def start_ngrok():
    """Start ngrok tunnel with custom domain"""
    try:
        # Configure ngrok
        conf.get_default().auth_token = NGROK_CONFIG["auth_token"]
        conf.get_default().region = NGROK_CONFIG["region"]

        # Start HTTP tunnel
        tunnel = ngrok.connect(
            NGROK_CONFIG["port"],
            "http",
            hostname=NGROK_CONFIG["domain"]
        )

        print("\n" + "="*50)
        print(f"Ngrok tunnel created: {tunnel.public_url}")
        print(f"WebSocket URL: wss://{NGROK_CONFIG['domain']}/ws/orders/")
        print("="*50 + "\n")

        # Keep tunnel open
        while True:
            time.sleep(10)

    except Exception as e:
        print(f"\nError in ngrok tunnel: {e}\n")

def run_server():
    """Run Django development server"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
    Runserver().handle(addrport=f"0.0.0.0:{NGROK_CONFIG['port']}", use_reloader=False)
