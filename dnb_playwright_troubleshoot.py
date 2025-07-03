import os
import time
import subprocess
import random
from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

# --- Configuration ---
DNB_HOME_URL = "https://www.dnb.com/"
TARGET_DNB_URL = "https://www.dnb.com/business-directory/company-information.oil_and_gas_extraction.ca.html?page=3"
RESULTS_FILE = "dnb_playwright_troubleshoot_results.txt"
SCREENSHOT_DIR = "playwright_troubleshoot_screenshots"
HTML_DUMP_DIR = "playwright_troubleshoot_html_dumps"

# Reduced to 3 WireGuard config files for faster runtime
WIREGUARD_CONFIG_FILES_TO_TEST = [
    "ch-zrh-wg-001.conf",  # Switzerland
    "us-phx-wg-101.conf",  # US Phoenix
    "us-sjc-wg-002.conf",  # US San Jose
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

def take_screenshot(page, filename_prefix, config_file_name, file_handle):
    """Takes a screenshot and saves it to the troubleshooting directory."""
    screenshot_name = f"{config_file_name.replace('.conf', '')}_{filename_prefix}_{datetime.now().strftime('%H%M%S')}.png"
    screenshot_path = os.path.join(SCREENSHOT_DIR, screenshot_name)
    try:
        page.screenshot(path=screenshot_path, full_page=True)
        log_message(f"Screenshot saved: {screenshot_path}", file_handle)
    except Exception as e:
        log_message(f"Error taking screenshot {screenshot_name}: {e}", file_handle)

def dump_html_content(page, filename_prefix, config_file_name, file_handle):
    """Dumps the full HTML content of the page to a file."""
    html_dump_name = f"{config_file_name.replace('.conf', '')}_{filename_prefix}_{datetime.now().strftime('%H%M%S')}.html"
    html_dump_path = os.path.join(HTML_DUMP_DIR, html_dump_name)
    try:
        content = page.content()
        with open(html_dump_path, 'w', encoding='utf-8') as f:
            f.write(content)
        log_message(f"HTML content dumped: {html_dump_path}", file_handle)
    except Exception as e:
        log_message(f"Error dumping HTML content {html_dump_name}: {e}", file_handle)

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
    time.sleep(5)
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

def simulate_human_mouse_movement(page, steps=7, delay_ms_range=(50, 150)):
    """Simulates human-like mouse movements with variable delays."""
    log_message(f"Simulating human-like mouse movements ({steps} steps)...")
    try:
        current_x = random.randint(100, 500)
        current_y = random.randint(100, 500)
        page.mouse.move(current_x, current_y)
        for _ in range(steps):
            target_x = random.randint(50, 1000)
            target_y = random.randint(50, 800)
            page.mouse.move(target_x, target_y, steps=random.randint(5, 20))
            time.sleep(random.uniform(*delay_ms_range) / 1000)
        if random.random() < 0.5:  # 50% chance of a click
            click_x = random.randint(50, 1000)
            click_y = random.randint(50, 800)
            page.mouse.click(click_x, click_y)
            log_message("Mouse click simulated.")
        log_message("Mouse movements completed.")
    except Exception as e:
        log_message(f"Error simulating mouse movement: {e}")

def simulate_human_scroll(page, scroll_attempts=4, scroll_amount_range=(300, 700), delay_range=(0.5, 2.5)):
    """Simulates human-like scrolling with variable amounts and delays."""
    log_message(f"Simulating human-like scrolling ({scroll_attempts} attempts)...")
    try:
        for _ in range(scroll_attempts):
            scroll_amount = random.randint(*scroll_amount_range)
            page.evaluate(f"window.scrollBy(0, {scroll_amount});")
            time.sleep(random.uniform(*delay_range))
        log_message("Scrolling simulated.")
    except Exception as e:
        log_message(f"Error simulating scroll: {e}")

def simulate_background_activity(page):
    """Simulates background activity like opening a new tab and closing it."""
    log_message("Simulating background activity (new tab)...")
    try:
        new_page = page.context.new_page()
        new_page.goto("https://www.example.com", timeout=30000)
        time.sleep(random.uniform(1, 3))
        new_page.close()
        log_message("Background activity simulated.")
    except Exception as e:
        log_message(f"Error simulating background activity: {e}")

def troubleshoot_dnb_playwright():
    """Attempts to load D&B page using Playwright through VPN and logs diagnostics."""
    with open(RESULTS_FILE, 'w') as f_results:
        log_message("--- Starting Playwright DNB Scraper Troubleshooting (Enhanced Stealth - Firefox) ---", f_results)
        log_message(f"DNB Home URL: {DNB_HOME_URL}", f_results)
        log_message(f"Target DNB URL: {TARGET_DNB_URL}", f_results)
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
                    # Use persistent context to maintain cookies/session
                    context_dir = f"playwright_context_{config_file.replace('.conf', '')}"
                    browser = p.firefox.launch_persistent_context(
                        user_data_dir=context_dir,
                        headless=True,
                        user_agent=random.choice([
                            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0",
                            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/115.0",
                            "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0",
                        ]),
                        viewport={"width": random.randint(1300, 1920), "height": random.randint(768, 1080)},
                        bypass_csp=True,
                        java_script_enabled=True,
                        accept_downloads=False,
                        locale=random.choice(["en-US,en;q=0.9", "en-GB,en;q=0.9", "fr-FR,fr;q=0.9"]),
                    )
                    context = browser
                    context.set_default_timeout(60000)

                    # Embed stealth script directly
                    context.add_init_script("""
                        Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                        Object.defineProperty(window, 'chrome', { get: () => undefined });
                        Object.defineProperty(navigator, 'plugins', {
                            get: () => [
                                { name: 'PDF Viewer', filename: 'internal-pdf-viewer', description: 'Portable Document Format', length: 1 },
                                { name: 'Widevine Content Decryption Module', filename: 'widevinecdm.dll', description: 'Enables secure playback', length: 1 },
                            ],
                        });
                        Object.defineProperty(navigator, 'mimeTypes', {
                            get: () => [
                                { type: 'application/pdf', suffixes: 'pdf', description: 'Portable Document Format', enabledPlugin: navigator.plugins[0] },
                            ],
                        });
                        Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
                        Object.defineProperty(navigator, 'hardwareConcurrency', { get: () => [4, 8, 12][Math.floor(Math.random() * 3)] });
                        Object.defineProperty(navigator, 'deviceMemory', { get: () => [4, 8, 16][Math.floor(Math.random() * 3)] });
                        Object.defineProperty(window, 'outerWidth', { get: () => window.innerWidth });
                        Object.defineProperty(window, 'outerHeight', { get: () => window.innerHeight });
                        console.debug = () => {};

                        // Enhanced WebGL spoofing
                        const getParameter = WebGLRenderingContext.prototype.getParameter;
                        WebGLRenderingContext.prototype.getParameter = function(parameter) {
                            if (parameter === 37445) return 'Mozilla';
                            if (parameter === 37446) {
                                const renderers = ['ANGLE (NVIDIA GeForce RTX 3060)', 'ANGLE (Intel Iris Xe)', 'ANGLE (AMD Radeon)'];
                                return renderers[Math.floor(Math.random() * renderers.length)];
                            }
                            return getParameter.apply(this, arguments);
                        };

                        // Spoof canvas fingerprint
                        const getContext = HTMLCanvasElement.prototype.getContext;
                        HTMLCanvasElement.prototype.getContext = function(type) {
                            if (type === '2d') {
                                const ctx = getContext.apply(this, arguments);
                                const originalGetImageData = ctx.getImageData;
                                ctx.getImageData = function(x, y, w, h) {
                                    const data = originalGetImageData.apply(this, arguments);
                                    const pixels = data.data;
                                    for (let i = 0; i < pixels.length; i += 4) {
                                        pixels[i] += Math.floor(Math.random() * 2); // Slight noise
                                    }
                                    return data;
                                };
                                return ctx;
                            }
                            return getContext.apply(this, arguments);
                        };

                        // Spoof navigator.connection
                        Object.defineProperty(navigator, 'connection', {
                            get: () => ({
                                effectiveType: '4g',
                                rtt: Math.floor(Math.random() * 100) + 50,
                                downlink: Math.random() * 5 + 5,
                                saveData: false,
                            }),
                        });

                        // Spoof Permissions.query
                        const originalQuery = Permissions.prototype.query;
                        Permissions.prototype.query = async function(permissionDesc) {
                            if (permissionDesc.name === 'notifications') return { state: 'denied' };
                            if (['geolocation', 'midi', 'camera', 'microphone'].includes(permissionDesc.name)) return { state: 'granted' };
                            return originalQuery.call(this, permissionDesc);
                        };
                    """)

                    context.set_extra_http_headers({
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                        'Accept-Encoding': 'gzip, deflate, br',
                        'Connection': 'keep-alive',
                        'Upgrade-Insecure-Requests': '1',
                    })

                    page = context.new_page()
                    log_message("Playwright browser launched with persistent context and embedded stealth.", f_results)

                    # Longer random delay before DNB Home
                    delay_before_dnb_home = random.uniform(10, 25)
                    log_message(f"Waiting {delay_before_dnb_home:.2f} seconds before navigating to DNB Home URL...", f_results)
                    time.sleep(delay_before_dnb_home)

                    # Simulate human-like behavior
                    simulate_human_mouse_movement(page)
                    simulate_human_scroll(page)
                    simulate_background_activity(page)

                    # Navigate to DNB Home URL
                    log_message(f"\nNavigating to DNB Home URL: {DNB_HOME_URL}...", f_results)
                    try:
                        page.goto(DNB_HOME_URL, timeout=60000)
                        page.wait_for_load_state('networkidle', timeout=30000)
                        log_message(f"Successfully navigated to {DNB_HOME_URL}. Title: {page.title()}", f_results)
                        dump_html_content(page, "dnb_home_page_content", config_file, f_results)

                        # Check for CAPTCHA
                        captcha_detected = page.query_selector('iframe[src*="recaptcha"]') or \
                                          page.query_selector('div#cf-wrapper') or \
                                          page.query_selector('div[data-hcaptcha-widget-id]')
                        if captcha_detected:
                            log_message("CAPTCHA detected on DNB Home page!", f_results)
                            take_screenshot(page, "dnb_home_captcha_detected", config_file, f_results)
                        f_results.write(f"  DNB Home Page Status: SUCCESS{' (CAPTCHA Detected)' if captcha_detected else ''}\n")
                    except PlaywrightTimeoutError:
                        log_message(f"Timeout navigating to {DNB_HOME_URL}.", f_results)
                        take_screenshot(page, "dnb_home_timeout", config_file, f_results)
                        dump_html_content(page, "dnb_home_timeout_content", config_file, f_results)
                        f_results.write("  DNB Home Page Status: FAILED - Navigation Timeout\n")
                    except Exception as e:
                        log_message(f"Error navigating to DNB Home: {e}", f_results)
                        take_screenshot(page, "dnb_home_error", config_file, f_results)
                        dump_html_content(page, "dnb_home_error_content", config_file, f_results)
                        f_results.write(f"  DNB Home Page Status: FAILED - {type(e).__name__}\n")

                    # Delay before DNB Target
                    delay_before_dnb_target = random.uniform(5, 12)
                    log_message(f"Waiting {delay_before_dnb_target:.2f} seconds before navigating to DNB Target URL...", f_results)
                    time.sleep(delay_before_dnb_target)

                    # Simulate more human-like behavior
                    simulate_human_mouse_movement(page)
                    simulate_human_scroll(page)

                    # Navigate to Target DNB URL
                    log_message(f"\nNavigating to DNB Target URL: {TARGET_DNB_URL}...", f_results)
                    try:
                        page.goto(TARGET_DNB_URL, timeout=60000)
                        page.wait_for_load_state('networkidle', timeout=30000)
                        log_message(f"Successfully navigated to {TARGET_DNB_URL}. Title: {page.title()}", f_results)
                        take_screenshot(page, "dnb_target_page_loaded", config_file, f_results)
                        dump_html_content(page, "dnb_target_page_content", config_file, f_results)

                        # Check for CAPTCHA
                        captcha_detected_target = page.query_selector('iframe[src*="recaptcha"]') or \
                                                 page.query_selector('div#cf-wrapper') or \
                                                 page.query_selector('div[data-hcaptcha-widget-id]')
                        if captcha_detected_target:
                            log_message("CAPTCHA detected on DNB Target page!", f_results)
                            take_screenshot(page, "dnb_target_captcha_detected", config_file, f_results)
                        f_results.write(f"  DNB Target Page Status: SUCCESS{' (CAPTCHA Detected)' if captcha_detected_target else ''}\n")
                    except PlaywrightTimeoutError:
                        log_message(f"Timeout navigating to {TARGET_DNB_URL}.", f_results)
                        take_screenshot(page, "dnb_target_timeout", config_file, f_results)
                        dump_html_content(page, "dnb_target_timeout_content", config_file, f_results)
                        f_results.write("  DNB Target Page Status: FAILED - Navigation Timeout\n")
                    except Exception as e:
                        log_message(f"Error navigating to DNB Target: {e}", f_results)
                        take_screenshot(page, "dnb_target_error", config_file, f_results)
                        dump_html_content(page, "dnb_target_error_content", config_file, f_results)
                        f_results.write(f"  DNB Target Page Status: FAILED - {type(e).__name__}\n")

                    context.close()
                    log_message("Playwright browser closed.", f_results)

            except Exception as e:
                log_message(f"Error launching Playwright browser: {e}", f_results)
                f_results.write(f"  Status: FAILED - Playwright Launch Error\n")
            finally:
                bring_down_vpn(config_file, f_results)

        log_message("\n--- Playwright DNB Scraper Troubleshooting Complete ---", f_results)

if __name__ == "__main__":
    troubleshoot_dnb_playwright()
