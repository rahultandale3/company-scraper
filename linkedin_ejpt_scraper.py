import time
import random
import pandas as pd
import logging
from typing import List, Dict, Optional
from datetime import datetime
from tqdm import tqdm
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import selenium components
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, 
    NoSuchElementException, 
    ElementClickInterceptedException,
    StaleElementReferenceException
)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# For more stealth
from fake_useragent import UserAgent

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class LinkedInEJPTScraper:
    def __init__(self, headless: bool = False, max_pages: int = 100):
        """
        Initialize the LinkedIn EJPT Scraper
        
        Args:
            headless: Run browser in headless mode
            max_pages: Maximum number of search result pages to scrape
        """
        self.max_pages = max_pages
        self.headless = headless
        self.driver = None
        self.wait = None
        self.data = []
        self.visited_profiles = set()
        
        # Configuration
        self.base_url = "https://www.linkedin.com"
        self.search_url = f"{self.base_url}/search/results/people/"
        self.results_per_page = 10  # LinkedIn shows 10 results per page
        
        # Delays (to avoid detection)
        self.min_delay = 2
        self.max_delay = 5
        self.page_load_delay = 3
        self.scroll_pause_time = 1
        
        # Initialize driver
        self._setup_driver()
        
    def _setup_driver(self):
        """Setup Chrome driver with anti-detection features"""
        try:
            chrome_options = Options()
            
            if self.headless:
                chrome_options.add_argument("--headless")
            
            # Anti-detection arguments
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            
            # Random user agent
            ua = UserAgent()
            user_agent = ua.random
            chrome_options.add_argument(f'user-agent={user_agent}')
            
            # Disable automation flags
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Initialize driver
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Execute CDP commands to prevent detection
            self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                "userAgent": user_agent,
                "platform": "Windows"
            })
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            self.wait = WebDriverWait(self.driver, 30)
            logger.info("Chrome driver initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to setup driver: {e}")
            raise
    
    def _random_delay(self, min_seconds=None, max_seconds=None):
        """Add random delay between actions"""
        min_s = min_seconds or self.min_delay
        max_s = max_seconds or self.max_delay
        time.sleep(random.uniform(min_s, max_s))
    
    def _scroll_page(self, scroll_pause_time=None):
        """Scroll the page to load all content"""
        pause_time = scroll_pause_time or self.scroll_pause_time
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        
        while True:
            # Scroll down
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            self._random_delay(pause_time, pause_time + 1)
            
            # Calculate new scroll height
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
    
    def login(self, email: str = None, password: str = None):
        """
        Login to LinkedIn
        
        Args:
            email: LinkedIn email (from env if not provided)
            password: LinkedIn password (from env if not provided)
        """
        try:
            # Get credentials from env if not provided
            if not email or not password:
                email = os.getenv('LINKEDIN_EMAIL')
                password = os.getenv('LINKEDIN_PASSWORD')
                
                if not email or not password:
                    logger.warning("No credentials provided. Continuing without login (limited access)")
                    return False
            
            logger.info(f"Logging in with email: {email[:3]}...")
            
            # Go to login page
            self.driver.get(f"{self.base_url}/login")
            self._random_delay(3, 5)
            
            # Fill email
            email_field = self.wait.until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            email_field.clear()
            email_field.send_keys(email)
            self._random_delay(1, 2)
            
            # Fill password
            password_field = self.driver.find_element(By.ID, "password")
            password_field.clear()
            password_field.send_keys(password)
            self._random_delay(1, 2)
            
            # Click submit
            submit_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            submit_button.click()
            
            # Wait for login to complete
            self._random_delay(5, 7)
            
            # Check if login was successful
            if "feed" in self.driver.current_url or "login" not in self.driver.current_url:
                logger.info("Login successful!")
                return True
            else:
                logger.warning("Login may have failed. Check credentials or CAPTCHA.")
                return False
                
        except Exception as e:
            logger.error(f"Login failed: {e}")
            return False
    
    def search_ejpt_profiles(self, keywords: str = "ejpt certification"):
        """
        Search for profiles with EJPT certification
        
        Args:
            keywords: Search keywords
        """
        try:
            # Construct search URL
            params = {
                "keywords": keywords,
                "origin": "GLOBAL_SEARCH_HEADER"
            }
            query_string = "&".join([f"{k}={v}" for k, v in params.items()])
            search_url = f"{self.search_url}?{query_string}"
            
            logger.info(f"Searching for: {keywords}")
            self.driver.get(search_url)
            self._random_delay(4, 6)
            
            # Check for search results
            try:
                results_count = self.driver.find_element(
                    By.CLASS_NAME, "search-results__total"
                ).text
                logger.info(f"Search results: {results_count}")
            except:
                logger.info("No results count found")
            
            # Scroll to load all results
            self._scroll_page()
            
            return True
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return False
    
    def get_profile_urls_from_page(self) -> List[str]:
        """Extract profile URLs from current search results page"""
        profile_urls = []
        
        try:
            # Find all profile links in search results
            profile_elements = self.driver.find_elements(
                By.XPATH, "//a[contains(@href, '/in/') and @data-test-app-aware-link]"
            )
            
            for element in profile_elements:
                profile_url = element.get_attribute("href")
                if profile_url and "/in/" in profile_url:
                    # Clean URL
                    profile_url = profile_url.split('?')[0]  # Remove query params
                    if profile_url not in self.visited_profiles:
                        profile_urls.append(profile_url)
                        self.visited_profiles.add(profile_url)
            
            logger.info(f"Found {len(profile_urls)} new profile URLs on this page")
            
        except Exception as e:
            logger.error(f"Error extracting profile URLs: {e}")
        
        return profile_urls
    
    def go_to_next_page(self) -> bool:
        """Navigate to next page of search results"""
        try:
            # Find and click next button
            next_button = self.driver.find_element(
                By.XPATH, "//button[contains(@aria-label, 'Next')]"
            )
            
            if next_button.is_enabled():
                # Scroll to button
                self.driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
                self._random_delay(2, 3)
                
                # Click using JavaScript (more reliable)
                self.driver.execute_script("arguments[0].click();", next_button)
                self._random_delay(4, 6)
                
                # Wait for page to load
                self.wait.until(
                    EC.presence_of_element_located((By.CLASS_NAME, "search-results"))
                )
                
                # Scroll to load content
                self._scroll_page()
                
                logger.info("Navigated to next page")
                return True
            else:
                logger.info("No more pages available")
                return False
                
        except NoSuchElementException:
            logger.info("Next button not found - end of results")
            return False
        except Exception as e:
            logger.error(f"Error navigating to next page: {e}")
            return False
    
    def extract_profile_data(self, profile_url: str) -> Optional[Dict]:
        """
        Extract data from individual LinkedIn profile
        
        Args:
            profile_url: URL of the LinkedIn profile
        """
        try:
            logger.info(f"Extracting data from: {profile_url}")
            self.driver.get(profile_url)
            self._random_delay(3, 5)
            
            profile_data = {
                "profile_url": profile_url,
                "scraped_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "name": "",
                "headline": "",
                "location": "",
                "current_company": "",
                "current_company_url": "",
                "ejpt_mentioned": False,
                "experience": []
            }
            
            # Extract basic info
            try:
                # Name
                name_element = self.wait.until(
                    EC.presence_of_element_located((By.TAG_NAME, "h1"))
                )
                profile_data["name"] = name_element.text.strip()
            except:
                pass
            
            # Headline
            try:
                headline = self.driver.find_element(
                    By.CLASS_NAME, "text-body-medium"
                ).text.strip()
                profile_data["headline"] = headline
                
                # Check if EJPT is mentioned in headline
                if "ejpt" in headline.lower():
                    profile_data["ejpt_mentioned"] = True
            except:
                pass
            
            # Location
            try:
                location = self.driver.find_element(
                    By.XPATH, "//span[contains(@class, 'text-body-small')]"
                ).text.strip()
                profile_data["location"] = location
            except:
                pass
            
            # Scroll to load all sections
            self._scroll_page()
            
            # Extract experience section
            self._extract_experience(profile_data)
            
            # Check for certifications section for EJPT
            self._check_certifications(profile_data)
            
            # If no company found in experience, try from current position
            if not profile_data["current_company"]:
                self._extract_current_position(profile_data)
            
            logger.info(f"Successfully extracted data for: {profile_data['name']}")
            return profile_data
            
        except Exception as e:
            logger.error(f"Error extracting data from {profile_url}: {e}")
            return None
    
    def _extract_experience(self, profile_data: Dict):
        """Extract experience section from profile"""
        try:
            # Try to find experience section
            experience_section = self.driver.find_element(By.ID, "experience-section")
            
            # Find all experience items
            experience_items = experience_section.find_elements(
                By.CSS_SELECTOR, "li.artdeco-list__item"
            )
            
            for item in experience_items:
                try:
                    exp_data = {}
                    
                    # Company name
                    try:
                        company_element = item.find_element(
                            By.CSS_SELECTOR, "a[data-field='experience_company_logo']"
                        )
                        exp_data["company"] = company_element.text.strip()
                        exp_data["company_url"] = company_element.get_attribute("href")
                        
                        # Set as current company if it's the first one
                        if not profile_data["current_company"]:
                            profile_data["current_company"] = exp_data["company"]
                            profile_data["current_company_url"] = exp_data["company_url"]
                            
                    except:
                        pass
                    
                    # Position/title
                    try:
                        title = item.find_element(
                            By.CSS_SELECTOR, "span[aria-hidden='true']"
                        ).text.strip()
                        exp_data["position"] = title
                    except:
                        pass
                    
                    # Duration
                    try:
                        duration = item.find_element(
                            By.CSS_SELECTOR, "span.tvm__text"
                        ).text.strip()
                        exp_data["duration"] = duration
                    except:
                        pass
                    
                    # Location
                    try:
                        location = item.find_element(
                            By.CSS_SELECTOR, "span.experience-item__location"
                        ).text.strip()
                        exp_data["location"] = location
                    except:
                        pass
                    
                    if exp_data:
                        profile_data["experience"].append(exp_data)
                        
                except Exception as e:
                    continue  # Skip this experience item if there's an error
                    
        except NoSuchElementException:
            logger.debug("No experience section found")
        except Exception as e:
            logger.error(f"Error extracting experience: {e}")
    
    def _check_certifications(self, profile_data: Dict):
        """Check certifications section for EJPT"""
        try:
            # Look for certifications section
            certifications_section = self.driver.find_element(By.ID, "licenses_and_certifications-section")
            
            # Check if EJPT is mentioned
            certifications_text = certifications_section.text.lower()
            if "ejpt" in certifications_text or "eLearnSecurity" in certifications_text:
                profile_data["ejpt_mentioned"] = True
                
        except NoSuchElementException:
            pass  # No certifications section
        except Exception as e:
            logger.debug(f"Error checking certifications: {e}")
    
    def _extract_current_position(self, profile_data: Dict):
        """Extract current position if not found in experience"""
        try:
            # Try to get current position from main profile section
            current_position = self.driver.find_element(
                By.CSS_SELECTOR, "div.text-body-medium.break-words"
            ).text.strip()
            
            # Extract company from position text (heuristic)
            if " at " in current_position:
                parts = current_position.split(" at ")
                if len(parts) > 1:
                    profile_data["current_company"] = parts[1].strip()
                    
        except:
            pass
    
    def scrape_multiple_pages(self, start_page: int = 1) -> List[Dict]:
        """
        Scrape multiple pages of search results
        
        Args:
            start_page: Page number to start from
        """
        all_data = []
        
        try:
            for page in range(start_page, self.max_pages + 1):
                logger.info(f"Scraping page {page}")
                
                # Get profile URLs from current page
                profile_urls = self.get_profile_urls_from_page()
                
                if not profile_urls:
                    logger.warning(f"No profiles found on page {page}")
                    break
                
                # Process each profile
                for url in tqdm(profile_urls, desc=f"Page {page}"):
                    try:
                        profile_data = self.extract_profile_data(url)
                        if profile_data:
                            all_data.append(profile_data)
                            self.data.append(profile_data)
                            
                            # Save incremental backup
                            if len(all_data) % 10 == 0:
                                self._save_backup(all_data)
                            
                        # Random delay between profiles
                        self._random_delay(3, 7)
                        
                    except Exception as e:
                        logger.error(f"Error processing {url}: {e}")
                        continue
                
                # Save data after each page
                if all_data:
                    self.save_to_csv(f"ejpt_data_page_{page}.csv")
                
                # Go to next page
                if not self.go_to_next_page():
                    logger.info("Reached end of search results")
                    break
                
                # Random delay between pages
                self._random_delay(5, 10)
                
        except KeyboardInterrupt:
            logger.info("Scraping interrupted by user")
        except Exception as e:
            logger.error(f"Scraping failed: {e}")
        
        return all_data
    
    def _save_backup(self, data: List[Dict], filename: str = "backup_data.json"):
        """Save backup of scraped data"""
        try:
            df = pd.DataFrame(data)
            df.to_json(filename, orient='records', indent=2)
            logger.info(f"Backup saved to {filename}")
        except Exception as e:
            logger.error(f"Failed to save backup: {e}")
    
    def save_to_csv(self, filename: str = "ejpt_companies_analysis.csv"):
        """Save scraped data to CSV with analysis"""
        try:
            if not self.data:
                logger.warning("No data to save")
                return
            
            # Create DataFrame
            df = pd.DataFrame(self.data)
            
            # Flatten experience data
            flattened_data = []
            for record in self.data:
                base_record = {k: v for k, v in record.items() if k != 'experience'}
                
                if record['experience']:
                    for exp in record['experience']:
                        flattened_record = base_record.copy()
                        flattened_record.update({
                            f"exp_{k}": v for k, v in exp.items()
                        })
                        flattened_data.append(flattened_record)
                else:
                    flattened_data.append(base_record)
            
            df_flat = pd.DataFrame(flattened_data)
            
            # Save to CSV
            df_flat.to_csv(filename, index=False, encoding='utf-8')
            logger.info(f"Saved {len(df_flat)} records to {filename}")
            
            # Generate analysis
            self._generate_analysis(df_flat, filename.replace('.csv', '_analysis.txt'))
            
            return df_flat
            
        except Exception as e:
            logger.error(f"Error saving data: {e}")
    
    def _generate_analysis(self, df: pd.DataFrame, output_file: str):
        """Generate analysis report"""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("=== EJPT Professionals Analysis Report ===\n\n")
                f.write(f"Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Total profiles analyzed: {len(df)}\n")
                
                # Company analysis
                if 'exp_company' in df.columns:
                    company_counts = df['exp_company'].value_counts().head(20)
                    f.write("\n=== Top 20 Companies Hiring EJPT Professionals ===\n")
                    for company, count in company_counts.items():
                        if company:  # Skip empty values
                            f.write(f"{company}: {count} professionals\n")
                
                # Location analysis
                if 'location' in df.columns:
                    location_counts = df['location'].value_counts().head(15)
                    f.write("\n=== Top 15 Locations ===\n")
                    for location, count in location_counts.items():
                        if location:
                            f.write(f"{location}: {count} professionals\n")
                
                # EJPT mention analysis
                ejpt_count = df['ejpt_mentioned'].sum() if 'ejpt_mentioned' in df.columns else 0
                f.write(f"\n=== EJPT Mention Analysis ===\n")
                f.write(f"Profiles explicitly mentioning EJPT: {ejpt_count}\n")
                f.write(f"Percentage: {(ejpt_count/len(df)*100):.1f}%\n")
            
            logger.info(f"Analysis report saved to {output_file}")
            
        except Exception as e:
            logger.error(f"Error generating analysis: {e}")
    
    def close(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit()
            logger.info("Browser closed")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def main():
    """Main function to run the scraper"""
    print("=== LinkedIn EJPT Professionals Scraper ===\n")
    
    # Configuration
    USE_HEADLESS = False  # Set to True for production
    MAX_PAGES = 100
    START_PAGE = 1
    
    # Initialize scraper
    scraper = LinkedInEJPTScraper(headless=USE_HEADLESS, max_pages=MAX_PAGES)
    
    try:
        # Login (optional - remove if you want public access only)
        # scraper.login()
        
        # Search for EJPT profiles
        if scraper.search_ejpt_profiles():
            print("Search successful! Starting to scrape...\n")
            
            # Scrape multiple pages
            all_data = scraper.scrape_multiple_pages(start_page=START_PAGE)
            
            # Save final results
            if all_data:
                df = scraper.save_to_csv("final_ejpt_companies.csv")
                
                # Print summary
                print("\n=== Scraping Complete ===")
                print(f"Total profiles scraped: {len(all_data)}")
                print(f"Unique companies found: {df['exp_company'].nunique() if 'exp_company' in df.columns else 0}")
                print(f"Data saved to: final_ejpt_companies.csv")
            else:
                print("No data was scraped.")
        
        else:
            print("Search failed. Check your connection or search parameters.")
            
    except KeyboardInterrupt:
        print("\nScraping interrupted by user.")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Close browser
        scraper.close()
        
        # Create summary file
        summary_file = "scraping_summary.txt"
        with open(summary_file, 'w') as f:
            f.write(f"Scraping completed: {datetime.now()}\n")
            f.write(f"Profiles scraped: {len(scraper.data)}\n")
            f.write(f"Unique profiles visited: {len(scraper.visited_profiles)}\n")
        
        print(f"\nSummary saved to: {summary_file}")


if __name__ == "__main__":
    main()
