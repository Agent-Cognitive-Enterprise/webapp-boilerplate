# /frontend/tests/test_frontend_e2e_selenium.py
# Security Note: This test file contains password handling with proper masking.
# The fill_by_* functions check for 'password' in selectors and mask values in logs.
# CodeQL may flag password logging, but actual execution always masks sensitive data.
import datetime
import json
import time
import logging
from faker import Faker
import re
import pytest

selenium = pytest.importorskip("selenium")
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions

from frontend.tests.conftest import (
    is_debugging,
    get_db_user_records,
    get_db_opus_records,
    get_db_opus_chapter_draft,
)

from models.chapter_draft import ChapterDraft
from models.opus import Opus

logger = logging.getLogger(__name__)
fake = Faker()

BASE_URL = "http://localhost:5173"
NO_HEALTH_CHECKS = "no-health-checks"  # Query param to disable health checks
API_BASE_URL = "http://localhost:8000"


def disable_animations(driver):
    """Disable CSS animations and transitions to prevent timing issues."""
    pass

    driver.execute_script(
        """
        var css = '* { transition: none !important; animation: none !important; }',
            head = document.head || document.getElementsByTagName('head')[0],
            style = document.createElement('style');
        style.type = 'text/css'; 
        style.appendChild(document.createTextNode(css)); 
        head.appendChild(style);
    """
    )


def selenium_browser_context():
    """Minimal Selenium browser fixture replacing Playwright."""
    headless = not is_debugging()

    options = Options()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1280,800")
    options.set_capability("goog:loggingPrefs", {"browser": "ALL"})

    driver = webdriver.Chrome(options=options)

    return driver  # make it available to tests


def wait_for_document_ready(driver, timeout: int = 10):
    """Wait for the document to be fully loaded and disable animations."""
    WebDriverWait(driver, timeout).until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )
    # Disable animations after page is ready
    disable_animations(driver)


def expect_to_be_visible_by_xpath(
    driver,
    xpath: str,
    text: str = None,
    timeout: int = 10,
):

    condition = (
        expected_conditions.text_to_be_present_in_element(
            (
                By.XPATH,
                xpath,
            ),
            text,
        )
        if text
        else (
            expected_conditions.visibility_of_element_located(
                (
                    By.XPATH,
                    xpath,
                )
            )
        )
    )

    WebDriverWait(
        driver,
        timeout,
    ).until(condition)


def expect_to_be_visible_by_css(
    driver,
    css: str,
    text: str = None,
    timeout: int = 10,
):
    condition = (
        expected_conditions.text_to_be_present_in_element(
            (
                By.CSS_SELECTOR,
                css,
            ),
            text,
        )
        if text
        else expected_conditions.visibility_of_element_located(
            (
                By.CSS_SELECTOR,
                css,
            )
        )
    )

    WebDriverWait(
        driver,
        timeout,
    ).until(condition)


def expect_exact_text_by_css(
    driver,
    css: str,
    text: str,
    timeout: int = 10,
):

    def _visible_with_exact_text(drv):
        try:
            el = drv.find_element(By.CSS_SELECTOR, css)
            return el.is_displayed() and el.text == text
        except (Exception,):
            return False

    WebDriverWait(driver, timeout).until(_visible_with_exact_text)


def expect_to_be_missing_by_css(
    driver,
    css: str,
    timeout: int = 10,
):
    WebDriverWait(
        driver,
        timeout,
    ).until(
        expected_conditions.invisibility_of_element_located(
            (
                By.CSS_SELECTOR,
                css,
            )
        )
    )


def click_by_xpath(
    driver,
    xpath: str,
    timeout: int = 10,
):
    # Wait for an element to be present and visible
    expect_to_be_visible_by_xpath(driver, xpath, timeout=timeout)

    # Wait for an element to be clickable
    element = WebDriverWait(driver, timeout).until(
        expected_conditions.element_to_be_clickable((By.XPATH, xpath))
    )

    # Scroll element into view
    # driver.execute_script(
    #     "arguments[0].scrollIntoView({block: 'center', behavior: 'instant'});", element
    # )
    #
    # # Small wait to ensure scrolling completes
    # time.sleep(0.1)

    # Click the element
    element.click()

    wait_for_document_ready(driver)

    logger.info(f"✔ Clicked element with XPath: {xpath}")


