from pyngrok import ngrok, exception
import time

# Variable to store the current tunnel, to disconnect it when necessary
current_tunnel = None

def start_ngrok():
    global current_tunnel

    try:
        # Disconnect any existing tunnel first
        if current_tunnel:
            ngrok.disconnect(current_tunnel.public_url)
            print(f"Disconnected previous tunnel: {current_tunnel.public_url}")
        
        # Open a new HTTP tunnel (port 8000 for example)
        current_tunnel = ngrok.connect(8000)
        print(f"Public URL: {current_tunnel.public_url}")

        # Keep the ngrok process running
        while True:
            time.sleep(1)

    except exception.PyngrokNgrokError as e:
        print(f"Failed to start Ngrok tunnel: {e}")

    finally:
        # Ensure the ngrok tunnel is disconnected when the program ends
        if current_tunnel:
            ngrok.disconnect(current_tunnel.public_url)
            print(f"Ngrok tunnel {current_tunnel.public_url} closed.")
