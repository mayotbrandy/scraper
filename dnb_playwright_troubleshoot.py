import os
import time
import random
from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

# --- Configuration ---
DNB_HOME_URL = "https://www.dnb.com/"
TARGET_DNB_URL = "https://www.dnb.com/business-directory/company-information.oil_and_gas_extraction.ca.html?page=3"
RESULTS_FILE = "dnb_playwright_troubleshoot_results.txt"
SCREENSHOT_DIR = "playwright_troubleshoot_screenshots"
HTML_DUMP_DIR = "playwright_troubleshoot_html_dumps"

# List of 5 SOCKS5 proxies to test, chosen from scraper.py
SOCKS5_PROXIES_TO_TEST = [
    "us-qas-wg-socks5-001.relays.mullvad.net:1080",
    "nl-ams-wg-socks5-001.relays.mullvad.net:1080",
    "de-ber-wg-socks5-001.relays.mullvad.net:1080",
    "us-den-wg-socks5-101.relays.mullvad.net:1080",
    "us-lax-wg-socks5-101.relays.mullvad.net:1080"
]

# Ensure directories exist
os.makedirs(SCREENSHOT_DIR, exist_ok=True)
os.makedirs(HTML_DUMP_DIR, exist_ok=True)

# --- Script Logic ---
def log_message(message, file_handle=None):
    """Logs a message to console and optionally to a file."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    full_message = f"[{timestamp}] {message}"
    print(full_message)
    if file_handle:
        file_handle.write(full_message + "\n")

def take_screenshot(page, filename_prefix, proxy_name, file_handle):
    """Takes a screenshot and saves it to the troubleshooting directory."""
    # Sanitize proxy_name for filename
    sanitized_proxy_name = proxy_name.replace(':', '_').replace('.', '_').replace('-', '_')
    screenshot_name = f"{sanitized_proxy_name}_{filename_prefix}_{datetime.now().strftime('%H%M%S')}.png"
    screenshot_path = os.path.join(SCREENSHOT_DIR, screenshot_name)
    try:
        page.screenshot(path=screenshot_path, full_page=True)
        log_message(f"Screenshot saved: {screenshot_path}", file_handle)
    except Exception as e:
        log_message(f"Error taking screenshot {screenshot_name}: {e}", file_handle)

def dump_html_content(page, filename_prefix, proxy_name, file_handle):
    """Dumps the full HTML content of the page to a file."""
    # Sanitize proxy_name for filename
    sanitized_proxy_name = proxy_name.replace(':', '_').replace('.', '_').replace('-', '_')
    html_dump_name = f"{sanitized_proxy_name}_{filename_prefix}_{datetime.now().strftime('%H%M%S')}.html"
    html_dump_path = os.path.join(HTML_DUMP_DIR, html_dump_name)
    try:
        content = page.content()
        with open(html_dump_path, 'w', encoding='utf-8') as f:
            f.write(content)
        log_message(f"HTML content dumped: {html_dump_path}", file_handle)
    except Exception as e:
        log_message(f"Error dumping HTML content {html_dump_name}: {e}", file_handle)

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

def simulate_human_scroll(page, scroll_attempts=3, scroll_amount=500, delay_between_scrolls_s=(0.5, 2.0)):
    """Simulates human-like scrolling."""
    log_message(f"Simulating human-like scrolling ({scroll_attempts} attempts)...")
    try:
        for _ in range(scroll_attempts):
            page.evaluate(f"window.scrollBy(0, {scroll_amount});")
            time.sleep(random.uniform(*delay_between_scrolls_s))
        log_message("Scrolling simulated.")
    except Exception as e:
        log_message(f"Error simulating scroll: {e}")

def troubleshoot_dnb_playwright():
    """Attempts to load D&B page using Playwright through SOCKS5 proxies and logs diagnostics."""
    with open(RESULTS_FILE, 'w') as f_results:
        log_message("--- Starting Playwright DNB Scraper Troubleshooting (SOCKS5 Proxies - Firefox) ---", f_results)
        log_message(f"DNB Home URL: {DNB_HOME_URL}", f_results)
        log_message(f"Target DNB URL: {TARGET_DNB_URL}", f_results)
        log_message(f"Testing {len(SOCKS5_PROXIES_TO_TEST)} SOCKS5 proxies.", f_results)

        for proxy_address in SOCKS5_PROXIES_TO_TEST:
            log_message(f"\n--- Testing with SOCKS5 Proxy: {proxy_address} ---", f_results)
            f_results.write(f"\n--- SOCKS5 Proxy: {proxy_address} ---\n")
            
            proxy_config = {"server": f"socks5://{proxy_address}"}

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
                        },
                        proxy=proxy_config # Use the SOCKS5 proxy
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

                    # --- Add a longer, more variable random delay before navigating to DNB Home ---
                    delay_before_dnb_home = random.uniform(5, 20) # Longer random delay
                    log_message(f"Waiting {delay_before_dnb_home:.2f} seconds before navigating to DNB Home URL...", f_results)
                    time.sleep(delay_before_dnb_home)

                    # --- Simulate human-like mouse movement and scroll before DNB Home navigation ---
                    simulate_human_mouse_movement(page)
                    simulate_human_scroll(page)

                    # --- Navigate to DNB Home URL and dump HTML content ---
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
                        
                        # No screenshot for home page, but dump HTML content as proof
                        dump_html_content(page, "dnb_home_page_content", proxy_address, f_results)

                        # Check for CAPTCHA/Challenge elements on DNB Home
                        captcha_detected = False
                        if page.query_selector('iframe[src*="recaptcha"]') or \
                           page.query_selector('div#cf-wrapper') or \
                           page.query_selector('div[data-hcaptcha-widget-id]'):
                            log_message("Potential CAPTCHA or challenge detected on DNB Home page!", f_results)
                            captcha_detected = True
                            take_screenshot(page, "dnb_home_captcha_detected", proxy_address, f_results) # Take screenshot if CAPTCHA

                        f_results.write(f"  DNB Home Page Status: SUCCESS{' (CAPTCHA Detected)' if captcha_detected else ''}\n")

                    except PlaywrightTimeoutError:
                        log_message(f"Timeout navigating to {DNB_HOME_URL}. This indicates the page did not load within the allowed time.", f_results)
                        take_screenshot(page, "dnb_home_timeout", proxy_address, f_results)
                        dump_html_content(page, "dnb_home_timeout_content", proxy_address, f_results)
                        log_message(f"DNB Home Page content on timeout (first 500 chars):\n{page.content()[:500]}...", f_results)
                        f_results.write("  DNB Home Page Status: FAILED - Navigation Timeout\n")
                    except Exception as e:
                        log_message(f"An unexpected error occurred during DNB Home page navigation: {e}", f_results)
                        take_screenshot(page, "dnb_home_error", proxy_address, f_results)
                        dump_html_content(page, "dnb_home_error_content", proxy_address, f_results)
                        log_message(f"DNB Home Page content on error (first 500 chars):\n{page.content()[:500]}...", f_results)
                        f_results.write(f"  DNB Home Page Status: FAILED - {type(e).__name__}\n")
                        f_results.write(f"  Error Detail: {e}\n")
                    
                    # --- Add a second, more variable random delay before navigating to DNB Target URL ---
                    delay_before_dnb_target = random.uniform(3, 8) # Second random delay
                    log_message(f"Waiting {delay_before_dnb_target:.2f} seconds before navigating to DNB Target URL...", f_results)
                    time.sleep(delay_before_dnb_target)

                    # --- Simulate human-like mouse movement and scroll before DNB Target navigation ---
                    simulate_human_mouse_movement(page)
                    simulate_human_scroll(page)

                    # --- Navigate to Target DNB URL and take screenshot ---
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
                        
                        take_screenshot(page, "dnb_target_page_loaded", proxy_address, f_results) # Take screenshot of DNB Target page
                        dump_html_content(page, "dnb_target_page_content", proxy_address, f_results) # Dump HTML content

                        # Check for CAPTCHA/Challenge elements on DNB Target
                        captcha_detected_target = False
                        if page.query_selector('iframe[src*="recaptcha"]') or \
                           page.query_selector('div#cf-wrapper') or \
                           page.query_selector('div[data-hcaptcha-widget-id]'):
                            log_message("Potential CAPTCHA or challenge detected on DNB Target page!", f_results)
                            captcha_detected_target = True
                            take_screenshot(page, "dnb_target_captcha_detected", proxy_address, f_results)
                        
                        f_results.write(f"  DNB Target Page Status: SUCCESS{' (CAPTCHA Detected)' if captcha_detected_target else ''}\n")


                    except PlaywrightTimeoutError:
                        log_message(f"Timeout navigating to {TARGET_DNB_URL}. This indicates the page did not load within the allowed time.", f_results)
                        take_screenshot(page, "dnb_target_timeout", proxy_address, f_results)
                        dump_html_content(page, "dnb_target_timeout_content", proxy_address, f_results)
                        log_message(f"DNB Target Page content on timeout (first 500 chars):\n{page.content()[:500]}...", f_results)
                        f_results.write("  DNB Target Page Status: FAILED - Navigation Timeout\n")
                    except Exception as e:
                        log_message(f"An unexpected error occurred during DNB Target page navigation: {e}", f_results)
                        take_screenshot(page, "dnb_target_error", proxy_address, f_results)
                        dump_html_content(page, "dnb_target_error_content", proxy_address, f_results)
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

        log_message("\n--- Playwright DNB Scraper Troubleshooting Complete ---", f_results)

if __name__ == "__main__":
    troubleshoot_dnb_playwright()
