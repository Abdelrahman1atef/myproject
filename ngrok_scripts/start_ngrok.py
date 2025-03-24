from pyngrok import ngrok, conf, exception
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
        
        # Configure ngrok with the custom domain
        custom_domain = "locust-eminent-urchin.ngrok-free.app"
        pyngrok_config = conf.PyngrokConfig()
        pyngrok_config.region = "us"  # Optional: Set the region (e.g., "us", "eu")
        
        # Start the tunnel with the custom domain
        current_tunnel = ngrok.connect(8000, "http", hostname=custom_domain, pyngrok_config=pyngrok_config)
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