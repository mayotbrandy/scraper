import os
import time
import subprocess
from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

# --- Configuration ---
TARGET_URL = "https://www.dnb.com/business-directory/company-information.oil_and_gas_extraction.ca.html?page=3"
RESULTS_FILE = "dnb_playwright_troubleshoot_results.txt"
SCREENSHOT_DIR = "playwright_troubleshoot_screenshots"

# List of WireGuard config files to test (using first 5 for focused troubleshooting)
WIREGUARD_CONFIG_FILES_TO_TEST = [
    "ch-zrh-wg-001.conf",
    "ch-zrh-wg-004.conf",
    "ch-zrh-wg-404.conf",
    "us-phx-wg-101.conf",
    "us-phx-wg-103.conf",
]

# Ensure screenshot directory exists
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

# --- Script Logic ---
def log_message(message, file_handle=None):
    """Logs a message to console and optionally to a file."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    full_message = f"[{timestamp}] {message}"
    print(full_message)
    if file_handle:
        file_handle.write(full_message + "\n")

def bring_up_vpn(config_file, file_handle):
    """Brings up a WireGuard VPN tunnel using wg-quick."""
    config_path = os.path.join(os.getcwd(), config_file)
    log_message(f"Attempting to bring up WireGuard tunnel with '{config_file}'...", file_handle)
    up_command = ['sudo', 'wg-quick', 'up', config_path]
    up_process = subprocess.run(up_command, capture_output=True, text=True, check=False)

    if up_process.returncode != 0:
        log_message(f"Error bringing up VPN: {up_process.stderr.strip()}", file_handle)
        return False
    log_message(f"VPN tunnel for '{config_file}' brought up successfully. Waiting 5 seconds for tunnel to stabilize...", file_handle)
    time.sleep(5) # Give VPN time to establish
    return True

def bring_down_vpn(config_file, file_handle):
    """Brings down a WireGuard VPN tunnel using wg-quick."""
    config_path = os.path.join(os.getcwd(), config_file)
    log_message(f"Attempting to bring down WireGuard tunnel for '{config_file}'...", file_handle)
    down_command = ['sudo', 'wg-quick', 'down', config_path]
    down_process = subprocess.run(down_command, capture_output=True, text=True, check=False)

    if down_process.returncode != 0:
        log_message(f"Error bringing down VPN: {down_process.stderr.strip()}", file_handle)
    else:
        log_message(f"VPN tunnel for '{config_file}' brought down successfully.", file_handle)

def troubleshoot_dnb_playwright():
    """Attempts to load D&B page using Playwright through VPN and logs diagnostics."""
    with open(RESULTS_FILE, 'w') as f_results:
        log_message("--- Starting Playwright DNB Scraper Troubleshooting ---", f_results)
        log_message(f"Target URL: {TARGET_URL}", f_results)
        log_message(f"Testing {len(WIREGUARD_CONFIG_FILES_TO_TEST)} WireGuard configurations.", f_results)

        for config_file in WIREGUARD_CONFIG_FILES_TO_TEST:
            log_message(f"\n--- Testing with WireGuard config: {config_file} ---", f_results)
            
            if not bring_up_vpn(config_file, f_results):
                log_message(f"Skipping config {config_file} due to VPN setup failure.", f_results)
                continue

            try:
                with sync_playwright() as p:
                    # Launch Chromium browser
                    browser = p.chromium.launch(headless=True)
                    page = browser.new_page()
                    log_message("Playwright browser launched successfully.", f_results)

                    # --- Get current public IP through VPN ---
                    log_message("Checking public IP through VPN...", f_results)
                    try:
                        page.goto("https://ifconfig.me/ip", timeout=10000) # 10 seconds timeout
                        public_ip = page.inner_text("pre").strip()
                        log_message(f"Public IP through VPN: {public_ip}", f_results)
                    except PlaywrightTimeoutError:
                        log_message("Timeout checking public IP. VPN might not be fully functional or DNS issue.", f_results)
                        public_ip = "IP check timed out"
                    except Exception as e:
                        log_message(f"Error checking public IP: {e}", f_results)
                        public_ip = f"IP check failed: {e}"
                    f_results.write(f"  Public IP through VPN: {public_ip}\n")


                    # --- Navigate to Target URL and take screenshot ---
                    log_message(f"\nNavigating to {TARGET_URL}...", f_results)
                    try:
                        page.goto(TARGET_URL, timeout=60000) # 60 seconds timeout for DNB page
                        log_message(f"Successfully navigated to {TARGET_URL}.", f_results)
                        log_message(f"Page Title: {page.title()}", f_results)
                        
                        screenshot_name = f"{config_file.replace('.conf', '')}_dnb_page_loaded_{datetime.now().strftime('%H%M%S')}.png"
                        screenshot_path = os.path.join(SCREENSHOT_DIR, screenshot_name)
                        page.screenshot(path=screenshot_path, full_page=True)
                        log_message(f"Screenshot saved: {screenshot_path}", f_results)

                        # --- Attempt to Scrape Type 2 Links ---
                        log_message("\nAttempting to scrape for Type 2 links...", f_results)
                        content = page.content()
                        soup = BeautifulSoup(content, 'html.parser')
                        
                        # The selector for company profile links
                        company_links = soup.find_all('a', href=lambda x: x and '/business-directory/company-profiles.' in x)
                        
                        log_message(f"Found {len(company_links)} Type 2 links.", f_results)

                        if not company_links:
                            log_message("No Type 2 links found. Logging full page source for analysis:", f_results)
                            f_results.write("\n--- Full Page Source ---\n")
                            f_results.write(content)
                            f_results.write("\n--- End Full Page Source ---\n")
                        else:
                            log_message("Type 2 links found. Listing first 5 (if any):", f_results)
                            for i, link in enumerate(company_links[:5]):
                                log_message(f"  Link {i+1}: {link.get('href')}", f_results)
                        
                        log_message("\nScraping attempt complete for this config.", f_results)
                        f_results.write("  Status: SUCCESS (Page loaded, scraping attempted)\n")

                    except PlaywrightTimeoutError:
                        log_message(f"Timeout navigating to {TARGET_URL}. This indicates the page did not load within the allowed time.", f_results)
                        # Take screenshot even on timeout to see partial load / error page
                        screenshot_name = f"{config_file.replace('.conf', '')}_dnb_timeout_{datetime.now().strftime('%H%M%S')}.png"
                        screenshot_path = os.path.join(SCREENSHOT_DIR, screenshot_name)
                        page.screenshot(path=screenshot_path, full_page=True)
                        log_message(f"Screenshot saved on timeout: {screenshot_path}", f_results)
                        log_message(f"Page content on timeout (first 500 chars):\n{page.content()[:500]}...", f_results)
                        f_results.write("  Status: FAILED - Navigation Timeout\n")
                    except Exception as e:
                        log_message(f"An unexpected error occurred during page navigation or scraping: {e}", f_results)
                        # Take screenshot on other errors too
                        screenshot_name = f"{config_file.replace('.conf', '')}_dnb_error_{datetime.now().strftime('%H%M%S')}.png"
                        screenshot_path = os.path.join(SCREENSHOT_DIR, screenshot_name)
                        page.screenshot(path=screenshot_path, full_page=True)
                        log_message(f"Screenshot saved on error: {screenshot_path}", f_results)
                        log_message(f"Page content on error (first 500 chars):\n{page.content()[:500]}...", f_results)
                        f_results.write(f"  Status: FAILED - {type(e).__name__}\n")
                        f_results.write(f"  Error Detail: {e}\n")
                    
                    browser.close()
                    log_message("Playwright browser closed.", f_results)

            except Exception as e:
                log_message(f"Error launching Playwright browser: {e}", f_results)
                f_results.write(f"  Status: FAILED - Playwright Launch Error\n")
                f_results.write(f"  Error Detail: {e}\n")
            finally:
                bring_down_vpn(config_file, f_results)

        log_message("\n--- Playwright DNB Scraper Troubleshooting Complete ---", f_results)

if __name__ == "__main__":
    troubleshoot_dnb_playwright()
