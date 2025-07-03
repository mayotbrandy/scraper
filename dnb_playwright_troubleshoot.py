import os
import time
import subprocess
import random
from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

# Configuration
DNB_HOME_URL = "https://www.dnb.com/"
TARGET_DNB_URL = "https://www.dnb.com/business-directory/company-information.oil_and_gas_extraction.ca.html?page=3"
RESULTS_FILE = "dnb_playwright_troubleshoot_results.txt"
SCREENSHOT_DIR = "playwright_troubleshoot_screenshots"
HTML_DUMP_DIR = "playwright_troubleshoot_html_dumps"
WIREGUARD_CONFIG_FILES_TO_TEST = ["ch-zrh-wg-001.conf", "us-phx-wg-101.conf", "us-sjc-wg-002.conf"]

# Ensure directories
os.makedirs(SCREENSHOT_DIR, exist_ok=True)
os.makedirs(HTML_DUMP_DIR, exist_ok=True)

# Logging
def log_message(message, file_handle=None):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    full_message = f"[{timestamp}] {message}"
    print(full_message)
    if file_handle:
        file_handle.write(full_message + "\n")

# Screenshots and HTML dumps
def take_screenshot(page, filename_prefix, config_file_name, file_handle):
    screenshot_name = f"{config_file_name.replace('.conf', '')}_{filename_prefix}_{datetime.now().strftime('%H%M%S')}.png"
    screenshot_path = os.path.join(SCREENSHOT_DIR, screenshot_name)
    try:
        page.screenshot(path=screenshot_path, full_page=True)
        log_message(f"Screenshot saved: {screenshot_path}", file_handle)
    except Exception as e:
        log_message(f"Error taking screenshot {screenshot_name}: {e}", file_handle)

def dump_html_content(page, filename_prefix, config_file_name, file_handle):
    html_dump_name = f"{config_file_name.replace('.conf', '')}_{filename_prefix}_{datetime.now().strftime('%H%M%S')}.html"
    html_dump_path = os.path.join(HTML_DUMP_DIR, html_dump_name)
    try:
        content = page.content()
        with open(html_dump_path, 'w', encoding='utf-8') as f:
            f.write(content)
        log_message(f"HTML content dumped: {html_dump_path}", file_handle)
    except Exception as e:
        log_message(f"Error dumping HTML content {html_dump_name}: {e}", file_handle)

# VPN management
def bring_up_vpn(config_file, file_handle):
    config_path = os.path.join(os.getcwd(), config_file)
    log_message(f"Bringing up VPN '{config_file}'...", file_handle)
    up_command = ['sudo', 'wg-quick', 'up', config_path]
    up_process = subprocess.run(up_command, capture_output=True, text=True, check=False)
    if up_process.returncode != 0:
        log_message(f"VPN error: {up_process.stderr.strip()}", file_handle)
        return False
    log_message(f"VPN '{config_file}' up. Waiting 5s...", file_handle)
    time.sleep(5)
    return True

def bring_down_vpn(config_file, file_handle):
    config_path = os.path.join(os.getcwd(), config_file)
    log_message(f"Bringing down VPN '{config_file}'...", file_handle)
    down_command = ['sudo', 'wg-quick', 'down', config_path]
    down_process = subprocess.run(down_command, capture_output=True, text=True, check=False)
    if down_process.returncode != 0:
        log_message(f"VPN shutdown error: {down_process.stderr.strip()}", file_handle)
    else:
        log_message(f"VPN '{config_file}' down.", file_handle)

# Human-like behavior
def simulate_human_mouse_movement(page, steps=10, delay_ms_range=(50, 200)):
    log_message(f"Simulating mouse movements ({steps} steps)...")
    try:
        current_x, current_y = random.randint(100, 600), random.randint(100, 600)
        page.mouse.move(current_x, current_y)
        for _ in range(steps):
            target_x, target_y = random.randint(50, 1200), random.randint(50, 900)
            page.mouse.move(target_x, target_y, steps=random.randint(10, 25))
            time.sleep(random.uniform(*delay_ms_range) / 1000)
        if random.random() < 0.7:
            click_x, click_y = random.randint(50, 1200), random.randint(50, 900)
            page.mouse.click(click_x, click_y)
            log_message("Mouse click simulated.")
        log_message("Mouse movements completed.")
    except Exception as e:
        log_message(f"Mouse movement error: {e}")