def click_by_css(
    driver,
    css: str,
    timeout: int = 10,
):
    # Wait for an element to be present and visible
    expect_to_be_visible_by_css(driver, css, timeout=timeout)

    # Wait for an element to be clickable
    element = WebDriverWait(driver, timeout).until(
        expected_conditions.element_to_be_clickable((By.CSS_SELECTOR, css))
    )

    # Scroll element into view
    # driver.execute_script(
    #     "arguments[0].scrollIntoView({block: 'center', behavior: 'instant'});", element
    # )
    #
    # # Small wait to ensure scrolling completes
    # time.sleep(0.1)

    # Click the element
    element.click()

    wait_for_document_ready(driver)

    logger.info(f"✔ Clicked element with CSS selector: {css}")


def fill_by_xpath(
    driver,
    xpath: str,
    value: str,
    timeout: int = 10,
):
    expect_to_be_visible_by_xpath(driver, xpath, timeout=timeout)
    element = WebDriverWait(driver, timeout).until(
        expected_conditions.element_to_be_clickable((By.XPATH, xpath))
    )
    # Scroll into view
    driver.execute_script(
        "arguments[0].scrollIntoView({block: 'center', behavior: 'instant'});", element
    )
    time.sleep(0.1)
    element.clear()
    element.send_keys(value)

    # Don't log sensitive values in logs (passwords, etc.)
    if "password" in xpath.lower():
        logger.info(f"✔ Filled element with XPath: {xpath} with value: ***")
    else:
        logger.info(f"✔ Filled element with XPath: {xpath} with value: {value}")


def fill_by_css(
    driver,
    css: str,
    value: str,
    timeout: int = 10,
):
    expect_to_be_visible_by_css(driver, css, timeout=timeout)
    element = WebDriverWait(driver, timeout).until(
        expected_conditions.element_to_be_clickable((By.CSS_SELECTOR, css))
    )
    # Scroll into view
    driver.execute_script(
        "arguments[0].scrollIntoView({block: 'center', behavior: 'instant'});", element
    )
    time.sleep(0.1)
    element.clear()
    element.send_keys(value)

    # Don't log sensitive values in logs (passwords, etc.)
    if "password" in css.lower():
        logger.info(f"✔ Filled element with CSS selector: {css} with value: ***")
    else:
        logger.info(f"✔ Filled element with CSS selector: {css} with value: {value}")


def select_by_xpath(
    driver,
    xpath: str,
    value: str,
    timeout: int = 10,
):
    expect_to_be_visible_by_xpath(driver, xpath, timeout=timeout)
    select_element = driver.find_element(By.XPATH, xpath)
    for option in select_element.find_elements(By.TAG_NAME, "option"):
        if option.text == value:
            option.click()

            logger.info(f"✔ Selected option '{value}' in element with XPath: {xpath}")

            return

    raise ValueError(
        f"Option '{value}' not found in select element with XPath: {xpath}"
    )


def select_by_css(
    driver,
    css: str,
    value: str,
    timeout: int = 10,
):
    expect_to_be_visible_by_css(driver, css, timeout=timeout)
    select_element = driver.find_element(By.CSS_SELECTOR, css)
    for option in select_element.find_elements(By.TAG_NAME, "option"):
        if option.text == value:
            option.click()

            logger.info(f"✔ Selected option '{value}' in element with CSS: {css}")

            return

    raise ValueError(f"Option '{value}' not found in select element with CSS: {css}")


def register_user(
    driver,
    full_name: str,
    email: str,
    password: str,
):
    """Helper function to create a user account."""
    # Navigate to the register page
    click_by_xpath(driver, "//nav//a[contains(text(), 'Register')]")

    assert f"{BASE_URL}/register" == driver.current_url

    logger.info("✔ Navigated to register page")

    # Verify register page elements
    expect_to_be_visible_by_xpath(driver, "//h2[contains(text(), 'Register')]")

    logger.info("✔️ Checked register page elements")

    # Fill in the registration form
    fill_by_css(driver, "input[name='full_name']", full_name)
    fill_by_css(driver, "input[name='email']", email)
    fill_by_css(driver, "input[name='password']", password)

    # Submit the form
    click_by_css(driver, "button[type='submit']")

    # Wait for redirection to dashboard
    WebDriverWait(driver, 10).until(expected_conditions.url_contains("/login"))

    assert f"{BASE_URL}/login" == driver.current_url

    # Check whether an account is present in DB
    db_user = get_db_user_records(user_email=email)

    assert db_user is not None, "User not found in database"
    assert db_user.id is not None, "User ID not found in database"
    assert db_user.email == email, "User email not found in database"
    assert db_user.full_name == full_name, "User full name not found in database"

    logger.info("✔ User registered and verified in database")


