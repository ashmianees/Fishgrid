import time
from datetime import datetime
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

def log_message(message, file):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}"
    print(log_entry)
    file.write(log_entry + "\n")

class TestImageDetections:
    def setup_method(self, method):
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service)
        self.driver.maximize_window()

    def teardown_method(self, method):
        self.driver.quit()

    def test_imagedetections(self):
        log_file_path = "selenium_imagedetections_test_results.txt"
        with open(log_file_path, "w") as log_file:
            try:
                log_message("Starting the Selenium test for Image Detections...", log_file)
                self.driver.get("http://127.0.0.1:8000/")
                log_message("Navigated to the homepage.", log_file)

                WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.LINK_TEXT, "Login"))).click()
                log_message("Clicked on Login link.", log_file)
                
                self.driver.find_element(By.ID, "email").send_keys("ashmianees12@gmail.com")
                self.driver.find_element(By.ID, "password").send_keys("Ashmi@123")
                log_message("Entered login credentials.", log_file)
                
                self.driver.find_element(By.CSS_SELECTOR, ".btn").click()
                log_message("Clicked login button.", log_file)
                
                WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".user-name"))).click()
                WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#diseaseDetection span"))).click()
                log_message("Navigated to Disease Detection page.", log_file)
                
                image_path = "C:/path/to/your/image.jpg"  # Replace with actual image path
                self.driver.find_element(By.ID, "imageInput").send_keys(image_path)
                log_message("Uploaded image for detection.", log_file)
                
                WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.ID, "detectButton"))).click()
                log_message("Clicked detect button.", log_file)
                
                WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#logout-link > span"))).click()
                log_message("Logged out.", log_file)
                
            except Exception as e:
                log_message(f"An error occurred: {e}", log_file)
            
            finally:
                time.sleep(3)
                self.driver.quit()
                log_message("Browser closed. Test completed.", log_file)

print("Test completed. Results have been written to selenium_imagedetections_test_results.txt")
