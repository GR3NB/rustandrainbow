import os
import requests
from dotenv import load_dotenv, set_key

# Ensure we're running in the correct directory
script_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(script_dir, '.env')

# Load existing environment variables
load_dotenv(dotenv_path=env_path)

def refresh_token():
    print("Starting Meta token refresh...")
    
    current_token = os.getenv("META_ACCESS_TOKEN")
    if not current_token:
        print("Error: META_ACCESS_TOKEN not found in .env file.")
        return

    # Call the Instagram Graph API refresh endpoint
    url = f"https://graph.instagram.com/refresh_access_token?grant_type=ig_refresh_token&access_token={current_token}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        data = response.json()
        new_token = data.get("access_token")
        
        if new_token:
            # Update the .env file with the new token
            set_key(env_path, "META_ACCESS_TOKEN", new_token)
            print(f"Success! Token refreshed. Expires in: {data.get('expires_in')} seconds.")
        else:
            print("Error: Failed to parse access_token from response.")
            print(data)
            
    except requests.exceptions.RequestException as e:
        print(f"Error during API call: {e}")
        if e.response is not None:
            print(e.response.text)

if __name__ == "__main__":
    refresh_token()
