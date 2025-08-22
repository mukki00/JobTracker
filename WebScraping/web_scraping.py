from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
import time
import constants.getConstants as const
import constants.getElementsProps as elem
import constants.getScripts as scripts
def load_options_arguments(option: Options):
    option.add_argument(r"user-data-dir="+const.CHROME_EXE_PATH)
    option.add_argument(r"profile-directory="+const.PROFILE)
    # opts.add_argument("--headless=new")  # remove if you want to see the browser
    option.add_argument("--disable-gpu")
    option.add_argument("--no-first-run")
    option.add_argument("--no-default-browser-check")

def get_ul(wait: WebDriverWait ) -> webdriver.remote.webelement.WebElement:
    # UL right after the sentinel (works across class changes)
    return wait.until(EC.presence_of_element_located(
        (By.XPATH, elem.SCROLL_ITEMS)
    ))

def get_scrollable(driver, el):
    return driver.execute_script(scripts.SCROLL_BODY, el)

def extract_li(driver,li):
    # Force render: bring card into viewport
    try:
        driver.execute_script(scripts.SCROLL_INTO_VIEW, li)
    except StaleElementReferenceException:
        return None
    time.sleep(const.DATA_SCRAPING_TIME)

    # job id (on li or inner div)
    job_id = li.get_attribute(elem.JOB_ID)
    job_title = li.find_element(By.CLASS_NAME, elem.JOB_TITLE).text
    linkedin_verified = False
    if '\n' in job_title:
        if 'verification' in job_title.split('\n')[1].lower():
            linkedin_verified = True
        job_title = job_title.split('\n')[0]
    company = li.find_element(By.CLASS_NAME, elem.COMPANY).text
    company_location = li.find_element(By.CLASS_NAME, elem.COMPANY_LOCATION).text
    job_type = "Not Specified"
    if '(' and ')' in company_location:
        job_type = company_location.split('(')[1].split(')')[0]
        company_location = company_location.split('(')[0]
    job_link = li.find_element(By.TAG_NAME, "a").get_attribute("href")
    # filter ghost rows
    if not (job_id or job_title or company or job_link):
        return None
    return job_id, job_title, company, company_location, job_link, job_type, linkedin_verified

def direct_to_jobs_page(driver, URL):
    driver.get(URL)
    try:
        WebDriverWait(driver, const.JOB_PAGE_RENDERING_TIME).until(
            EC.presence_of_element_located((By.ID, elem.GLOBAL_NAVBAR))
        )
        WebDriverWait(driver, const.JOB_PAGE_ELEMENTS_RENDERING_TIME).until(EC.presence_of_element_located((By.ID, elem.GLOBAL_NAV_SEARCH)))
        print("Homepage loaded successfully.")
    except TimeoutException:
        print("Timeout: Unable to locate the global navigation search bar. Verifying page content...")
        print(driver.page_source)
    time.sleep(const.SLEEP_TIME_AFTER_DIRECT_TO_JOBS)

def extract_job_details(driver, lis, seen, ordered):
    for li in lis:
        try:
            data = extract_li(driver, li)
            if not data:
                continue
            job_id, job_title, company, company_location, job_link, job_type, linkedin_verified = data
            if job_id and job_id not in seen:
                seen.add(job_id)
                ordered.append((job_id, job_title, company, company_location, job_link, job_type, linkedin_verified))
                print(job_id, job_title, company, company_location, job_link, job_type, linkedin_verified)
        except StaleElementReferenceException:
            continue

def scrape_jobs(driver,seen,ordered,ul,wait, scrollable):
    stalls = 0
    last_visible_count = 0

    while True:
        # Re-anchor if the list re-rendered
        try:
            lis = ul.find_elements(By.CSS_SELECTOR, elem.ITEMS_IN_LIST)
            extract_job_details(driver, lis, seen, ordered)
        except StaleElementReferenceException:
            ul = get_ul(wait)
            scrollable = get_scrollable(driver, ul)
            continue

        # Extract from all currently visible lis (force-render per li)
        # Smooth incremental scroll (no PAGE_DOWN, no jump-to-end)
        try:
            driver.execute_script(scripts.SMOOTH_SCROLL,scrollable)
        except StaleElementReferenceException:
            ul = get_ul(wait)
            scrollable = get_scrollable(driver, ul)
            continue

        time.sleep(const.FETCHING_DATA_TIME)

        # Stall detection: compare visible li count (like-for-like)
        try:
            now_visible_count = len(ul.find_elements(By.CSS_SELECTOR, elem.VISIBLE_COUNT_IN_LIST))
            if now_visible_count <= last_visible_count:
                stalls += 1
            else:
                stalls = 0
                last_visible_count = now_visible_count
        except StaleElementReferenceException:
            ul = get_ul(wait)
            scrollable = get_scrollable(driver, ul)
            continue


        at_bottom = driver.execute_script(scripts.SCROLL_TO_BOTTOM,scrollable)
        if at_bottom and stalls >= const.ITEM_COUNTS_PER_SCROLL:
            break

def chrome_sign_in() -> Options:
    opts = Options()
    load_options_arguments(opts)
    return opts

def linkedin_data_scraper(opts: Options):
    driver = webdriver.Chrome(options=opts)
    URL = const.LINKEDIN_RECOMMENDED_JOB_URL
    direct_to_jobs_page(driver,URL)
    wait = WebDriverWait(driver, const.TIMEOUT_BEFORE_DATA_SCRAPING)
    # ---- MAIN SCROLL/COLLECT LOOP (replace your while True block) ----
    seen, ordered = set(), []
    ul = get_ul(wait)
    scrollable = get_scrollable(driver, ul)
    scrape_jobs(driver, seen, ordered, ul, wait, scrollable)
    time.sleep(const.TIMEOUT_AFTER_DATA_SCRAPING)
    driver.quit()
    print(f"Loaded {len(ordered)} jobs in order.")
