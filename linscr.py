import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re
import time
import dns.resolver
import os
import subprocess
import random
import socket # Although not directly used for proxying in this version, kept for potential future use or debugging
from datetime import datetime

# Import SeleniumBase components
from seleniumbase import Driver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException, TimeoutException

class DNBScraperSelenium:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.7 (KHTML, like Gecko) Chrome/90.0.0.0 Safari/537.7'
        }
        self.microsoft_patterns = [
            'outlook.com', 'office365.com', 'microsoft.com', 'microsoftonline.com',
            'hotmail.com', 'msn.com', 'exchange.microsoft.com', 'sharepoint.com',
            'azure.com', 'onmicrosoft.com', 'skype.com', 'teams.microsoft.com',
            'mail.protection.outlook.com', 'protection.outlook.com', 'mail.microsoft.com',
            'outbound.protection.outlook.com', 'cloudapp.net', 'trafficmanager.net',
            'windows.net', 'azureedge.net', 'msecnd.net'
        ]
        self.processed_domains = set()
        self.start_time = time.time()
        self.failed_pages = set()
        self.driver = None # Selenium WebDriver instance
        self.current_vpn_config_file = None # To track which VPN config is currently active

        # List of your Mullvad WireGuard config files.
        # These files are expected to be in the same directory as this script.
        self.WIREGUARD_CONFIG_FILES = [
            "ch-zrh-wg-001.conf", "ch-zrh-wg-004.conf", "ch-zrh-wg-404.conf",
            "us-phx-wg-101.conf", "us-phx-wg-103.conf", "us-phx-wg-202.conf",
            "us-sjc-wg-002.conf", "us-sjc-wg-302.conf", "us-sjc-wg-504.conf",
        ]
        self.results_file = "scraper_results.txt"
        self.vpn_setup_wait_time = 5 # seconds to wait after bringing up VPN

    def log(self, message, task_time=None):
        """Logs messages with an elapsed time prefix."""
        elapsed = time.time() - self.start_time
        if task_time:
            print(f"[{elapsed:.2f}s] {message} (took {task_time:.2f}s)")
        else:
            print(f"[{elapsed:.2f}s] {message}")

    def read_urls(self):
        """Reads URLs and target counts from 'urls.txt'."""
        urls_data = []
        try:
            with open('urls.txt', 'r') as file:
                for line in file.readlines():
                    parts = line.strip().split(' ///// ')
                    if len(parts) == 2:
                        url = parts[0]
                        count = parts[1]
                        page_match = re.search(r'page=(\d+)', url)
                        start_page = int(page_match.group(1)) if page_match else 1
                        base_url = url.split('?')[0] if '?' in url else url
                        urls_data.append((base_url, count, start_page))
        except FileNotFoundError:
            self.log("Error: urls.txt not found. Please create this file with URLs and target counts.")
        return urls_data

    def clean_url(self, url):
        """Cleans and normalizes a URL string."""
        url = url.lower()
        url = re.sub(r'^https?://', '', url)
        url = re.sub(r'^www\.', '', url)
        return url.strip('/')

    def is_domain_processed(self, domain):
        """Checks if a domain has already been processed."""
        clean_domain = self.clean_url(domain)
        return clean_domain in self.processed_domains

    def add_domain(self, domain):
        """Adds a domain to the processed set and writes it to 'microlinks.txt'."""
        clean_domain = self.clean_url(domain)
        if clean_domain not in self.processed_domains:
            self.processed_domains.add(clean_domain)
            try:
                with open('microlinks.txt', 'a') as f:
                    f.write(f"{clean_domain}\n")
                return True
            except IOError as e:
                self.log(f"Error writing to microlinks.txt: {e}")
                return False
        return False

    def check_mx_records(self, domain):
        """Checks if a domain's MX records indicate Microsoft affiliation."""
        try:
            start_time = time.time()
            resolver = dns.resolver.Resolver()
            # Set a timeout for DNS queries
            resolver.timeout = 5
            resolver.lifetime = 5
            mx_records = resolver.resolve(domain, 'MX')
            mx_strings = [str(mx.exchange).rstrip('.').lower() for mx in mx_records]
            microsoft_found = []
            for mx in mx_strings:
                for pattern in self.microsoft_patterns:
                    if pattern in mx or mx.endswith('.' + pattern):
                        microsoft_found.append(mx)
                        break
            is_microsoft = len(microsoft_found) > 0
            self.log(f"MX lookup for {domain}: {'Microsoft affiliated' if is_microsoft else 'Not Microsoft'}",
                     time.time() - start_time)
            if microsoft_found:
                self.log(f"Microsoft patterns found in MX records: {microsoft_found}")
            return is_microsoft
        except dns.resolver.NoAnswer:
            self.log(f"MX lookup for {domain}: No MX records found.")
            return False
        except dns.resolver.NXDOMAIN:
            self.log(f"MX lookup for {domain}: Domain does not exist.")
            return False
        except dns.resolver.Timeout:
            self.log(f"MX lookup for {domain}: DNS query timed out.")
            return False
        except Exception as e:
            self.log(f"MX lookup failed for {domain}: {str(e)}")
            return False

    def is_microsoft_affiliated(self, website):
        """Determines if a website is Microsoft affiliated based on MX records."""
        try:
            clean_domain = self.clean_url(website)
            self.log(f"Checking Microsoft affiliation for domain: {clean_domain}")
            return self.check_mx_records(clean_domain)
        except Exception as e:
            self.log(f"Error checking Microsoft affiliation: {str(e)}")
            return False

    def bring_up_vpn(self, config_file):
        """Brings up a WireGuard VPN tunnel using wg-quick."""
        config_path = os.path.join(os.getcwd(), config_file)
        self.log(f"Attempting to bring up WireGuard tunnel with '{config_file}'...")
        # Use sudo as wg-quick typically requires root privileges to manage network interfaces.
        up_command = ['sudo', 'wg-quick', 'up', config_path]
        up_process = subprocess.run(up_command, capture_output=True, text=True, check=False)

        if up_process.returncode != 0:
            self.log(f"Error bringing up VPN: {up_process.stderr.strip()}")
            return False
        self.log(f"VPN tunnel for '{config_file}' brought up successfully. Waiting {self.vpn_setup_wait_time} seconds...")
        time.sleep(self.vpn_setup_wait_time)
        self.current_vpn_config_file = config_file
        return True

    def bring_down_vpn(self):
        """Brings down the currently active WireGuard VPN tunnel."""
        if not self.current_vpn_config_file:
            return # No VPN is currently active
        
        config_path = os.path.join(os.getcwd(), self.current_vpn_config_file)
        self.log(f"Attempting to bring down WireGuard tunnel for '{self.current_vpn_config_file}'...")
        down_command = ['sudo', 'wg-quick', 'down', config_path]
        down_process = subprocess.run(down_command, capture_output=True, text=True, check=False)

        if down_process.returncode != 0:
            self.log(f"Error bringing down VPN: {down_process.stderr.strip()}")
        else:
            self.log(f"VPN tunnel for '{self.current_vpn_config_file}' brought down successfully.")
        self.current_vpn_config_file = None

    def initialize_driver(self):
        """Initializes the SeleniumBase WebDriver."""
        # SeleniumBase Driver will automatically use the system's network configuration,
        # which will be routed through the active WireGuard VPN.
        try:
            self.driver = Driver(browser="chromium", headless=True) # Use chromium for GitHub Actions
            self.driver.set_page_load_timeout(60) # Set page load timeout to 60 seconds
            self.log("Selenium WebDriver initialized in headless mode.")
        except Exception as e:
            self.log(f"Error initializing Selenium WebDriver: {e}")
            self.driver = None

    def quit_driver(self):
        """Quits the Selenium WebDriver."""
        if self.driver:
            self.driver.quit()
            self.driver = None
            self.log("Selenium WebDriver quit.")

    def scrape_company_websites(self, url):
        """Scrapes company websites from a given D&B page using SeleniumBase."""
        websites = []
        try:
            start_task = time.time()
            self.log(f"Navigating to D&B page: {url}")
            self.driver.get(url) # Navigate using SeleniumBase

            # Get page source after navigation
            content = self.driver.page_source
            soup = BeautifulSoup(content, 'html.parser')
            
            # Find links to individual company profiles
            company_links = soup.find_all('a', href=lambda x: x and '/business-directory/company-profiles.' in x)
            self.log(f"Found {len(company_links)} company profile links on this page", time.time() - start_task)

            for idx, link in enumerate(company_links, 1):
                link_start = time.time()
                company_page_url = urljoin(url, link['href'])
                self.log(f"Processing company profile link {idx}/{len(company_links)}: {company_page_url}")
                website = self.get_company_website(company_page_url)
                if website:
                    self.log(f"Found company website: {website}", time.time() - link_start)
                    websites.append(website)
                else:
                    self.log(f"No website found for company page", time.time() - link_start)
            return websites
        except TimeoutException:
            self.log(f"Navigation to {url} timed out.")
            return []
        except WebDriverException as e:
            self.log(f"WebDriver error while scraping {url}: {e}")
            return []
        except Exception as e:
            self.log(f"Error scraping {url}: {e}")
            return []

    def get_company_website(self, company_page_url):
        """Extracts the main website URL from a company profile page using SeleniumBase."""
        try:
            start_time = time.time()
            self.driver.get(company_page_url) # Navigate using SeleniumBase
            content = self.driver.page_source
            soup = BeautifulSoup(content, 'html.parser')

            # Find the website link element (assuming it has id='hero-company-link')
            website_element = soup.find('a', id='hero-company-link')
            result = None
            if website_element and website_element.get('href'):
                raw_url = website_element['href']
                clean_url = self.clean_url(raw_url)
                self.log(f"Retrieved and cleaned website URL: {clean_url}", time.time() - start_time)
                result = clean_url
            return result
        except TimeoutException:
            self.log(f"Navigation to {company_page_url} timed out.")
            return None
        except WebDriverException as e:
            self.log(f"WebDriver error while getting company website from {company_page_url}: {e}")
            return None
        except Exception as e:
            self.log(f"Error getting company website from {company_page_url}: {e}")
            return None

    def get_paginated_url(self, base_url, page_number):
        """Constructs a paginated URL."""
        if '?' in base_url:
            base_url = base_url.split('?')[0]
        return f"{base_url}?page={page_number}"

    def main(self):
        """Main execution flow of the scraper."""
        urls_with_counts = self.read_urls()
        if not urls_with_counts:
            self.log("No URLs to process. Exiting.")
            return

        MAX_PAGES = 20
        MAX_RETRIES = 3 # Maximum number of retries for failed pages

        # Open results file once at the beginning to write all results
        with open(self.results_file, 'w') as f_results:
            f_results.write(f"--- DNB Scraper Run: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---\n\n")

            for config_file in self.WIREGUARD_CONFIG_FILES:
                self.log(f"\n--- Starting scraping with WireGuard config: {config_file} ---")
                f_results.write(f"\n--- WireGuard Config: {config_file} ---\n")

                if not self.bring_up_vpn(config_file):
                    self.log(f"Skipping config {config_file} due to VPN setup failure.")
                    f_results.write(f"  VPN Setup Failed. Skipping this config.\n\n")
                    continue

                # Initialize driver *after* VPN is up so it uses the VPN tunnel
                self.initialize_driver()
                if not self.driver:
                    self.log(f"Could not initialize browser for {config_file}. Skipping this config.")
                    f_results.write(f"  Browser Initialization Failed. Skipping this config.\n\n")
                    self.bring_down_vpn() # Attempt to bring down VPN even if browser failed
                    continue

                try:
                    # Test current IP through the VPN using Selenium to confirm connectivity
                    self.driver.get("https://ifconfig.me/ip")
                    current_ip = self.driver.page_source.strip()
                    self.log(f"Current Public IP through VPN: {current_ip}")
                    f_results.write(f"  Public IP through VPN: {current_ip}\n")

                    # Now, run the actual scraping logic for this VPN
                    for base_url, count, start_page in urls_with_counts:
                        ms_count = 0
                        target_count = int(count)
                        page_number = start_page
                        last_successful_page = page_number - 1
                        retry_count = 0
                        self.log(f"Starting to process URL: {base_url} for {target_count} Microsoft-affiliated sites.")
                        f_results.write(f"  Processing URL: {base_url} (Target: {target_count} MS sites)\n")

                        while ms_count < target_count and page_number <= MAX_PAGES:
                            current_url = self.get_paginated_url(base_url, page_number)
                            self.log(f"Scraping page {page_number}/{MAX_PAGES}: {current_url}")
                            
                            websites = self.scrape_company_websites(current_url)

                            if websites:
                                # If this page has data but we skipped some pages, go back and retry
                                if page_number > last_successful_page + 1 and retry_count < MAX_RETRIES:
                                    retry_pages = list(range(last_successful_page + 1, page_number))
                                    self.log(f"Found data on page {page_number} but missed pages {retry_pages}. Retrying from {last_successful_page + 1}...")
                                    page_number = last_successful_page + 1
                                    retry_count += 1
                                    continue # Re-enter loop to process the missed page

                                last_successful_page = page_number
                                retry_count = 0  # Reset retry counter on success
                                
                                for website in websites:
                                    if website and not self.is_domain_processed(website):
                                        if self.is_microsoft_affiliated(website):
                                            if self.add_domain(website):
                                                ms_count += 1
                                                self.log(f"Found Microsoft-affiliated website ({ms_count}/{target_count}): {website}")
                                                f_results.write(f"    Found MS-affiliated: {website}\n")
                                            if ms_count >= target_count:
                                                break # Found enough for this URL
                            else:
                                self.log(f"No companies found on page {page_number}.")
                                f_results.write(f"    No companies found on page {page_number}.\n")
                                self.failed_pages.add(page_number)

                            if ms_count >= target_count:
                                break # Found enough for this URL
                            page_number += 1

                        if ms_count < target_count:
                            self.log(f"Could only find {ms_count} Microsoft-affiliated websites out of {target_count} requested for {base_url}")
                            f_results.write(f"  Finished {base_url}. Found {ms_count}/{target_count} MS-affiliated sites.\n")
                        else:
                            self.log(f"Successfully found {ms_count} Microsoft-affiliated websites for {base_url}.")
                            f_results.write(f"  Finished {base_url}. Successfully found {ms_count} MS-affiliated sites.\n")

                        if self.failed_pages:
                            self.log(f"Failed to process pages for {base_url}: {sorted(self.failed_pages)}")
                            f_results.write(f"  Failed pages for {base_url}: {sorted(self.failed_pages)}\n")
                        self.failed_pages.clear() # Clear for next URL/config
                    f_results.write("\n") # Add a newline for readability between configs

                finally:
                    self.quit_driver() # Quit driver before bringing down VPN
                    self.bring_down_vpn() # Bring down VPN after scraping with it

            self.log(f"All scraping tests completed. Results saved to '{self.results_file}'.")

if __name__ == "__main__":
    scraper = DNBScraperSelenium()
    scraper.main()
