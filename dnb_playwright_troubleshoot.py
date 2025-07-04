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
    print(f"[{timestamp}] {message}")
    if file_handle:
        file_handle.write(f"[{timestamp}] {message}\n")

# Screenshots and HTML dumps
def take_screenshot(page, filename_prefix, config_file_name, file_handle):
    screenshot_name = f"{config_file_name.replace('.conf', '')}_{filename_prefix}_{datetime.now().strftime('%H%M%S')}.png"
    screenshot_path = os.path.join(SCREENSHOT_DIR, screenshot_name)
    try:
        page.screenshot(path=screenshot_path, full_page=True)
        log_message(f"Screenshot: {screenshot_path}", file_handle)
    except Exception as e:
        log_message(f"Screenshot error {screenshot_name}: {e}", file_handle)

def dump_html_content(page, filename_prefix, config_file_name, file_handle):
    html_dump_name = f"{config_file_name.replace('.conf', '')}_{filename_prefix}_{datetime.now().strftime('%H%M%S')}.html"
    html_dump_path = os.path.join(HTML_DUMP_DIR, html_dump_name)
    try:
        content = page.content()
        with open(html_dump_path, 'w', encoding='utf-8') as f:
            f.write(content)
        log_message(f"HTML dumped: {html_dump_path}", file_handle)
    except Exception as e:
        log_message(f"HTML dump error {html_dump_name}: {e}", file_handle)

# VPN management
def bring_up_vpn(config_file, file_handle):
    config_path = os.path.join(os.getcwd(), config_file)
    log_message(f"Starting VPN '{config_file}'...", file_handle)
    up_command = ['sudo', 'wg-quick', 'up', config_path]
    try:
        subprocess.run(up_command, capture_output=True, text=True, check=True, timeout=10)
        log_message(f"VPN '{config_file}' up. Waiting 3s...", file_handle)
        time.sleep(3)
        return True
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        log_message(f"VPN error: {e}", file_handle)
        return False

def bring_down_vpn(config_file, file_handle):
    config_path = os.path.join(os.getcwd(), config_file)
    log_message(f"Stopping VPN '{config_file}'...", file_handle)
    down_command = ['sudo', 'wg-quick', 'down', config_path]
    try:
        subprocess.run(down_command, capture_output=True, text=True, check=True, timeout=10)
        log_message(f"VPN '{config_file}' down.", file_handle)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        log_message(f"VPN shutdown error: {e}", file_handle)

# Human-like behavior
def simulate_human_mouse_movement(page, steps=5, delay_ms_range=(30, 100)):
    log_message(f"Simulating mouse ({steps} steps)...")
    try:
        current_x, current_y = random.randint(100, 600), random.randint(100, 600)
        page.mouse.move(current_x, current_y)
        for _ in range(steps):
            target_x, target_y = random.randint(50, 1200), random.randint(50, 900)
            page.mouse.move(target_x, target_y, steps=random.randint(5, 15))
            time.sleep(random.uniform(*delay_ms_range) / 1000)
        if random.random() < 0.5:
            page.mouse.click(random.randint(50, 1200), random.randint(50, 900))
            log_message("Mouse click simulated.")
        log_message("Mouse done.")
    except Exception as e:
        log_message(f"Mouse error: {e}")

def simulate_human_scroll(page, scroll_attempts=3, scroll_amount_range=(200, 600), delay_range=(0.5, 2)):
    log_message(f"Simulating scroll ({scroll_attempts} attempts)...")
    try:
        for _ in range(scroll_attempts):
            scroll_amount = random.randint(*scroll_amount_range) * random.choice([1, -1])
            page.evaluate(f"window.scrollBy(0, {scroll_amount});")
            time.sleep(random.uniform(*delay_range))
        log_message("Scroll done.")
    except Exception as e:
        log_message(f"Scroll error: {e}")

def simulate_background_activity(page):
    log_message("Simulating background activity...")
    try:
        new_page = page.context.new_page()
        new_page.goto("https://www.example.com", timeout=15000)
        time.sleep(random.uniform(1, 3))
        new_page.close()
        log_message("Background activity done.")
    except Exception as e:
        log_message(f"Background error: {e}")

