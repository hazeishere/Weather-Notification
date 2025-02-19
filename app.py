import os
import schedule
import time
from pushbullet import Pushbullet
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import g4f

def generate_sentence():
    prompt = "Give me a sentence of life ONLY"
    response = g4f.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    return response

def send_weather_notification():
    load_dotenv()

    # Initialize Pushbullet
    pb = Pushbullet(os.getenv('PUSHBULLET_API_KEY'))

    # Setup Chrome options
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # Run in headless mode
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')

    # Initialize the driver
    driver = webdriver.Chrome(options=chrome_options)
    url = 'https://www.cwa.gov.tw/V8/C/W/County/County.html?CID=64'
    driver.get(url)

    # Wait for the content to load
    wait = WebDriverWait(driver, 10)
    parent = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "banner_wrap")))

    # Get the page source after JavaScript execution
    soup = BeautifulSoup(driver.page_source, 'html.parser')

    try:
        time_data = soup.find('th', {'scope': 'col', 'class': 'holiday'})

        morning_elem = soup.select_one("ul > li:nth-child(2) > span.tem > span.tem-C.is-active")
        morning = morning_elem.text if morning_elem else "N/A"
        
        night_elem = soup.select_one("ul > li:nth-child(3) > span.tem > span.tem-C.is-active")
        night = night_elem.text if night_elem else "N/A"
        
        rain_elem = soup.select_one("ul > li:nth-child(3) > span:nth-child(4)")
        rain = rain_elem.text.strip('%') if rain_elem else "N/A"
    except AttributeError as e:
        print(f"Error finding elements: {e}")
        driver.quit()
        exit(1)

    # Create and send the notification
    sentence = generate_sentence()
    push = pb.push_note(f"{time_data.text} 明日天氣預報", f"早上：{morning}°C\n晚上：{night}°C\n{rain}%\n{sentence}")
    print("Notification sent!")

    # Clean up
    driver.quit()

# Schedule the job to run at 23:50 every day
schedule.every().day.at("23:50").do(send_weather_notification)

# Keep the script running
while True:
    schedule.run_pending()
    time.sleep(1)