def simulate_human_scroll(page, scroll_attempts=5, scroll_amount_range=(200, 800), delay_range=(0.7, 3)):
    log_message(f"Simulating scrolling ({scroll_attempts} attempts)...")
    try:
        for _ in range(scroll_attempts):
            scroll_amount = random.randint(*scroll_amount_range)
            direction = random.choice([1, -1])  # Random up/down scroll
            page.evaluate(f"window.scrollBy(0, {scroll_amount * direction});")
            time.sleep(random.uniform(*delay_range))
        log_message("Scrolling simulated.")
    except Exception as e:
        log_message(f"Scroll error: {e}")

def simulate_background_activity(page):
    log_message("Simulating background activity...")
    try:
        new_page = page.context.new_page()
        new_page.goto(random.choice(["https://www.example.com", "https://www.wikipedia.org"]), timeout=30000)
        time.sleep(random.uniform(2, 5))
        new_page.close()
        log_message("Background activity simulated.")
    except Exception as e:
        log_message(f"Background activity error: {e}")

# Main function
def troubleshoot_dnb_playwright():
    with open(RESULTS_FILE, 'w') as f_results:
        log_message("Starting Playwright DNB Scraper Troubleshooting...", f_results)
        log_message(f"Home URL: {DNB_HOME_URL}", f_results)
        log_message(f"Target URL: {TARGET_DNB_URL}", f_results)
        log_message(f"Testing {len(WIREGUARD_CONFIG_FILES_TO_TEST)} VPNs.", f_results)

        for config_file in WIREGUARD_CONFIG_FILES_TO_TEST:
            log_message(f"\nTesting VPN: {config_file}", f_results)
            f_results.write(f"\n--- VPN: {config_file} ---\n")
            
            if not bring_up_vpn(config_file, f_results):
                log_message(f"Skipping {config_file} due to VPN failure.", f_results)
                f_results.write("  VPN Setup Failed.\n")
                continue

            try:
                with sync_playwright() as p:
                    context_dir = f"playwright_context_{config_file.replace('.conf', '')}"
                    browser = p.firefox.launch_persistent_context(
                        user_data_dir=context_dir,
                        headless=True,
                        user_agent=random.choice([
                            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
                            "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5; rv:125.0) Gecko/20100101 Firefox/125.0",
                            "Mozilla/5.0 (X11; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0",
                        ]),
                        viewport={"width": random.randint(1280, 1920), "height": random.randint(720, 1080)},
                        bypass_csp=True,
                        java_script_enabled=True,
                        accept_downloads=False,
                        locale=random.choice(["en-US,en;q=0.9", "en-GB,en;q=0.8", "fr-FR,fr;q=0.9"]),
                        screen={"width": random.randint(1280, 1920), "height": random.randint(720, 1080)},
                        has_touch=False,
                        is_mobile=False,
                        device_scale_factor=random.uniform(1.0, 1.5),
                    )
                    context = browser
                    context.set_default_timeout(60000)

                    # Enhanced stealth script
                    context.add_init_script("""
                        Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                        Object.defineProperty(window, 'chrome', { get: () => undefined });
                        Object.defineProperty(navigator, 'plugins', {
                            get: () => [
                                { name: 'PDF Viewer', filename: 'internal-pdf-viewer', description: 'Portable Document Format', length: 1 },
                                { name: 'Widevine CDM', filename: 'widevinecdm.dll', description: 'Enables secure playback', length: 1 },
                            ],
                        });
                        Object.defineProperty(navigator, 'mimeTypes', {
                            get: () => [
                                { type: 'application/pdf', suffixes: 'pdf', description: 'Portable Document Format', enabledPlugin: navigator.plugins[0] },
                            ],
                        });
                        Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
                        Object.defineProperty(navigator, 'hardwareConcurrency', { get: () => [4, 8, 12, 16][Math.floor(Math.random() * 4)] });
                        Object.defineProperty(navigator, 'deviceMemory', { get: () => [4, 8, 16, 32][Math.floor(Math.random() * 4)] });
                        Object.defineProperty(window, 'outerWidth', { get: () => window.innerWidth });
                        Object.defineProperty(window, 'outerHeight', { get: () => window.innerHeight });
                        Object.defineProperty(navigator, 'platform', { get: () => ['Win32', 'MacIntel', 'Linux x86_64'][Math.floor(Math.random() * 3)] });
                        console.debug = () => {};

                        // WebGL spoofing
                        const getParameter = WebGLRenderingContext.prototype.getParameter;
                        WebGLRenderingContext.prototype.getParameter = function(parameter) {
                            if (parameter === 37445) return 'Mozilla';
                            if (parameter === 37446) {
                                const renderers = ['ANGLE (NVIDIA GeForce RTX 3060)', 'ANGLE (Intel Iris Xe)', 'ANGLE (AMD Radeon)', 'ANGLE (Intel UHD Graphics)'];
                                return renderers[Math.floor(Math.random() * renderers.length)];
                            }
                            return getParameter.apply(this, arguments);
                        };

                        // Canvas fingerprint spoofing
                        const getContext = HTMLCanvasElement.prototype.getContext;
                        HTMLCanvasElement.prototype.getContext = function(type) {
                            if (type === '2d') {
                                const ctx = getContext.apply(this, arguments);
                                const originalGetImageData = ctx.getImageData;
                                ctx.getImageData = function(x, y, w, h) {
                                    const data = originalGetImageData.apply(this, arguments);
                                    const pixels = data.data;
                                    for (let i = 0; i < pixels.length; i += 4) {
                                        pixels[i] += Math.floor(Math.random() * 3) - 1; // Subtle noise
                                    }
                                    return data;
                                };
                                return ctx;
                            savour                            } catch (e) {
                                log_message(f"Canvas spoofing error: {e}");
                            }
                            return getContext.apply(this, arguments);
                        };

                        // Navigator connection spoofing
                        Object.defineProperty(navigator, 'connection', {
                            get: () => ({
                                effectiveType: '4g',
                                rtt: Math.floor(Math.random() * 100) + 50,
                                downlink: Math.random() * 5 + 5,
                                saveData: Math.random() < 0.3,
                            }),
                        });

                        // Permissions spoofing
                        const originalQuery = Permissions.prototype.query;
                        Permissions.prototype.query = async function(permissionDesc) {
                            if (permissionDesc.name === 'notifications') return { state: 'denied' };
                            if (['geolocation', 'midi', 'camera', 'microphone'].includes(permissionDesc.name)) return { state: 'granted' };
                            return originalQuery.call(this, permissionDesc);
                        };

                        // Spoof window.screen
                        Object.defineProperty(window, 'screen', {
                            get: () => ({
                                width: window.innerWidth,
                                height: window.innerHeight,
                                availWidth: window.innerWidth,
                                availHeight: window.innerHeight,
                                colorDepth: 24,
                                pixelDepth: 24,
                            }),
                        });
                    """)

                    context.set_extra_http_headers({
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                        'Accept-Encoding': 'gzip, deflate, br',
                        'Connection': 'keep-alive',
                        'Upgrade-Insecure-Requests': '1',
                        'Sec-Fetch-Dest': 'document',
                        'Sec-Fetch-Mode': 'navigate',
                        'Sec-Fetch-Site': 'none',
                        'Sec-Fetch-User': '?1',
                    })

                    page = context.new_page()
                    log_message("Browser launched with enhanced stealth.", f_results)

                    # Navigate to DNB Home
                    delay = random.uniform(15, 30)
                    log_message(f"Waiting {delay:.2f}s before home URL...", f_results)
                    time.sleep(delay)
                    simulate_human_mouse_movement(page)
                    simulate_human_scroll(page)
                    simulate_background_activity(page)

                    log_message(f"\nNavigating to {DNB_HOME_URL}...", f_results)
                    try:
                        page.goto(DNB_HOME_URL, timeout=60000)
                        page.wait_for_load_state('networkidle', timeout=30000)
                        log_message(f"Navigated to {DNB_HOME_URL}. Title: {page.title()}", f_results)
                        dump_html_content(page, "dnb_home_page_content", config_file, f_results)
                        if page.query_selector('iframe[src*="recaptcha"],div#cf-wrapper,div[data-hcaptcha-widget-id]'):
                            log_message("CAPTCHA detected on home page!", f_results)
                            take_screenshot(page, "dnb_home_captcha_detected", config_file, f_results)
                        f_results.write(f"  Home Page Status: SUCCESS{' (CAPTCHA Detected)' if page.query_selector('iframe[src*="recaptcha"],div#cf-wrapper,div[data-hcaptcha-widget-id]') else ''}\n")
                    except PlaywrightTimeoutError:
                        log_message(f"Timeout on {DNB_HOME_URL}.", f_results)
                        take_screenshot(page, "dnb_home_timeout", config_file, f_results)
                        dump_html_content(page, "dnb_home_timeout_content", config_file, f_results)
                        f_results.write("  Home Page Status: FAILED - Timeout\n")
                    except Exception as e:
                        log_message(f"Error on {DNB_HOME_URL}: {e}", f_results)
                        take_screenshot(page, "dnb_home_error", config_file, f_results)
                        dump_html_content(page, "dnb_home_error_content", config_file, f_results)
                        f_results.write(f"  Home Page Status: FAILED - {type(e).__name__}\n")

                    # Navigate to Target URL
                    delay = random.uniform(7, 15)
                    log_message(f"Waiting {delay:.2f}s before target URL...", f_results)
                    time.sleep(delay)
                    simulate_human_mouse_movement(page)
                    simulate_human_scroll(page)

                    log_message(f"\nNavigating to {TARGET_DNB_URL}...", f_results)
                    try:
                        page.goto(TARGET_DNB_URL, timeout=60000)
                        page.wait_for_load_state('networkidle', timeout=30000)
                        log_message(f"Navigated to {TARGET_DNB_URL}. Title: {page.title()}", f_results)
                        take_screenshot(page, "dnb_target_page_loaded", config_file, f_results)
                        dump_html_content(page, "dnb_target_page_content", config_file, f_results)
                        if page.query_selector('iframe[src*="recaptcha"],div#cf-wrapper,div[data-hcaptcha-widget-id]'):
                            log_message("CAPTCHA detected on target page!", f_results)
                            take_screenshot(page, "dnb_target_captcha_detected", config_file, f_results)
                        f_results.write(f"  Target Page Status: SUCCESS{' (CAPTCHA Detected)' if page.query_selector('iframe[src*="recaptcha"],div#cf-wrapper,div[data-hcaptcha-widget-id]') else ''}\n")
                    except PlaywrightTimeoutError:
                        log_message(f"Timeout on {TARGET_DNB_URL}.", f_results)
                        take_screenshot(page, "dnb_target_timeout", config_file, f_results)
                        dump_html_content(page, "dnb_target_timeout_content", config_file, f_results)
                        f_results.write("  Target Page Status: FAILED - Timeout\n")
                    except Exception as e:
                        log_message(f"Error on {TARGET_DNB_URL}: {e}", f_results)
                        take_screenshot(page, "dnb_target_error", config_file, f_results)
                        dump_html_content(page, "dnb_target_error_content", config_file, f_results)
                        f_results.write(f"  Target Page Status: FAILED - {type(e).__name__}\n")

                    context.close()
                    log_message("Browser closed.", f_results)

            except Exception as e:
                log_message(f"Browser launch error: {e}", f_results)
                f_results.write(f"  Status: FAILED - Browser Launch Error\n")
            finally:
                bring_down_vpn(config_file, f_results)

        log_message("\nTroubleshooting Complete", f_results)

if __name__ == "__main__":
    troubleshoot_dnb_playwright()