# Main function
def troubleshoot_dnb_playwright():
    with open(RESULTS_FILE, 'w') as f_results:
        log_message("Starting DNB Scraper Troubleshooting...", f_results)
        log_message(f"Home URL: {DNB_HOME_URL}", f_results)
        log_message(f"Target URL: {TARGET_DNB_URL}", f_results)
        log_message(f"Testing {len(WIREGUARD_CONFIG_FILES_TO_TEST)} VPNs.", f_results)

        for config_file in WIREGUARD_CONFIG_FILES_TO_TEST:
            log_message(f"\nTesting VPN: {config_file}", f_results)
            f_results.write(f"\n--- VPN: {config_file} ---\n")
            
            if not bring_up_vpn(config_file, f_results):
                log_message(f"Skipping {config_file}.", f_results)
                f_results.write("  VPN Failed.\n")
                continue

            try:
                with sync_playwright() as p:
                    context_dir = f"playwright_context_{config_file.replace('.conf', '')}"
                    browser = p.firefox.launch_persistent_context(
                        user_data_dir=context_dir,
                        headless=True,
                        user_agent=random.choice([
                            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0",
                            "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_6; rv:128.0) Gecko/20100101 Firefox/128.0",
                            "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0",
                        ]),
                        viewport={"width": random.randint(1280, 1920), "height": random.randint(720, 1080)},
                        bypass_csp=True,
                        java_script_enabled=True,
                        accept_downloads=False,
                        locale=random.choice(["en-US,en;q=0.9", "en-GB,en;q=0.8", "fr-FR,fr;q=0.9"]),
                        screen={"width": random.randint(1280, 1920), "height": random.randint(720, 1080)},
                        has_touch=False,
                        is_mobile=False,
                        device_scale_factor=1.0,
                    )
                    context = browser
                    context.set_default_timeout(30000)

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
                            get: () => [{ type: 'application/pdf', suffixes: 'pdf', description: 'Portable Document Format', enabledPlugin: navigator.plugins[0] }], });
                        Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
                        Object.defineProperty(navigator, 'hardwareConcurrency', { get: () => [4, 8, 12][Math.floor(Math.random() * 3)] });
                        Object.defineProperty(navigator, 'deviceMemory', { get: () => [4, 8, 16][Math.floor(Math.random() * 3)] });
                        Object.defineProperty(window, 'outerWidth', { get: () => window.innerWidth });
                        Object.defineProperty(window, 'outerHeight', { get: () => window.innerHeight });
                        Object.defineProperty(navigator, 'platform', { get: () => ['Win32', 'MacIntel', 'Linux x86_64'][Math.floor(Math.random() * 3)] });
                        console.debug = () => {};

                        const getParameter = WebGLRenderingContext.prototype.getParameter;
                        WebGLRenderingContext.prototype.getParameter = function(parameter) {
                            if (parameter === 37445) return 'Mozilla';
                            if (parameter === 37446) return ['ANGLE (NVIDIA GeForce RTX 3060)', 'ANGLE (Intel Iris Xe)', 'ANGLE (AMD Radeon)'][Math.floor(Math.random() * 3)];
                            return getParameter.apply(this, arguments);
                        };

                        const getContext = HTMLCanvasElement.prototype.getContext;
                        HTMLCanvasElement.prototype.getContext = function(type) {
                            if (type === '2d') {
                                const ctx = getContext.apply(this, arguments);
                                const originalGetImageData = ctx.getImageData;
                                ctx.getImageData = function(x, y, w, h) {
                                    const data = originalGetImageData.apply(this, arguments);
                                    const pixels = data.data;
                                    for (let i = 0; i < pixels.length; i += 4) pixels[i] += Math.floor(Math.random() * 3) - 1;
                                    return data;
                                };
                                return ctx;
                            }
                            return getContext.apply(this, arguments);
                        };

                        Object.defineProperty(navigator, 'connection', {
                            get: () => ({
                                effectiveType: '4g',
                                rtt: Math.floor(Math.random() * 50) + 50,
                                downlink: Math.random() * 4 + 4,
                                saveData: false,
                            }),
                        });

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
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                        'Accept-Encoding': 'gzip, deflate, br',
                        'Connection': 'keep-alive',
                        'Upgrade-Insecure-Requests': '1',
                        'Sec-Fetch-Dest': 'document',
                        'Sec-Fetch-Mode': 'navigate',
                        'Sec-Fetch-Site': 'none',
                        'Sec-Fetch-User': '?1',
                        'Referer': 'https://www.google.com/',
                    })

                    page = context.new_page()
                    log_message("Browser launched.", f_results)

                    # Navigate to DNB Home
                    delay = random.uniform(5, 10)
                    log_message(f"Waiting {delay:.2f}s for home URL...", f_results)
                    time.sleep(delay)
                    simulate_human_mouse_movement(page)
                    simulate_human_scroll(page)

                    log_message(f"Navigating to {DNB_HOME_URL}...", f_results)
                    try:
                        page.goto(DNB_HOME_URL, timeout=30000, wait_until='domcontentloaded')
                        log_message(f"Navigated to {DNB_HOME_URL}. Title: {page.title()}", f_results)
                        dump_html_content(page, "dnb_home_page_content", config_file, f_results)
                        if page.query_selector('iframe[src*="recaptcha"],div#cf-wrapper,div[data-hcaptcha-widget-id],h1:contains("Access Denied")'):
                            log_message("Block detected on home page!", f_results)
                            take_screenshot(page, "dnb_home_block_detected", config_file, f_results)
                        f_results.write(f"  Home Page: SUCCESS{' (Block Detected)' if page.query_selector('iframe[src*="recaptcha"],div#cf-wrapper,div[data-hcaptcha-widget-id],h1:contains(\"Access Denied\")') else ''}\n")
                    except PlaywrightTimeoutError:
                        log_message(f"Timeout on {DNB_HOME_URL}.", f_results)
                        take_screenshot(page, "dnb_home_timeout", config_file, f_results)
                        dump_html_content(page, "dnb_home_timeout_content", config_file, f_results)
                        f_results.write("  Home Page: FAILED - Timeout\n")
                    except Exception as e:
                        log_message(f"Error on {DNB_HOME_URL}: {e}", f_results)
                        take_screenshot(page, "dnb_home_error", config_file, f_results)
                        dump_html_content(page, "dnb_home_error_content", config_file, f_results)
                        f_results.write(f"  Home Page: FAILED - {type(e).__name__}\n")

                    # Navigate to Target URL
                    delay = random.uniform(3, 7)
                    log_message(f"Waiting {delay:.2f}s for target URL...", f_results)
                    time.sleep(delay)
                    simulate_human_mouse_movement(page)
                    simulate_human_scroll(page)

                    log_message(f"Navigating to {TARGET_DNB_URL}...", f_results)
                    try:
                        page.goto(TARGET_DNB_URL, timeout=30000, wait_until='domcontentloaded')
                        log_message(f"Navigated to {TARGET_DNB_URL}. Title: {page.title()}", f_results)
                        take_screenshot(page, "dnb_target_page_loaded", config_file, f_results)
                        dump_html_content(page, "dnb_target_page_content", config_file, f_results)
                        if page.query_selector('iframe[src*="recaptcha"],div#cf-wrapper,div[data-hcaptcha-widget-id],h1:contains("Access Denied")'):
                            log_message("Block detected on target page!", f_results)
                            take_screenshot(page, "dnb_target_block_detected", config_file, f_results)
                        f_results.write(f"  Target Page: SUCCESS{' (Block Detected)' if page.query_selector('iframe[src*="recaptcha"],div#cf-wrapper,div[data-hcaptcha-widget-id],h1:contains(\"Access Denied\")') else ''}\n")
                    except PlaywrightTimeoutError:
                        log_message(f"Timeout on {TARGET_DNB_URL}.", f_results)
                        take_screenshot(page, "dnb_target_timeout", config_file, f_results)
                        dump_html_content(page, "dnb_target_timeout_content", config_file, f_results)
                        f_results.write("  Target Page: FAILED - Timeout\n")
                    except Exception as e:
                        log_message(f"Error on {TARGET_DNB_URL}: {e}", f_results)
                        take_screenshot(page, "dnb_target_error", config_file, f_results)
                        dump_html_content(page, "dnb_target_error_content", config_file, f_results)
                        f_results.write(f"  Target Page: FAILED - {type(e).__name__}\n")

                    context.close()
                    log_message("Browser closed.", f_results)

            except Exception as e:
                log_message(f"Browser error: {e}", f_results)
                f_results.write(f"  Status: FAILED - Browser Error\n")
            finally:
                bring_down_vpn(config_file, f_results)

        log_message("Troubleshooting Done.", f_results)

if __name__ == "__main__":
    troubleshoot_dnb_playwright()
