import requests
import os
import subprocess
import time
from datetime import datetime

# --- Configuration ---
# List of your Mullvad WireGuard config files.
# These files are expected to be in the same directory as this script.
WIREGUARD_CONFIG_FILES = [
    "ch-zrh-wg-001.conf",
    "ch-zrh-wg-004.conf",
    "ch-zrh-wg-404.conf",
    "us-phx-wg-101.conf",
    "us-phx-wg-103.conf",
    "us-phx-wg-202.conf",
    "us-sjc-wg-002.conf",
    "us-sjc-wg-302.conf",
    "us-sjc-wg-504.conf",
]

# The URL to test connectivity and get the public IP address.
# ifconfig.me/ip is a simple service that returns your public IP.
TEST_URL = "https://ifconfig.me/ip"

# The name of the file where results will be saved.
# This file will be created/overwritten in the repository.
RESULTS_FILE = "vpn_test_results.txt"

# Time to wait after bringing up a VPN tunnel before testing connectivity (in seconds).
# This allows the VPN connection to establish.
VPN_SETUP_WAIT_TIME = 5

# --- Script Logic ---
def run_connectivity_test():
    """
    Runs connectivity tests for each specified WireGuard config using wg-quick.
    This script is designed to run in environments like GitHub Actions where
    wg-quick is available and can be run with sudo permissions.
    """
    print(f"Starting WireGuard connectivity tests. Results will be saved to '{RESULTS_FILE}'.")
    print("-" * 70)

    results = []
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    results.append(f"--- VPN Test Run: {current_time} ---")
    results.append(f"Testing URL: {TEST_URL}\n")

    for config_file in WIREGUARD_CONFIG_FILES:
        config_path = os.path.join(os.getcwd(), config_file)
        print(f"Attempting to bring up WireGuard tunnel with '{config_file}'...")
        results.append(f"Config: {config_file}")

        # --- Bring up WireGuard Tunnel ---
        # Use sudo as wg-quick typically requires root privileges to manage network interfaces.
        up_command = ['sudo', 'wg-quick', 'up', config_path]
        up_process = subprocess.run(up_command, capture_output=True, text=True, check=False)

        if up_process.returncode != 0:
            status = "VPN_UP_FAILED"
            detail = f"Error bringing up VPN: {up_process.stderr.strip()}"
            print(f"  {status}: {detail}")
            results.append(f"  Status: {status}")
            results.append(f"  Detail: {detail}\n")
            # Skip to the next config if VPN failed to come up
            continue

        print(f"  VPN tunnel for '{config_file}' brought up successfully. Waiting {VPN_SETUP_WAIT_TIME} seconds...")
        time.sleep(VPN_SETUP_WAIT_TIME) # Give VPN time to establish

        # --- Test Connectivity ---
        try:
            # Make a simple HTTP GET request to the test URL
            # The IP address returned should be the public IP of the VPN server.
            response = requests.get(TEST_URL, timeout=15) # 15-second timeout for the request
            response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
            public_ip = response.text.strip()
            status = "CONNECTIVITY_SUCCESS"
            detail = f"Public IP: {public_ip}"
        except requests.exceptions.RequestException as e:
            status = "CONNECTIVITY_FAILED"
            detail = f"Error during web request: {e}"
        except Exception as e:
            status = "CONNECTIVITY_FAILED"
            detail = f"Unexpected Error during web request: {e}"

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
