import os
import time
import subprocess
import random
from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
# BeautifulSoup is no longer strictly needed as we removed scraping, but keeping it for now
# from bs4 import BeautifulSoup 

# --- Configuration ---
DNB_HOME_URL = "https://www.dnb.com/" # New: DNB Home Page
TARGET_DNB_URL = "https://www.dnb.com/business-directory/company-information.oil_and_gas_extraction.ca.html?page=3"
PUBLIC_TEST_URL = "https://www.wikipedia.org" # A general public website to test basic connectivity
IP_CHECK_URL = "https://ifconfig.me/ip" # Website to check public IP
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

def take_screenshot(page, filename_prefix, config_file_name, file_handle):
    """Takes a screenshot and saves it to the troubleshooting directory."""
    screenshot_name = f"{config_file_name.replace('.conf', '')}_{filename_prefix}_{datetime.now().strftime('%H%M%S')}.png"
    screenshot_path = os.path.join(SCREENSHOT_DIR, screenshot_name)
    try:
        page.screenshot(path=screenshot_path, full_page=True)
        log_message(f"Screenshot saved: {screenshot_path}", file_handle)
    except Exception as e:
        log_message(f"Error taking screenshot {screenshot_name}: {e}", file_handle)

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

def simulate_human_mouse_movement(page, steps=5, delay_ms=50):
    """Simulates a few human-like mouse movements."""
    log_message(f"Simulating human-like mouse movements ({steps} steps)...")
    try:
        current_x = random.randint(100, 500)
        current_y = random.randint(100, 500)
        page.mouse.move(current_x, current_y)
        for _ in range(steps):
            target_x = random.randint(50, 1000)
            target_y = random.randint(50, 800)
            page.mouse.move(target_x, target_y, steps=random.randint(5, 15))
            time.sleep(delay_ms / 1000) # Convert ms to seconds
        # Perform a random click
        click_x = random.randint(50, 1000)
        click_y = random.randint(50, 800)
        page.mouse.click(click_x, click_y)
        log_message("Mouse movements and click simulated.")
    except Exception as e:
        log_message(f"Error simulating mouse movement: {e}")


