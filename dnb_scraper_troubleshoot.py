import os
import time
from datetime import datetime
from seleniumbase import Driver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException, TimeoutException, SessionNotCreatedException
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# --- Configuration ---
TARGET_URL = "https://www.dnb.com/business-directory/company-information.oil_and_gas_extraction.ca.html?page=3"
RESULTS_FILE = "dnb_troubleshoot_results.txt"
SCREENSHOT_DIR = "troubleshoot_screenshots"

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

def take_screenshot(driver, filename_suffix, file_handle):
    """Takes a screenshot and saves it to the troubleshooting directory."""
    if driver:
        screenshot_name = f"dnb_page_{filename_suffix}_{datetime.now().strftime('%H%M%S')}.png"
        screenshot_path = os.path.join(SCREENSHOT_DIR, screenshot_name)
        try:
            driver.save_screenshot(screenshot_path)
            log_message(f"Screenshot saved: {screenshot_path}", file_handle)
        except Exception as e:
            log_message(f"Error taking screenshot {screenshot_name}: {e}", file_handle)

def troubleshoot_dnb_scraper():
    """Attempts to scrape a D&B page and provides detailed troubleshooting."""
    driver = None
    with open(RESULTS_FILE, 'w') as f_results:
        log_message("--- Starting DNB Scraper Troubleshooting ---", f_results)
        log_message(f"Target URL: {TARGET_URL}", f_results)

        # --- Initialize Browser ---
        log_message("\nAttempting to initialize SeleniumBase Driver...", f_results)
        try:
            driver = Driver(browser="chrome", headless=True) # Use "chrome" for Chromium
            driver.set_page_load_timeout(60) # Set page load timeout to 60 seconds
            log_message("Selenium WebDriver initialized successfully in headless mode!", f_results)

            # --- Navigate to Target URL ---
            log_message(f"\nNavigating to {TARGET_URL}...", f_results)
            driver.get(TARGET_URL)
            log_message(f"Successfully navigated to {TARGET_URL}. Current URL: {driver.current_url}", f_results)
            log_message(f"Page Title: {driver.title}", f_results)

            # --- Take Screenshot after load ---
            take_screenshot(driver, "after_load", f_results)

            # --- Check for a known element to confirm content is loading ---
            # This is a generic check for body content, can be made more specific if a common element is known.
            body_text = driver.find_element(By.TAG_NAME, "body").text
            if len(body_text) > 100: # Check if there's substantial text content
                log_message(f"Body contains substantial text content (first 100 chars): {body_text[:100]}...", f_results)
            else:
                log_message(f"Body contains very little text content (length: {len(body_text)}). This might indicate a loading issue.", f_results)

            # --- Attempt to Scrape Type 2 Links ---
            log_message("\nAttempting to scrape for Type 2 links...", f_results)
            content = driver.page_source
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
            
            log_message("\nScraping attempt complete.", f_results)
            f_results.write("Overall Status: SUCCESS (Browser launched, page loaded, scraping attempted)\n")

        except TimeoutException:
            log_message(f"TimeoutException during navigation to {TARGET_URL}.", f_results)
            f_results.write("Overall Status: FAILED - TimeoutException\n")
        except SessionNotCreatedException as e:
            log_message(f"SessionNotCreatedException during WebDriver initialization: {e}", f_results)
            log_message("Possible causes: Browser not installed correctly, incompatible WebDriver, or display issues.", f_results)
            f_results.write("Overall Status: FAILED - SessionNotCreatedException\n")
        except WebDriverException as e:
            log_message(f"WebDriverException during browser operation: {e}", f_results)
            log_message("This is a general WebDriver error. Check the full traceback for more details.", f_results)
            f_results.write("Overall Status: FAILED - WebDriverException\n")
        except Exception as e:
            log_message(f"An unexpected error occurred: {e}", f_results)
            log_message("Please review the full traceback for more information.", f_results)
            f_results.write("Overall Status: FAILED - Unexpected Error\n")
        finally:
            if driver:
                log_message("Quitting Selenium WebDriver...", f_results)
                driver.quit()
                log_message("WebDriver quit successfully.", f_results)
            else:
                log_message("WebDriver was not initialized, no need to quit.", f_results)

        log_message("\n--- DNB Scraper Troubleshooting Complete ---", f_results)

if __name__ == "__main__":
    troubleshoot_dnb_scraper()