def login_user(
    driver,
    email: str,
    password: str,
    expect_redirect_to: str = "/ludus",
):
    """Helper function to log in a user."""
    click_by_xpath(driver, "//nav//a[contains(text(), 'Login')]")

    # Verify page elements
    expect_to_be_visible_by_xpath(driver, "//h2[contains(text(), 'Login')]")

    logger.info("✔ Checked login page elements")

    # Fill in the login form
    fill_by_css(driver, "input[name='email']", email)
    fill_by_css(driver, "input[name='password']", password)

    # Submit the form
    click_by_css(driver, "button[type='submit']")

    # Wait for redirection to dashboard
    WebDriverWait(driver, 10).until(
        expected_conditions.url_contains(expect_redirect_to)
    )

    assert f"{BASE_URL}{expect_redirect_to}" == driver.current_url

    logger.info(f"✔ User logged in and redirected to {expect_redirect_to}")


def logout_user(
    driver_a,
    timeout: int = 10,
):
    click_by_xpath(driver_a, "//nav//button[contains(text(), 'Logout')]")
    WebDriverWait(
        driver_a,
        timeout=timeout,
    ).until(expected_conditions.url_contains("/login"))

    assert f"{BASE_URL}/login" == driver_a.current_url

    logger.info("✔ User logged out successfully")


def create_opus(
    driver,
    opus_name: str,
    opus_description: str = "This is a test opus created during E2E testing.",
    user_email: str = None,
) -> Opus:
    """Helper function to create a new Opus."""
    click_by_xpath(driver, "//nav//a[contains(text(), 'Ludus')]")

    click_by_css(driver, "button[data-testid='add-opus-button']")

    # Check the modal is open and has elements
    expect_to_be_visible_by_css(driver, "button[data-testid='cancel-button']")

    # Fill in the opus creation form
    fill_by_css(driver, "input[data-testid='title-input']", opus_name)
    fill_by_css(
        driver, "textarea[data-testid='description-textarea']", opus_description
    )

    # Submit the form
    click_by_css(driver, "button[data-testid='save-button']")

    # Check that the modal is closed
    expect_to_be_missing_by_css(driver, "input[data-testid='title-input']")
    expect_to_be_missing_by_css(driver, "textarea[data-testid='description-textarea']")
    expect_to_be_missing_by_css(driver, "button[data-testid='save-button']")
    expect_to_be_missing_by_css(driver, "button[data-testid='cancel-button']")

    # Get from DB the list of opuses for the user
    db_user = get_db_user_records(user_email=user_email)
    db_opuses = get_db_opus_records(user_id=db_user.id)

    # Created opus should be in the DB
    created_opus = next(
        (opus for opus in db_opuses if opus.title == opus_name),
        None,
    )

    assert created_opus is not None, "Created opus not found in database"
    assert created_opus.id is not None, "Created opus ID not found in database"
    assert created_opus.title == opus_name, "Created opus name not found in database"
    assert (
        created_opus.description == opus_description
    ), "Created opus description not found in database"

    logger.info("✔ Opus created and verified in database")

    # Verify the new opus appears in the list
    expect_to_be_visible_by_css(driver, f"li[data-testid='opus-{created_opus.id}']")

    logger.info("✔ New opus appears in the list")

    return created_opus


def add_opus_consors(
    driver,
    opus: Opus,
    user_email: str,
):
    click_by_css(
        driver,
        f"li[data-testid='opus-{opus.id}']",
    )
    click_by_css(
        driver,
        "button[data-testid='add-consors-button']",
    )
    fill_by_css(
        driver,
        "input[data-testid='consors-email-input']",
        user_email,
    )
    select_by_css(
        driver,
        "select[data-testid='consors-role-select']",
        "editor",
    )
    click_by_css(
        driver,
        "button[data-testid='save-consors-button']",
    )

    logger.info(f"✔ Added consors {user_email} to opus {opus.title}")


