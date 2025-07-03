import os
import subprocess
import time
from datetime import datetime
from seleniumbase import Driver
from selenium.common.exceptions import WebDriverException, SessionNotCreatedException

# --- Configuration ---
RESULTS_FILE = "browser_troubleshoot_results.txt"

# --- Script Logic ---
def log_message(message, file_handle=None):
    """Logs a message to console and optionally to a file."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    full_message = f"[{timestamp}] {message}"
    print(full_message)
    if file_handle:
        file_handle.write(full_message + "\n")

def run_command(command, description, file_handle):
    """Runs a shell command and logs its output."""
    log_message(f"--- Running command: {description} ({' '.join(command)}) ---", file_handle)
    try:
        process = subprocess.run(command, capture_output=True, text=True, check=False)
        log_message(f"Command STDOUT:\n{process.stdout.strip()}", file_handle)
        if process.stderr:
            log_message(f"Command STDERR:\n{process.stderr.strip()}", file_handle)
        log_message(f"Command exited with code: {process.returncode}", file_handle)
        return process.returncode == 0
    except FileNotFoundError:
        log_message(f"Error: Command '{command[0]}' not found.", file_handle)
        return False
    except Exception as e:
        log_message(f"Error running command: {e}", file_handle)
        return False

def troubleshoot_browser_launch():
    """Attempts to launch SeleniumBase browser and troubleshoots if it fails."""
    with open(RESULTS_FILE, 'w') as f_results:
        log_message("--- Starting SeleniumBase Browser Troubleshooting ---", f_results)

        # --- Diagnostic Checks ---
        log_message("Performing pre-launch diagnostic checks...", f_results)
        
        # Check Chromium version
        run_command(["chromium-browser", "--version"], "Chromium Browser Version", f_results)
        
        # Check if Xvfb (virtual display) is running (SeleniumBase often uses it automatically)
        # This command might vary, but this is a common way to check for Xvfb processes.
        run_command(["pgrep", "-l", "Xvfb"], "Check for Xvfb process", f_results)

        # Check display environment variable
        log_message(f"DISPLAY environment variable: {os.environ.get('DISPLAY', 'Not set')}", f_results)

        # --- Attempt Browser Launch ---
        log_message("\nAttempting to initialize SeleniumBase Driver...", f_results)
        driver = None
        try:
            # Try launching in headless mode first
            driver = Driver(browser="chromium", headless=True)
            log_message("SeleniumBase Driver initialized successfully in headless mode!", f_results)
            
            # Perform a simple navigation to confirm it works
            log_message("Navigating to example.com to confirm connectivity...", f_results)
            driver.get("http://example.com")
            log_message(f"Successfully navigated to example.com. Title: {driver.title}", f_results)
            log_message(f"Page Source Snippet:\n{driver.page_source[:500]}...", f_results) # Log a snippet
            
            log_message("\nBrowser launch and basic navigation SUCCESSFUL.", f_results)
            f_results.write("Overall Status: SUCCESS\n")

        except SessionNotCreatedException as e:
            log_message(f"SessionNotCreatedException: {e}", f_results)
            log_message("This often means the browser executable could not be started or found, or there's a compatibility issue with the WebDriver.", f_results)
            log_message("Possible causes: Missing browser, incorrect browser path, incompatible browser/driver version, or missing display server.", f_results)
            f_results.write("Overall Status: FAILED - SessionNotCreatedException\n")
        except WebDriverException as e:
            log_message(f"WebDriverException: {e}", f_results)
            log_message("This is a general WebDriver error. Check the full traceback for more details.", f_results)
            log_message("Ensure all browser dependencies are installed (e.g., fonts, libraries).", f_results)
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

        log_message("\n--- Browser Troubleshooting Complete ---", f_results)

if __name__ == "__main__":
    troubleshoot_browser_launch()
