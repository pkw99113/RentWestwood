from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import random
import pandas as pd
from webdriver_manager.chrome import ChromeDriverManager
from selenium_stealth import stealth
from selenium.webdriver.common.action_chains import ActionChains




    

# Set up Selenium WebDriver
options = webdriver.ChromeOptions()
options.add_argument("user-agent=Mozilla/5.0 (Macintosh; ARM64 Mac OS X 14_6_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36")
options.add_argument("window-size=1920,1080")
options.add_argument("--incognito")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)

#user agent
user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:93.0) Gecko/20100101 Firefox/93.0"
]
options.add_argument(f"user-agent={random.choice(user_agents)}")


# Initialize WebDriver
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

#randomized mouse movements
def simulate_human_movement(driver):
    actions = ActionChains(driver)
    actions.move_by_offset(random.randint(5,50), random.randint(5,50)).perform()
    time.sleep(random.uniform(0.5, 1.5))

# apply stealth settings
stealth(driver,
    languages = ["en-US", "en"], # pretned i speak english
    vendor = "Google Inc.", #pretend my browser vendor is Google 
    platform = "MacIntel", # pretend I'm using mac
    webgl_vendor = "Intel Inc.", # pretned my gpu is intel
    renderer = "Intel Iris OpenGL Engine", # pretend my graphics card is intel iris 
    fix_hairline = True,
)

# Zillow URL
#zillow_url = "https://www.zillow.com/los-angeles-ca-90024/rentals/"
zillow_url = "https://www.zillow.com/los-angeles-ca-90024/rentals/?searchQueryState=%7B%22pagination%22%3A%7B%7D%2C%22isMapVisible%22%3Atrue%2C%22mapBounds%22%3A%7B%22west%22%3A-118.47882370666503%2C%22east%22%3A-118.39488129333495%2C%22south%22%3A34.036443282160924%2C%22north%22%3A34.09496004342156%7D%2C%22regionSelection%22%3A%5B%7B%22regionId%22%3A96005%2C%22regionType%22%3A7%7D%5D%2C%22filterState%22%3A%7B%22sort%22%3A%7B%22value%22%3A%22priorityscore%22%7D%2C%22fr%22%3A%7B%22value%22%3Atrue%7D%2C%22fsba%22%3A%7B%22value%22%3Afalse%7D%2C%22fsbo%22%3A%7B%22value%22%3Afalse%7D%2C%22nc%22%3A%7B%22value%22%3Afalse%7D%2C%22cmsn%22%3A%7B%22value%22%3Afalse%7D%2C%22auc%22%3A%7B%22value%22%3Afalse%7D%2C%22fore%22%3A%7B%22value%22%3Afalse%7D%2C%22mf%22%3A%7B%22value%22%3Afalse%7D%2C%22land%22%3A%7B%22value%22%3Afalse%7D%2C%22manu%22%3A%7B%22value%22%3Afalse%7D%2C%22beds%22%3A%7B%22min%22%3A2%7D%2C%22baths%22%3A%7B%22min%22%3A2%7D%7D%2C%22isListVisible%22%3Atrue%2C%22mapZoom%22%3A14%2C%22usersSearchTerm%22%3A%22Los%20Angeles%20CA%2090024%22%7D"
driver.get(zillow_url)
time.sleep(5)  # Allow page to load

# Function to Scroll Thoroughly Until All Listings Appear
def scroll_until_no_new_listings(driver, max_attempts=15):
    last_height = driver.execute_script("return document.body.scrollHeight")
    
    for _ in range(max_attempts):
        driver.find_element(By.TAG_NAME, "body").send_keys(Keys.END)  # Scroll down
        time.sleep(random.uniform(3, 7))  # Wait for new listings to load

        new_height = driver.execute_script("return document.body.scrollHeight")
        
        if new_height == last_height:
            print("✅ No more new listings loaded on this page.")
            break  # Stop scrolling if the page height doesn’t change
        
        last_height = new_height
        simulate_human_movement(driver)


# Function to Click Next Page Button
def click_next_page():
    try:
        next_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, '//a[contains(@title, "Next page")]'))
        )
        next_button.click()
        time.sleep(random.uniform(5, 10))  # Wait for next page to load
        simulate_human_movement(driver)

        return True
        
    except:
        print("🚫 No more pages available.")
        return False

#random click
# driver.find_element(By.TAG_NAME, "body").click()
# time.sleep(random.uniform(1, 2))

# Data Collection
property_data = []

while True:
    scroll_until_no_new_listings(driver)  # Scroll until no more new listings appear
    properties = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.XPATH, '//article[@data-test="property-card"]'))
    )

    for property in properties:
        try:
            price = property.find_element(By.XPATH, './/span[@data-test="property-card-price"]').text
            address = property.find_element(By.XPATH, './/address[@data-test="property-card-addr"]').text
            details_elements = property.find_elements(By.XPATH, ".//ul[contains(@class, 'StyledPropertyCardHomeDetailsList')]/li")
            details = " | ".join([item.text for item in details_elements]) if details_elements else "N/A"

            property_data.append({"Price": price, "Address": address, "Details": details})
        except Exception as e:
            print(f"Error extracting data: {e}")

    if not click_next_page():
        break  # Exit loop if no more pages

# Save to CSV
if property_data:
    df = pd.DataFrame(property_data)
    df.to_csv("zillow_properties_1.csv", index=False)
    print("✅ Data saved to 'zillow_properties.csv'")
else:
    print("🚫 No property data scraped.")

# Close Browser
driver.quit()
