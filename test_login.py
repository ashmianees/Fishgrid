import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def log_message(message, file):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}"
    print(log_entry)
    file.write(log_entry + "\n")

# Set up the WebDriver using webdriver_manager
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service)

# Open the log file
with open("selenium_login_test_results.txt", "w") as log_file:
    try:
        log_message("Starting the Selenium test...", log_file)

        driver.maximize_window()
        log_message("Browser window maximized.", log_file)

        # Navigate to the login page
        driver.get("http://localhost:8000/login/")  # Replace with your actual login URL
        log_message("Navigated to the login page.", log_file)

        # Wait for the email input field to be visible
        email_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "email"))
        )
        log_message("Email input field is visible.", log_file)

        # Enter the email
        email_input.send_keys("meenuantony333@gmail.com")
        log_message("Entered email: meenuantony333@gmail.com", log_file)

        # Find the password input and enter the password
        password_input = driver.find_element(By.ID, "password")
        password_input.send_keys("Meenu@123")
        log_message("Entered password: ********", log_file)

        # Find and click the login button
        login_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Login')]")
        login_button.click()
        log_message("Clicked the login button.", log_file)

        # Wait for the page to load after login
        WebDriverWait(driver, 10).until(
            EC.url_changes("http://localhost:8000/login/")
        )
        log_message("Page URL changed after login attempt.", log_file)

        # Check if login was successful
        if "member_index" in driver.current_url:
            log_message("Login successful!", log_file)
        else:
            log_message("Login failed or unexpected redirect.", log_file)

        # Optional: Add more assertions or checks here

    except Exception as e:
        log_message(f"An error occurred: {e}", log_file)

    finally:
        # Close the browser
        time.sleep(3)  # Wait for 3 seconds to see the result
        driver.quit()
        log_message("Browser closed. Test completed.", log_file)

print("Test completed. Results have been written to selenium_test_results.txt")