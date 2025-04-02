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
with open("selenium_edit_product_test_results.txt", "w") as log_file:
    try:
        log_message("Starting the Selenium test for Edit Product...", log_file)

        driver.maximize_window()
        log_message("Browser window maximized.", log_file)

        # Navigate to the shop login page
        driver.get("http://127.0.0.1:8000/shop_login/")  # Replace with your actual login URL
        log_message("Navigated to shop login page.", log_file)

        # Wait for the email input field to be visible
        email_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "email"))
        )
        log_message("Email input field is visible.", log_file)

        # Enter the email
        email_input.send_keys("ashmianees12@gmail.com")
        log_message("Entered email: ashmianees12@gmail.com", log_file)

        # Find the password input and enter the password
        password_input = driver.find_element(By.ID, "password")
        password_input.send_keys("Ashmi@123")
        log_message("Entered password: ********", log_file)

        # Find and click the login button
        login_button = driver.find_element(By.CSS_SELECTOR, ".btn")
        login_button.click()
        log_message("Clicked the login button.", log_file)

        # Wait for the URL to change after login
        WebDriverWait(driver, 10).until(
            EC.url_changes("http://127.0.0.1:8000/shop_login/")
        )
        log_message("Login successful, URL changed.", log_file)

        # Navigate to the Product page
        driver.find_element(By.LINK_TEXT, "Product").click()
        log_message("Navigated to Product page.", log_file)

        # Wait for the edit button to be clickable and click it
        edit_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "tr:nth-child(1) .btn-primary"))
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", edit_button)
        edit_button.click()
        log_message("Clicked edit button for the first product.", log_file)

        # Wait for the add quantity input to be interactable
        add_quantity_input = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "edit_product_add_quantity"))
        )
        add_quantity_input.click()
        add_quantity_input.send_keys("2")
        log_message("Entered quantity: 2", log_file)

        # Click the save button in the modal
        save_button = driver.find_element(By.CSS_SELECTOR, ".modal-footer > .btn-primary")
        save_button.click()
        log_message("Clicked the save button.", log_file)

        # Optionally log any additional checks or assertions
        log_message("Edit Product test completed successfully.", log_file)

    except Exception as e:
        log_message(f"An error occurred: {e}", log_file)

    finally:
        # Close the browser
        time.sleep(3)  # Wait for 3 seconds to see the result
        driver.quit()
        log_message("Browser closed. Test completed.", log_file)

print("Test completed. Results have been written to selenium_edit_product_test_results.txt")
