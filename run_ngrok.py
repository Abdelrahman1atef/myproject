import os
import time
from threading import Thread
from pyngrok import ngrok, conf
from django.core.management.commands.runserver import Command as Runserver
from django.core.management import execute_from_command_line
import subprocess
# Configuration
CUSTOM_DOMAIN = "locust-eminent-urchin.ngrok-free.app"
NGROK_AUTH_TOKEN = "2paDIwMr0BtDPRstSyqMbislEuw_2rKpoLBvWZtiGjV2DRj9c"  # Replace with your actual token

def start_ngrok():
    """Start ngrok tunnel with custom domain and handle existing sessions"""
    conf.get_default().auth_token = NGROK_AUTH_TOKEN
    conf.get_default().region = "us"

    try:
        # Disconnect existing tunnels
        for tunnel in ngrok.get_tunnels():
            print(f"🔌 Disconnecting existing tunnel: {tunnel.public_url}")
            ngrok.disconnect(tunnel.public_url)
            time.sleep(1)

        # Connect new tunnel
        tunnel = ngrok.connect(8000, "http", hostname=CUSTOM_DOMAIN)
        print(f"\n✅ Ngrok tunnel created: {tunnel.public_url}")
        print("🌐 WebSocket URL: wss://{CUSTOM_DOMAIN}/ws/orders/")

    except Exception as e:
        print(f"❌ Failed to start ngrok tunnel: {e}")
        print("💡 Tip: Make sure no other session is using this custom domain.")

    while True:
        time.sleep(10)

if __name__ == '__main__':
    # Start ngrok in background thread
    Thread(target=start_ngrok, daemon=True).start()

    # Run Django normally (in main thread)
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
    # Run Daphne instead of runserver
    daphne_command = [
        "daphne",
        "-p", "8000",
        "myproject.asgi:application"
    ]

    print("🚀 Starting Daphne ASGI server...")
    subprocess.run(daphne_command)