def troubleshoot_dnb_playwright():
    """Attempts to load D&B page using Playwright through VPN and logs diagnostics."""
    with open(RESULTS_FILE, 'w') as f_results:
        log_message("--- Starting Playwright DNB Scraper Troubleshooting (DNB Home Page Focus - Firefox) ---", f_results)
        log_message(f"DNB Home URL: {DNB_HOME_URL}", f_results)
        log_message(f"Target DNB URL: {TARGET_DNB_URL}", f_results)
        log_message(f"Public Test URL: {PUBLIC_TEST_URL}", f_results)
        log_message(f"IP Check URL: {IP_CHECK_URL}", f_results)
        log_message(f"Testing {len(WIREGUARD_CONFIG_FILES_TO_TEST)} WireGuard configurations.", f_results)

        for config_file in WIREGUARD_CONFIG_FILES_TO_TEST:
            log_message(f"\n--- Testing with WireGuard config: {config_file} ---", f_results)
            f_results.write(f"\n--- WireGuard Config: {config_file} ---\n")
            
            if not bring_up_vpn(config_file, f_results):
                log_message(f"Skipping config {config_file} due to VPN setup failure.", f_results)
                f_results.write(f"  VPN Setup Failed. Skipping this config.\n")
                continue

            try:
                with sync_playwright() as p:
                    # --- Launch Firefox browser ---
                    browser = p.firefox.launch(
                        headless=True,
                    )
                    # Set a realistic user agent, viewport, and other context options
                    context = browser.new_context(
                        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0", # Firefox User-Agent
                        viewport={"width": 1920, "height": 1080},
                        bypass_csp=True, # Bypass Content Security Policy if any
                        java_script_enabled=True, # Ensure JavaScript is enabled
                        accept_downloads=False, # Prevent accidental downloads
                        locale="en-US,en;q=0.9", # Set Accept-Language header
                        extra_http_headers={ # Add more common headers
                            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                            'Accept-Encoding': 'gzip, deflate, br',
                            'Connection': 'keep-alive'
                        }
                    )
                    page = context.new_page()
                    page.set_default_timeout(60000) # Set default timeout for page operations to 60 seconds

                    # Inject JavaScript to hide common automation flags and spoof fingerprints
                    page.add_init_script("""
                        // Spoof navigator.webdriver
                        Object.defineProperty(navigator, 'webdriver', {
                            get: () => undefined
                        });

                        // Spoof navigator.plugins (more generic for Firefox)
                        Object.defineProperty(navigator, 'plugins', {
                            get: () => [
                                { name: 'Shockwave Flash', filename: 'libflashplayer.so', description: 'Shockwave Flash 32.0 r0' }
                            ]
                        });

                        // Spoof navigator.languages
                        Object.defineProperty(navigator, 'languages', {
                            get: () => ['en-US', 'en']
                        });

                        // Spoof navigator.mimeTypes (more generic for Firefox)
                        Object.defineProperty(navigator, 'mimeTypes', {
                            get: () => [
                                { type: 'application/x-shockwave-flash', suffixes: 'swf', description: 'Shockwave Flash' }
                            ]
                        });

                        // Spoof navigator.hardwareConcurrency and deviceMemory
                        Object.defineProperty(navigator, 'hardwareConcurrency', { get: () => 8 }); // Common CPU cores
                        Object.defineProperty(navigator, 'deviceMemory', { get: () => 8 }); // Common RAM in GB

                        // Spoof window.outerWidth/Height to match innerWidth/Height (common headless detection)
                        Object.defineProperty(window, 'outerWidth', { get: () => window.innerWidth });
                        Object.defineProperty(window, 'outerHeight', { get: () => window.innerHeight });

                        // Override console.debug to prevent detection from logging
                        console.debug = () => {};

                        // Attempt to spoof WebGL for Firefox (less common detection than Chrome, but good to have)
                        const getParameter = WebGLRenderingContext.prototype.getParameter;
                        WebGLRenderingContext.prototype.getParameter = function(parameter) {
                            // UNMASKED_VENDOR_WEBGL
                            if (parameter === 37445) {
                                return 'Mozilla';
                            }
                            // UNMASKED_RENDERER_WEBGL
                            if (parameter === 37446) {
                                return 'Mozilla Firefox';
                            }
                            return getParameter.apply(this, arguments);
                        };
                    """)
                    log_message("Playwright browser launched and configured for enhanced stealth (Firefox).", f_results)

                    # --- Get current public IP through VPN and take screenshot ---
                    log_message(f"Checking public IP through VPN at {IP_CHECK_URL}...", f_results)
                    try:
                        page.goto(IP_CHECK_URL, timeout=15000) # 15 seconds timeout
                        public_ip = page.inner_text("pre").strip()
                        log_message(f"Public IP through VPN: {public_ip}", f_results)
                        take_screenshot(page, "ip_check", config_file, f_results) # Take screenshot of IP page
                    except PlaywrightTimeoutError:
                        log_message("Timeout checking public IP. VPN might not be fully functional or DNS issue.", f_results)
                        public_ip = "IP check timed out"
                        take_screenshot(page, "ip_check_timeout", config_file, f_results) # Screenshot on timeout
                    except Exception as e:
                        log_message(f"Error checking public IP: {e}", f_results)
                        public_ip = f"IP check failed: {e}"
                        take_screenshot(page, "ip_check_error", config_file, f_results) # Screenshot on error
                    f_results.write(f"  Public IP through VPN: {public_ip}\n")

                    # --- Test general public website connectivity ---
                    log_message(f"\nTesting general public website: {PUBLIC_TEST_URL}...", f_results)
                    try:
                        page.goto(PUBLIC_TEST_URL, timeout=30000) # 30 seconds timeout
                        log_message(f"Successfully navigated to {PUBLIC_TEST_URL}. Title: {page.title()}", f_results)
                        take_screenshot(page, "public_site", config_file, f_results) # Take screenshot of public site
                        f_results.write(f"  Public Site Test: SUCCESS - Title: {page.title()}\n")
                    except PlaywrightTimeoutError:
                        log_message(f"Timeout navigating to {PUBLIC_TEST_URL}.", f_results)
                        f_results.write(f"  Public Site Test: FAILED - Timeout\n")
                        take_screenshot(page, "public_site_timeout", config_file, f_results)
                    except Exception as e:
                        log_message(f"Error navigating to {PUBLIC_TEST_URL}: {e}", f_results)
                        f_results.write(f"  Public Site Test: FAILED - Error: {e}\n")
                        take_screenshot(page, "public_site_error", config_file, f_results)

                    # --- Add a larger random delay before navigating to DNB Home ---
                    delay_before_dnb_home = random.uniform(5, 15) # Random delay between 5 and 15 seconds
                    log_message(f"Waiting {delay_before_dnb_home:.2f} seconds before navigating to DNB Home URL...", f_results)
                    time.sleep(delay_before_dnb_home)

                    # --- Simulate human-like mouse movement before DNB Home navigation ---
                    simulate_human_mouse_movement(page)

                    # --- Navigate to DNB Home URL and take screenshot ---
                    log_message(f"\nNavigating to DNB Home URL: {DNB_HOME_URL}...", f_results)
                    try:
                        page.goto(DNB_HOME_URL, timeout=60000) # 60 seconds timeout for DNB page
                        
                        log_message("Waiting for DNB Home page to fully load (network idle)...", f_results)
                        try:
                            page.wait_for_load_state('networkidle', timeout=30000) # Wait for network to be idle
                            log_message("DNB Home page load state is network idle.", f_results)
                        except PlaywrightTimeoutError:
                            log_message("Timeout waiting for DNB Home network idle state. Page might not have fully loaded, but we will proceed.", f_results)
                        except Exception as e:
                            log_message(f"Error waiting for DNB Home page load state: {e}", f_results)

                        log_message(f"Successfully navigated to {DNB_HOME_URL}.", f_results)
                        log_message(f"DNB Home Page Title: {page.title()}", f_results)
                        
                        take_screenshot(page, "dnb_home_page_loaded", config_file, f_results) # Take screenshot of DNB Home page

                        # Check for CAPTCHA/Challenge elements on DNB Home
                        captcha_detected = False
                        if page.query_selector('iframe[src*="recaptcha"]') or \
                           page.query_selector('div#cf-wrapper') or \
                           page.query_selector('div[data-hcaptcha-widget-id]'):
                            log_message("Potential CAPTCHA or challenge detected on DNB Home page!", f_results)
                            captcha_detected = True
                            take_screenshot(page, "dnb_home_captcha_detected", config_file, f_results)

                        f_results.write(f"  DNB Home Page Status: SUCCESS{' (CAPTCHA Detected)' if captcha_detected else ''}\n")
                        f_results.write(f"  DNB Home Page Content (first 500 chars):\n{page.content()[:500]}...\n")

                    except PlaywrightTimeoutError:
                        log_message(f"Timeout navigating to {DNB_HOME_URL}. This indicates the page did not load within the allowed time.", f_results)
                        take_screenshot(page, "dnb_home_timeout", config_file, f_results)
                        log_message(f"DNB Home Page content on timeout (first 500 chars):\n{page.content()[:500]}...", f_results)
                        f_results.write("  DNB Home Page Status: FAILED - Navigation Timeout\n")
                    except Exception as e:
                        log_message(f"An unexpected error occurred during DNB Home page navigation: {e}", f_results)
                        take_screenshot(page, "dnb_home_error", config_file, f_results)
                        log_message(f"DNB Home Page content on error (first 500 chars):\n{page.content()[:500]}...", f_results)
                        f_results.write(f"  DNB Home Page Status: FAILED - {type(e).__name__}\n")
                        f_results.write(f"  Error Detail: {e}\n")
                    
                    # --- Add a small random delay before navigating to DNB Target URL ---
                    delay_before_dnb_target = random.uniform(2, 5)
                    log_message(f"Waiting {delay_before_dnb_target:.2f} seconds before navigating to DNB Target URL...", f_results)
                    time.sleep(delay_before_dnb_target)

                    # --- Navigate to Target DNB URL and take screenshot (still useful for full context) ---
                    log_message(f"\nNavigating to DNB Target URL: {TARGET_DNB_URL}...", f_results)
                    try:
                        page.goto(TARGET_DNB_URL, timeout=60000) # 60 seconds timeout for DNB page
                        
                        log_message("Waiting for DNB Target page to fully load (network idle)...", f_results)
                        try:
                            page.wait_for_load_state('networkidle', timeout=30000) # Wait for network to be idle
                            log_message("DNB Target page load state is network idle.", f_results)
                        except PlaywrightTimeoutError:
                            log_message("Timeout waiting for DNB Target network idle state. Page might not have fully loaded, but we will proceed.", f_results)
                        except Exception as e:
                            log_message(f"Error waiting for DNB Target page load state: {e}", f_results)

                        log_message(f"Successfully navigated to {TARGET_DNB_URL}.", f_results)
                        log_message(f"DNB Target Page Title: {page.title()}", f_results)
                        
                        take_screenshot(page, "dnb_target_page_loaded", config_file, f_results) # Take screenshot of DNB Target page

                        # Check for CAPTCHA/Challenge elements on DNB Target
                        captcha_detected_target = False
                        if page.query_selector('iframe[src*="recaptcha"]') or \
                           page.query_selector('div#cf-wrapper') or \
                           page.query_selector('div[data-hcaptcha-widget-id]'):
                            log_message("Potential CAPTCHA or challenge detected on DNB Target page!", f_results)
                            captcha_detected_target = True
                            take_screenshot(page, "dnb_target_captcha_detected", config_file, f_results)
                        
                        f_results.write(f"  DNB Target Page Status: SUCCESS{' (CAPTCHA Detected)' if captcha_detected_target else ''}\n")
                        f_results.write(f"  DNB Target Page Content (first 500 chars):\n{page.content()[:500]}...\n")


                    except PlaywrightTimeoutError:
                        log_message(f"Timeout navigating to {TARGET_DNB_URL}. This indicates the page did not load within the allowed time.", f_results)
                        take_screenshot(page, "dnb_target_timeout", config_file, f_results)
                        log_message(f"DNB Target Page content on timeout (first 500 chars):\n{page.content()[:500]}...", f_results)
                        f_results.write("  DNB Target Page Status: FAILED - Navigation Timeout\n")
                    except Exception as e:
                        log_message(f"An unexpected error occurred during DNB Target page navigation: {e}", f_results)
                        take_screenshot(page, "dnb_target_error", config_file, f_results)
                        log_message(f"DNB Target Page content on error (first 500 chars):\n{page.content()[:500]}...", f_results)
                        f_results.write(f"  DNB Target Page Status: FAILED - {type(e).__name__}\n")
                        f_results.write(f"  Error Detail: {e}\n")
                    
                    context.close() # Close the context
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
