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
with open("selenium_wishlist_test_results.txt", "w") as log_file:
    try:
        log_message("Starting the wishlist test...", log_file)

        driver.maximize_window()
        log_message("Browser window maximized.", log_file)

        # Navigate to the login page
        driver.get("http://127.0.0.1:8000/login/")  # Update this URL if needed
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
        log_message("Entered password.", log_file)

        # Find and click the login button
        login_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Login')]")
        login_button.click()
        log_message("Clicked the login button.", log_file)

        # Wait for the page to load after login
        WebDriverWait(driver, 10).until(EC.url_changes("http://127.0.0.1:8000/login/"))
        time.sleep(2)  # Optional delay to ensure the page has fully loaded

        current_url = driver.current_url
        log_message(f"Current URL after login: {current_url}", log_file)

        # Check if login was successful
        if "user/indexfish" in current_url:  # Change this to your actual successful URL
            log_message("Login successful!", log_file)
        else:
            log_message("Login failed or redirected to an unexpected page.", log_file)

        # Optional: Check for error messages
        try:
            error_message = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".error-message"))  # Adjust the selector
            )
            log_message(f"Error message displayed: {error_message.text}", log_file)
        except Exception:
            log_message("No error message displayed after login attempt.", log_file)

        # Proceed with the wishlist test if logged in successfully
        if "user/indexfish" in current_url:
            # Navigate to product details
            view_more_link = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.LINK_TEXT, "View More"))
            )
            view_more_link.click()
            log_message("Clicked on 'View More'.", log_file)

            view_details_link = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.LINK_TEXT, "View Details"))
            )
            view_details_link.click()
            log_message("Clicked on 'View Details'.", log_file)

            # Add to wishlist
            wishlist_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "wishlistBtn"))
            )
            wishlist_button.click()
            log_message("Clicked 'Add to Wishlist' button.", log_file)

            # Click again to remove from wishlist if needed (optional)
            wishlist_button.click()
            log_message("Clicked 'Add to Wishlist' button again (optional).", log_file)

    except Exception as e:
        log_message(f"An error occurred: {e}", log_file)

    finally:
        # Close the browser after a short delay
        time.sleep(3)  # Optional delay to observe the result
        driver.quit()
        log_message("Browser closed. Test completed.", log_file)

print("Test completed. Results have been written to selenium_wishlist_test_results.txt.")