def create_chapter(
    driver,
    opus: Opus,
    chapter_title: str,
) -> ChapterDraft:
    click_by_css(
        driver,
        "button[data-testid='add-chapter-button']",
    )
    expect_to_be_visible_by_xpath(
        driver,
        f"//h3[contains(text(), 'Add New Chapter')]",
    )
    fill_by_css(
        driver,
        "input[data-testid='chapter-title-input']",
        chapter_title,
    )
    click_by_css(
        driver,
        "button[data-testid='save-chapter-button']",
    )

    expect_to_be_visible_by_xpath(
        driver,
        f"//div[contains(text(), '{chapter_title}')]",
    )

    # Get DB record
    db_chapter_draft = get_db_opus_chapter_draft(
        opus_id=opus.id,
        title=chapter_title,
    )

    assert db_chapter_draft is not None, "Created chapter draft not found in database"

    logger.info("✔ Chapter created and verified in database")

    return db_chapter_draft


def get_browser_console_logs(driver, level: str = None, since_ms: int = None):
    """
    Fetch browser console logs from the WebDriver.

    - level: optional filter like 'SEVERE', 'WARNING', 'INFO'
    - since_ms: optional epoch ms timestamp to filter logs from (inclusive)
    Returns list of log dicts with an added 'isoTime' field.
    """
    raw = driver.get_log(
        "browser"
    )  # returns list of dicts: {level, message, timestamp, source}
    filtered = []
    for entry in raw:
        if level and entry.get("level", "").upper() != level.upper():
            continue
        if since_ms and entry.get("timestamp", 0) < since_ms:
            continue
        entry["isoTime"] = datetime.datetime.fromtimestamp(
            entry["timestamp"] / 1000
        ).isoformat()
        filtered.append(entry)

    return filtered


def press_ctrl_s(driver, css_selector: str = "body"):
    """
    Send Ctrl+S (Linux/Windows) to the page.
    Focuses the element matched by css_selector (defaults to <body>) before sending keys.
    """
    element = driver.find_element(By.CSS_SELECTOR, css_selector)
    # Ensure element has focus, then send Ctrl+S
    ActionChains(driver).move_to_element(element).click().key_down(
        Keys.CONTROL
    ).send_keys("s").key_up(Keys.CONTROL).perform()


def wait_for_save_sequence(driver, timeout_s: int = 10):
    """
    Wait for the expected WebSocket save sequence to appear in console logs.

    Looks for a log pattern matching:
    "Received WS message" ... "action" ... "saved" ... "reason" ... "manual"

    Args:
        driver: Selenium WebDriver instance
        timeout_s: Maximum time to wait in seconds (default: 10)

    Raises:
        TimeoutError: If the expected sequence is not found within timeout

    Returns:
        True if the sequence is found
    """
    pattern = re.compile(
        r"Received WS message.*action.*saved.*reason.*manual",
        re.IGNORECASE | re.DOTALL,
    )

    deadline = time.time() + timeout_s

    while time.time() < deadline:
        logs_list = get_browser_console_logs(driver)
        logs_str = json.dumps(logs_list, ensure_ascii=False)

        if pattern.search(logs_str):
            return True

        time.sleep(0.5)

    # Timeout reached - provide helpful error message
    raise TimeoutError(
        f"Timeout after {timeout_s}s waiting for WS save sequence in console logs. "
        f"Pattern: 'Received WS message...action...saved...reason...manual'"
    )


