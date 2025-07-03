import requests
import os
import subprocess
import time
import json
from datetime import datetime

# --- Configuration ---
# Define groups of WireGuard config files and their corresponding API endpoints.
# Each tuple contains (config_file_name, API_URL, description_of_api, key_to_extract_from_json)
# If key_to_extract_from_json is None, the full JSON response will be saved.
TEST_CONFIGS = [
    # Group 1: IP Geo-location API
    ("ch-zrh-wg-001.conf", "http://ip-api.com/json", "IP Geo-location", ["query", "country", "city"]),
    ("ch-zrh-wg-004.conf", "http://ip-api.com/json", "IP Geo-location", ["query", "country", "city"]),
    ("ch-zrh-wg-404.conf", "http://ip-api.com/json", "IP Geo-location", ["query", "country", "city"]),

    # Group 2: Random Cat Fact API
    ("us-phx-wg-101.conf", "https://catfact.ninja/fact", "Random Cat Fact", "fact"),
    ("us-phx-wg-103.conf", "https://catfact.ninja/fact", "Random Cat Fact", "fact"),
    ("us-phx-wg-202.conf", "https://catfact.ninja/fact", "Random Cat Fact", "fact"),

    # Group 3: World Time by IP API
    ("us-sjc-wg-002.conf", "http://worldtimeapi.org/api/ip", "World Time by IP", ["datetime", "timezone"]),
    ("us-sjc-wg-302.conf", "http://worldtimeapi.org/api/ip", "World Time by IP", ["datetime", "timezone"]),
    ("us-sjc-wg-504.conf", "http://worldtimeapi.org/api/ip", "World Time by IP", ["datetime", "timezone"]),
]

# The name of the file where results will be saved.
# This file will be created/overwritten in the repository.
RESULTS_FILE = "vpn_test_results.txt"

# Time to wait after bringing up a VPN tunnel before testing connectivity (in seconds).
# This allows the VPN connection to establish.
VPN_SETUP_WAIT_TIME = 5

# --- Script Logic ---
def run_connectivity_test():
    """
    Runs connectivity and API tests for each specified WireGuard config using wg-quick.
    This script is designed to run in environments like GitHub Actions where
    wg-quick is available and can be run with sudo permissions.
    """
    print(f"Starting WireGuard connectivity and API tests. Results will be saved to '{RESULTS_FILE}'.")
    print("-" * 70)

    results = []
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    results.append(f"--- VPN & API Test Run: {current_time} ---")
    results.append(f"Total configs to test: {len(TEST_CONFIGS)}\n")

    for config_file, api_url, api_description, json_key_or_keys in TEST_CONFIGS:
        config_path = os.path.join(os.getcwd(), config_file)
        print(f"Processing '{config_file}' for {api_description} API ({api_url})...")
        results.append(f"Config: {config_file}")
        results.append(f"  API Test: {api_description} ({api_url})")

        # --- Bring up WireGuard Tunnel ---
        up_command = ['sudo', 'wg-quick', 'up', config_path]
        up_process = subprocess.run(up_command, capture_output=True, text=True, check=False)

        if up_process.returncode != 0:
            status = "VPN_UP_FAILED"
            detail = f"Error bringing up VPN: {up_process.stderr.strip()}"
            print(f"  {status}: {detail}")
            results.append(f"  Status: {status}")
            results.append(f"  Detail: {detail}\n")
            continue # Skip to the next config if VPN failed to come up

        print(f"  VPN tunnel for '{config_file}' brought up successfully. Waiting {VPN_SETUP_WAIT_TIME} seconds...")
        time.sleep(VPN_SETUP_WAIT_TIME) # Give VPN time to establish

        # --- Test API Connectivity and Data Retrieval ---
        api_data = "N/A"
        try:
            response = requests.get(api_url, timeout=15) # 15-second timeout for the request
            response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
            
            json_response = response.json()
            
            if isinstance(json_key_or_keys, list):
                extracted_data = {}
                for key in json_key_or_keys:
                    if key in json_response:
                        extracted_data[key] = json_response[key]
                    else:
                        extracted_data[key] = "Key Not Found"
                api_data = json.dumps(extracted_data)
            elif json_key_or_keys and json_key_or_keys in json_response:
                api_data = json_response[json_key_or_keys]
            else:
                api_data = json.dumps(json_response) # Fallback to full JSON if no specific key or key not found

            status = "API_SUCCESS"
            detail = f"API Data: {api_data}"

        except requests.exceptions.RequestException as e:
            status = "API_REQUEST_FAILED"
            detail = f"Error during API request: {e}"
        except json.JSONDecodeError as e:
            status = "API_JSON_PARSE_FAILED"
            detail = f"Error parsing JSON response: {e}. Raw response: {response.text[:200]}..." # Show snippet
        except Exception as e:
            status = "API_UNEXPECTED_ERROR"
            detail = f"Unexpected Error during API call: {e}"

        print(f"  {status}: {detail}\n")
        results.append(f"  Status: {status}")
        results.append(f"  Detail: {detail}\n")

        # --- Bring down WireGuard Tunnel ---
        print(f"Attempting to bring down WireGuard tunnel for '{config_file}'...")
        down_command = ['sudo', 'wg-quick', 'down', config_path]
        down_process = subprocess.run(down_command, capture_output=True, text=True, check=False)

        if down_process.returncode != 0:
            down_status = "VPN_DOWN_FAILED"
            down_detail = f"Error bringing down VPN: {down_process.stderr.strip()}"
            print(f"  {down_status}: {down_detail}\n")
            results.append(f"  Down Status: {down_status}")
            results.append(f"  Down Detail: {down_detail}\n")
        else:
            print(f"  VPN tunnel for '{config_file}' brought down successfully.\n")
            results.append(f"  Down Status: VPN_DOWN_SUCCESS\n")

    # Write results to the output file
    try:
        with open(RESULTS_FILE, 'w') as f: # 'w' mode will overwrite the file
            for line in results:
                f.write(line + "\n")
        print(f"All tests completed. Results saved to '{RESULTS_FILE}'.")
    except IOError as e:
        print(f"Error saving results to file: {e}")

if __name__ == "__main__":
    run_connectivity_test()
