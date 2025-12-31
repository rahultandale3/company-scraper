import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import csv

class LinkedInEJPTScraper:
    def __init__(self):
        self.driver = webdriver.Chrome()
        self.wait = WebDriverWait(self.driver, 10)
        self.data = []
        
    def login(self, email, password):
        """Login to LinkedIn (required for viewing profiles)"""
        self.driver.get("https://www.linkedin.com/login")
        self.driver.find_element(By.ID, "bellachav512@gmail.com").send_keys(email)
        self.driver.find_element(By.ID, "Rich@369").send_keys(password)
        self.driver.find_element(By.XPATH, "//button[@type='submit']").click()
        time.sleep(3)
    
    def search_ejpt_profiles(self):
        """Search for people with ejpt certification"""
        search_url = "https://www.linkedin.com/search/results/people/?keywords=ejpt%20certification"
        self.driver.get(search_url)
        time.sleep(3)
        
        # You'll need to implement pagination logic here
        # Note: LinkedIn shows ~10 pages max without premium
        
    def extract_profile_data(self, profile_url):
        """Extract data from individual profile"""
        self.driver.get(profile_url)
        time.sleep(2)
        
        try:
            # Get name
            name = self.driver.find_element(By.CSS_SELECTOR, "h1.text-heading-xlarge").text
            
            # Get current position and company
            experience_section = self.driver.find_element(By.ID, "experience-section")
            
            # Get company URL (this is tricky as LinkedIn obfuscates URLs)
            company_elements = experience_section.find_elements(By.CSS_SELECTOR, "a[data-field='experience_company_logo']")
            company_url = company_elements[0].get_attribute('href') if company_elements else ""
            
            # Get location
            location = self.driver.find_element(By.CSS_SELECTOR, "span.text-body-small").text
            
            return {
                'name': name,
                'profile_url': profile_url,
                'company_url': company_url,
                'location': location
            }
            
        except Exception as e:
            print(f"Error scraping {profile_url}: {e}")
            return None
    
    def save_to_csv(self, filename="ejpt_companies.csv"):
        """Save data to CSV"""
        df = pd.DataFrame(self.data)
        df.to_csv(filename, index=False)
        print(f"Saved {len(df)} records to {filename}")
    
    def close(self):
        self.driver.quit()

# Usage
scraper = LinkedInEJPTScraper()
# scraper.login("your_email", "your_password")  # Be cautious with credentials
# scraper.search_ejpt_profiles()
# scraper.close()
