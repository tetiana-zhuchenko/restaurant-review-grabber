"""
Google Maps Reviews Scraper using Selenium 

"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
import time
import json
from datetime import datetime

class GoogleMapsReviewsScraper:
    def __init__(self, headless=True):
        """Initialize the scraper with Chrome driver"""
        self.setup_driver(headless)
        
    def setup_driver(self, headless=True):
        """Setup Chrome driver with appropriate options"""
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self.wait = WebDriverWait(self.driver, 15)
        
    def search_restaurant(self, restaurant_name, city="Київ"):
        """Search for a restaurant on Google Maps"""
        query = f"{restaurant_name} {city}"
        search_url = f"https://www.google.com/maps/search/{query.replace(' ', '+')}"
        
        print(f"🔍 Searching: {query}")
        self.driver.get(search_url)
        time.sleep(10)
        
        # Check if we're already on a restaurant page
        current_url = self.driver.current_url
        if 'place/' in current_url:
            print(f"   ✅ Already on restaurant page")
            return True
        
        # Try to find and click the first restaurant
        try:
            print("   🎯 Looking for restaurant...")
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "[data-result-index='0']"))
            )
            
            first_restaurant = self.driver.find_element(By.CSS_SELECTOR, "[data-result-index='0']")
            self.driver.execute_script("arguments[0].scrollIntoView(true);", first_restaurant)
            time.sleep(2)
            ActionChains(self.driver).move_to_element(first_restaurant).click().perform()
            time.sleep(5)
            
            if 'place/' in self.driver.current_url:
                print("   ✅ Successfully opened restaurant page")
                return True
                
        except Exception as e:
            print(f"   ❌ Could not find restaurant: {e}")
            
        return False
    
    def click_reviews_tab(self):
        """Click on reviews tab"""
        print("   🔍 Looking for reviews tab...")
        time.sleep(5)
        
        # Check if reviews are already visible
        existing_reviews = self.driver.find_elements(By.CSS_SELECTOR, "[data-review-id]")
        if len(existing_reviews) > 0:
            print(f"   ✅ Reviews already visible - found {len(existing_reviews)} reviews")
            return True
        
        # Find and click reviews tab
        try:
            all_tabs = self.driver.find_elements(By.CSS_SELECTOR, "button[role='tab']")
            print(f"   📋 Found {len(all_tabs)} tabs")
            
            for i, tab in enumerate(all_tabs):
                tab_text = tab.text.strip()
                tab_label = tab.get_attribute('aria-label') or ''
                tab_index = tab.get_attribute('data-tab-index') or ''
                
                print(f"      Tab {i}: '{tab_text}' | Index: '{tab_index}'")
                
                # Check if this is the reviews tab
                if (tab_index == '2' or 
                    'відгук' in tab_text.lower() or 
                    'відгук' in tab_label.lower() or
                    'reviews' in tab_label.lower()):
                    
                    print(f"   ✅ Found reviews tab: {tab_text}")
                    
                    # Click the tab
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", tab)
                    time.sleep(1)
                    self.driver.execute_script("arguments[0].removeAttribute('tabindex');", tab)
                    self.driver.execute_script("arguments[0].click();", tab)
                    time.sleep(5)
                    
                    reviews = self.driver.find_elements(By.CSS_SELECTOR, "[data-review-id]")
                    if reviews:
                        print(f"   ✅ Successfully loaded reviews - found {len(reviews)} reviews")
                        return True
                        
        except Exception as e:
            print(f"   ❌ Could not click reviews tab: {e}")
        
        return False
    
    def load_more_reviews(self, max_reviews=200):
        """Scroll to load more reviews"""
        print(f"   📜 Loading more reviews (target: {max_reviews})...")
        
        last_review_count = 0
        attempts = 0
        max_attempts = 40
        
        while attempts < max_attempts:
            # Scroll down
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)
            
            # Count current reviews
            reviews = self.driver.find_elements(By.CSS_SELECTOR, "[data-review-id]")
            current_count = len(reviews)
            
            print(f"      Currently loaded: {current_count} reviews")
            
            if current_count >= max_reviews or current_count == last_review_count:
                break
                
            last_review_count = current_count
            attempts += 1
            
        print(f"   ✅ Loaded {len(reviews)} reviews total")
        return len(reviews)
    
    def extract_reviews(self):
        """Extract all review data from the current page"""
        reviews_data = []
        
        review_elements = self.driver.find_elements(By.CSS_SELECTOR, "[data-review-id]")
        print(f"   🔍 Extracting data from {len(review_elements)} reviews...")
        
        for i, review_element in enumerate(review_elements, 1):
            try:
                review_data = self.extract_single_review(review_element)
                if review_data and review_data.get('text'):
                    reviews_data.append(review_data)
                        
            except Exception as e:
                print(f"      ❌ Error extracting review {i}: {e}")
                continue
        
        print(f"   📊 Extracted {len(reviews_data)} total reviews")
        return reviews_data
    
    def extract_single_review(self, review_element):
        """Extract data from a single review element"""
        review_data = {}
        
        # Author name
        try:
            author_selectors = [".d4r55.fontTitleMedium", ".d4r55", ".WNxzHc .d4r55"]
            author_name = "Anonymous"
            
            for selector in author_selectors:
                try:
                    author_elem = review_element.find_element(By.CSS_SELECTOR, selector)
                    author_name = author_elem.text.strip()
                    if author_name:
                        break
                except:
                    continue
                    
            review_data['author'] = author_name
        except:
            review_data['author'] = "Anonymous"
        
        # Rating
        try:
            stars = review_element.find_elements(By.CSS_SELECTOR, ".kvMYJc span.hCCjke.google-symbols.NhBTye.elGi1d")
            review_data['rating'] = len(stars)
        except:
            review_data['rating'] = 0
        
        # Review text
        try:
            text_selectors = [".wiI7pd", ".MyEned .wiI7pd", ".MyEned span.wiI7pd"]
            review_text = ""
            
            for selector in text_selectors:
                try:
                    text_elem = review_element.find_element(By.CSS_SELECTOR, selector)
                    review_text = text_elem.text.strip()
                    if review_text and len(review_text) > 5:
                        break
                except:
                    continue
                    
            review_data['text'] = review_text
        except:
            review_data['text'] = ""
        
        # Time
        try:
            time_elem = review_element.find_element(By.CSS_SELECTOR, ".rsqaWe")
            review_data['time'] = time_elem.text.strip()
        except:
            review_data['time'] = ""
        
        return review_data
    
    def scrape_restaurant_reviews(self, restaurant_name, city="Київ", max_reviews=200):
        """Complete workflow to scrape reviews for one restaurant"""
        
        if not self.search_restaurant(restaurant_name, city):
            return []
        
        if not self.click_reviews_tab():
            print("   ❌ Could not access reviews tab")
            return []
        
        total_loaded = self.load_more_reviews(max_reviews)
        
        if total_loaded == 0:
            print("   ❌ No reviews found")
            return []
        
        reviews = self.extract_reviews()
        
        # Add restaurant metadata
        for review in reviews:
            review['restaurant_name'] = restaurant_name
            review['restaurant_city'] = city
            review['scraped_at'] = datetime.now().isoformat()
        
        return reviews
    
    def close(self):
        """Close the browser"""
        self.driver.quit()

def scrape_multiple_restaurants(restaurant_list, max_reviews_per_restaurant=50):
    """Scrape reviews from multiple restaurants"""
    
    all_reviews = []
    scraper = GoogleMapsReviewsScraper(headless=False)
    
    try:
        for i, restaurant_name in enumerate(restaurant_list, 1):
            print(f"\n[{i}/{len(restaurant_list)}] Processing: {restaurant_name}")
            print("=" * 60)
            
            reviews = scraper.scrape_restaurant_reviews(
                restaurant_name, 
                city="Київ",
                max_reviews=max_reviews_per_restaurant
            )
            
            all_reviews.extend(reviews)
            print(f"✅ Collected {len(reviews)} total reviews")
            time.sleep(3)
            
    finally:
        scraper.close()
    
    return all_reviews

def save_reviews(all_reviews):
    """Save reviews to JSON file"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    with open(f"gmaps_reviews_{timestamp}.json", "w", encoding="utf-8") as f:
        json.dump(all_reviews, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 Saved {len(all_reviews)} total reviews")

if __name__ == "__main__":
    test_restaurants = [
        "Mafia",
        "Хачапурі та Вино", 
        "Евразія",
        "Чорноморка",
        "Чорноморка"
    ]
    
    print("🇺🇦 Google Maps Reviews Scraper - SIMPLIFIED VERSION")
    print("=" * 50)
    print("⚠️  Make sure you have Chrome browser installed")
    print("⚠️  Install: pip install selenium")
    print()
    
    all_reviews = scrape_multiple_restaurants(
        test_restaurants, 
        max_reviews_per_restaurant=200
    )
    
    save_reviews(all_reviews)
    
    print(f"\n🎉 Scraping completed!")
    print(f"📊 Total reviews: {len(all_reviews)}")
    
    if all_reviews:
        print(f"\n📄 Sample review:")
        sample = all_reviews[0]
        print(f"Restaurant: {sample['restaurant_name']}")
        print(f"Author: {sample['author']}")
        print(f"Rating: {sample['rating']}⭐")
        print(f"Text: {sample['text'][:150]}...")