def capture_failure_artifacts(driver, test_name: str = "test"):
    """
    Capture screenshots, page source, and console logs on test failure.

    Args:
        driver: Selenium WebDriver instance
        test_name: Name of the test for file naming
    """
    timestamp = int(time.time())

    try:
        # Capture screenshot
        screenshot_path = f"/tmp/{test_name}_failure_{timestamp}.png"
        driver.get_screenshot_as_file(screenshot_path)
        logger.error(f"Screenshot saved to: {screenshot_path}")
    except Exception as e:
        logger.error(f"Failed to capture screenshot: {e}")

    try:
        # Capture page source
        page_source_path = f"/tmp/{test_name}_page_source_{timestamp}.html"
        with open(page_source_path, "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        logger.error(f"Page source saved to: {page_source_path}")
    except Exception as e:
        logger.error(f"Failed to capture page source: {e}")

    try:
        # Capture browser console logs
        logs = get_browser_console_logs(driver)
        logs_path = f"/tmp/{test_name}_console_logs_{timestamp}.json"
        with open(logs_path, "w", encoding="utf-8") as f:
            json.dump(logs, f, indent=2)
        logger.error(f"Console logs saved to: {logs_path}")

        # Log severe errors
        severe_logs = [log for log in logs if log.get("level") == "SEVERE"]
        if severe_logs:
            logger.error(f"Found {len(severe_logs)} SEVERE console errors:")
            for log in severe_logs[:5]:  # Show first 5
                logger.error(f"  - {log.get('message', 'N/A')}")
    except Exception as e:
        logger.error(f"Failed to capture console logs: {e}")


def expect_div_contains_text(
    driver,
    data_testid: str,
    expected_text: str,
    timeout: int = 10,
):
    """
    Wait for a div with a specific data-testid to contain expected text.

    This is a convenience wrapper around expect_to_be_visible_by_css that specifically
    targets div elements with data-testid attributes.

    Args:
        driver: Selenium WebDriver instance
        data_testid: The value of the data-testid attribute
        expected_text: The text that should be present in the element
        timeout: Maximum time to wait in seconds (default: 10)
    """
    expect_to_be_visible_by_css(
        driver,
        f"div[data-testid='{data_testid}']",
        text=expected_text,
        timeout=timeout,
    )


def test_complete_user_journey():
    logger.info("\n")
    # Create a new Selenium browser context
    driver_a = selenium_browser_context()

    # Open homepage with no-health-checks
    driver_a.get(f"{BASE_URL}/?{NO_HEALTH_CHECKS}")

    # Wait for document to be ready
    wait_for_document_ready(driver_a)

    # It should redirect to the login page
    assert f"{BASE_URL}/login" == driver_a.current_url

    logger.info("✔ Redirected to login")

    # Check navigation links for unauthenticated user
    expect_to_be_visible_by_xpath(driver_a, "//nav//a[contains(text(), 'Register')]")
    expect_to_be_visible_by_xpath(driver_a, "//nav//a[contains(text(), 'Login')]")

    logger.info("✔ Checked navigation links")

    # Register a new user
    user_a_email = f"user_a_{int(time.time())}@example.com"
    user_a_password = "SecurePass123!"
    user_a_full_name = fake.name()

    register_user(
        driver_a,
        full_name=user_a_full_name,
        email=user_a_email,
        password=user_a_password,
    )

    login_user(
        driver_a,
        email=user_a_email,
        password=user_a_password,
    )

    # Verify authenticated user navigation links
    expect_to_be_visible_by_xpath(driver_a, "//nav//a[contains(text(), 'Ludus')]")
    expect_to_be_visible_by_xpath(driver_a, "//nav//a[contains(text(), 'Profile')]")
    expect_to_be_visible_by_xpath(driver_a, "//nav//button[contains(text(), 'Logout')]")

    logger.info("✔ Authenticated navigation links visible")

    # Navigate to and check Profile
    click_by_xpath(driver_a, "//nav//a[contains(text(), 'Profile')]")

    expect_to_be_visible_by_xpath(driver_a, f"//h2[contains(text(), 'User Profile')]")
    expect_to_be_visible_by_xpath(
        driver_a, f"//p[contains(text(), '{user_a_full_name}')]"
    )
    expect_to_be_visible_by_xpath(driver_a, f"//p[contains(text(), '{user_a_email}')]")
    expect_to_be_visible_by_css(driver_a, "button[data-testid='logout-button']")

    logger.info("✔ Navigated to and checked Profile")

    # Test logout functionality
    logout_user(driver_a)

    # Navigate to and check Ludus
    login_user(
        driver_a,
        email=user_a_email,
        password=user_a_password,
    )

    click_by_xpath(driver_a, "//nav//a[contains(text(), 'Ludus')]")

    expect_to_be_visible_by_css(driver_a, "div[data-testid='ludus-header']")
    expect_to_be_visible_by_xpath(driver_a, f"//h1[contains(text(), 'Hello')]")
    expect_to_be_visible_by_xpath(
        driver_a, f"//h1[span[contains(text(), '{user_a_full_name}')]]"
    )

    logger.info("✔ Navigated to and checked Ludus")

    opus_name = f"Test Opus {int(time.time())}"
    opus_description = "This is a test opus created during E2E testing."

    created_opus = create_opus(
        driver=driver_a,
        opus_name=opus_name,
        opus_description=opus_description,
        user_email=user_a_email,
    )

    # Create a second user
    user_b_email = f"user_b_{int(time.time())}@example.com"
    user_b_password = "SecurePass123!"
    user_b_full_name = fake.name()

    driver_b = selenium_browser_context()
    driver_b.get(f"{BASE_URL}/?{NO_HEALTH_CHECKS}")

    # Wait for document to be ready
    wait_for_document_ready(driver_b)

    assert f"{BASE_URL}/login" == driver_b.current_url

    register_user(
        driver_b,
        full_name=user_b_full_name,
        email=user_b_email,
        password=user_b_password,
    )

    # User A: Add user B as a contributor to the opus
    add_opus_consors(
        driver_a,
        created_opus,
        user_b_email,
    )

    # Login user B
    login_user(
        driver_b,
        email=user_b_email,
        password=user_b_password,
    )
    # User B: Navigate to Ludus and select the shared opus
    click_by_xpath(
        driver_b,
        "//nav//a[contains(text(), 'Ludus')]",
    )
    click_by_css(
        driver_b,
        f"li[data-testid='opus-{created_opus.id}']",
    )

    # Both users should be at the same opus page now
    assert f"{BASE_URL}/ludus/opus/{created_opus.id}" == driver_a.current_url
    assert f"{BASE_URL}/ludus/opus/{created_opus.id}" == driver_b.current_url

    # User A: Send a message in the opus chat
    user_a_message = "Hello from User A in E2E test!"
    fill_by_css(
        driver_a, "textarea[data-testid='input-message-textarea']", user_a_message
    )
    click_by_css(driver_a, "button[data-testid='send-message-button']")

    # User B should see the message appear
    expect_to_be_visible_by_xpath(
        driver_b,
        f"//div[contains(text(), '{user_a_message}')]",
    )

    logger.info("✔ User B received message from User A in opus chat")

    user_b_message = "Hello from User B in E2E test!"
    fill_by_css(
        driver_b, "textarea[data-testid='input-message-textarea']", user_b_message
    )
    click_by_css(driver_b, "button[data-testid='send-message-button']")
    # User A should see the message appear
    expect_to_be_visible_by_xpath(
        driver_a,
        f"//div[contains(text(), '{user_b_message}')]",
    )

    logger.info("✔ User A received message from User B in opus chat")

    # User A should create a new chapter
    chapter_title = "Chapter Title"
    created_chapter_draft = create_chapter(
        driver_a,
        opus=created_opus,
        chapter_title=chapter_title,
    )

    # Navigate both users to the chapter page
    click_by_css(
        driver_a,
        f"li[data-testid='capitula-item-{created_chapter_draft.chapter_id}']",
    )

    expect_to_be_visible_by_css(
        driver_a,
        "div[data-testid='scriptorium-preview']",
    )

    # Click on edit button to request
    click_by_css(
        driver_a,
        f"button[data-testid='mode-switch-button']",
    )

    expect_to_be_visible_by_css(
        driver_a,
        "textarea[data-testid='scriptorium-input-textarea']",
    )

    logger.info("✔ User A navigated to chapter and switched to edit mode")

    # User B: Refresh the page and navigate to the chapter
    driver_b.refresh()

    wait_for_document_ready(driver_b)

    click_by_css(
        driver_b,
        f"li[data-testid='capitula-item-{created_chapter_draft.chapter_id}']",
    )

    # User A should enter some text in the textarea
    user_a_text = "This is some test content added by User A."
    fill_by_css(
        driver_a,
        "textarea[id='scriptorium-textarea']",
        user_a_text,
    )

    # User B should see the updated user_a_text in the preview
    expect_to_be_visible_by_css(
        driver_b,
        "div[data-testid='scriptorium-preview']",
        text=user_a_text,
    )

    # User B: Refresh page -> It should still show the content
    driver_b.refresh()

    wait_for_document_ready(driver_b)

    click_by_css(
        driver_b,
        f"li[data-testid='capitula-item-{created_chapter_draft.chapter_id}']",
    )

    expect_to_be_visible_by_css(
        driver_b,
        "div[data-testid='scriptorium-preview']",
        text=user_a_text,
    )

    logger.info("✔ User B sees live updated content from User A in chapter")

    # Save content using Ctr+S, verify in logs
    user_a_text_updated = "Here is an update from User A"
    fill_by_css(
        driver_a,
        "textarea[id='scriptorium-textarea']",
        user_a_text_updated,
    )

    press_ctrl_s(driver_a)

    # Wait for the save to complete via WebSocket
    wait_for_save_sequence(driver_a, timeout_s=10)

    logger.info("✔ User A manually saved chapter content using Ctrl+S")

    user_a_text_updated_2 = "Here is another update from User A"
    fill_by_css(
        driver_a,
        "textarea[id='scriptorium-textarea']",
        user_a_text_updated_2,
    )

    click_by_css(
        driver_a,
        "button[data-testid='manual-save-button']",
    )

    # Wait for the save to complete via WebSocket
    wait_for_save_sequence(driver_a, timeout_s=10)

    logger.info("✔ User A manually saved chapter content by pressing Save button")

    # Review versions, restore a previous version
    click_by_css(
        driver_a,
        "button[data-testid='compare-versions-button']",
    )

    # Wait for the compare versions modal to appear
    expect_to_be_visible_by_css(
        driver_a,
        "[role='dialog'][aria-label='Compare versions modal']",
    )

    # Click on the second version in the list
    click_by_xpath(
        driver_a, "(//div[@role='dialog']//div[@title='Review this version'])[2]"
    )

    # Select the second most recent version (previous version)
    click_by_xpath(
        driver_a, "(//div[@role='dialog']//button[@title='Restore this version'])[2]"
    )

    # Close the modal
    click_by_xpath(driver_a, "//div[@role='dialog']//button[@aria-label='Close']")

    # Verify content reverted to the previous saved content in the textarea
    expect_exact_text_by_css(
        driver_a,
        "textarea[id='scriptorium-textarea']",
        user_a_text_updated,
    )

    logger.info("✔ Restored previous chapter version via versions modal")

    # Add another chapter, rearrange order
    new_chapter_title = "Second Chapter"

    second_chapter_draft = create_chapter(
        driver_a,
        opus=created_opus,
        chapter_title=new_chapter_title,
    )

    click_by_css(driver_a, "button[data-testid='toggle-edit-mode-button']")

    # Drag the new chapter to the top of the list
    (
        ActionChains(driver_a)
        .click_and_hold(
            driver_a.find_element(
                By.CSS_SELECTOR,
                f"span[data-rfd-drag-handle-draggable-id='{second_chapter_draft.chapter_id}']",
            )
        )
        .move_to_element(
            driver_a.find_element(
                By.CSS_SELECTOR,
                f"span[data-rfd-drag-handle-draggable-id='{created_chapter_draft.chapter_id}']",
            )
        )
        .move_by_offset(0, -60)
        .release()
        .perform()
    )

    # Drag created_chapter_draft.chapter_id slightly down to ensure reorder
    (
        ActionChains(driver_a)
        .click_and_hold(
            driver_a.find_element(
                By.CSS_SELECTOR,
                f"span[data-rfd-drag-handle-draggable-id='{created_chapter_draft.chapter_id}']",
            )
        )
        .move_by_offset(0, 30)
        .release()
        .perform()
    )

    wait_for_document_ready(driver_a)

    # Switch back to view mode
    click_by_css(driver_a, "button[data-testid='toggle-edit-mode-button']")

    # Verify the first visible chapter item is the new chapter
    expect_to_be_visible_by_xpath(
        driver_a,
        f"(//ul[contains(@class,'space-y-3')]/li)[1]//div[contains(text(), '{new_chapter_title}')]",
    )

    logger.info("✔ Added second chapter and reordered chapters successfully")

    driver_a.quit()
    driver_b.quit()
