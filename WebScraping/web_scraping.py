import logging
import re
from DB.db_connection import setup_db_connection
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
from DB.DB_Transactions import insert_job_posts
import time
import constants.getConstants as const
import constants.getElementsProps as elem
import constants.getScripts as scripts
import constants.getJobCategoryMap as job_category_map
from logger.logger_config import setup_logging

logger = setup_logging(__name__)

def load_options_arguments(option: Options):
    option.add_argument(r"user-data-dir="+const.CHROME_EXE_PATH)
    option.add_argument(r"profile-directory="+const.PROFILE)
    option.add_argument("--headless=new")  # remove if you want to see the browser
    option.add_argument("--disable-gpu")
    option.add_argument("--no-first-run")
    option.add_argument("--no-default-browser-check")
    option.add_argument("--remote-debugging-port=0")

def get_ul(wait: WebDriverWait, driver) -> webdriver.remote.webelement.WebElement:
    # UL right after the sentinel (works across class changes)
    try:
        wait = WebDriverWait(driver, const.TIMEOUT_BEFORE_SCROLL_ITEMS)
        return wait.until(EC.presence_of_element_located((By.XPATH, elem.SCROLL_ITEMS)))
    except TimeoutException:
        logger.info("No job list found on page (possible filter / no jobs). Skipping this page.")
        return None
    except Exception:
        logger.error("Unexpected error while locating job list.", exc_info=True)
        return None

def get_scrollable(driver, el):
    return driver.execute_script(scripts.SCROLL_BODY, el)

def extract_li(driver,li):
    # Force render: bring card into viewport
    try:
        driver.execute_script(scripts.SCROLL_INTO_VIEW, li)
    except StaleElementReferenceException:
        logger.error("StaleElementReferenceException encountered while scrolling into view.")
        return None
    time.sleep(const.DATA_SCRAPING_TIME)

    # job id (on li or inner div)
    job_id = li.get_attribute(elem.JOB_ID)
    job_title = li.find_element(By.CLASS_NAME, elem.JOB_TITLE).text
    linkedin_verified = 'N'
    if '\n' in job_title:
        if 'verification' in job_title.split('\n')[1].lower():
            linkedin_verified = 'Y'
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

def if_no_jobs_found(driver):
    try:
        no_jobs_card = driver.find_element(By.CLASS_NAME, "jobs-search-results-list__no-jobs-available-card")
        logger.info("No jobs available: Jobs no longer available were omitted from results.")
        return True # Stop further scraping
    except Exception:
        return False


def direct_to_jobs_page(driver, URL):
    driver.get(URL)
    time.sleep(const.SLEEP_TIME_AFTER_DIRECT_TO_JOBS)
    try:
        if not (if_no_jobs_found(driver)):
            WebDriverWait(driver, const.JOB_PAGE_RENDERING_TIME).until(
                EC.presence_of_element_located((By.ID, elem.GLOBAL_NAVBAR))
            )
            WebDriverWait(driver, const.JOB_PAGE_ELEMENTS_RENDERING_TIME).until(EC.presence_of_element_located((By.ID, elem.GLOBAL_NAV_SEARCH)))
            logger.info("Homepage loaded successfully.")
        else:
            return
    except TimeoutException:
        logger.error("Timeout: Unable to locate the global navigation search bar. Verifying page content...")
        logger.error(driver.page_source)
    time.sleep(const.SLEEP_TIME_AFTER_DIRECT_TO_JOBS)

def extract_job_details(driver, lis, seen, ordered, job_category):
    for li in lis:
        try:
            data = extract_li(driver, li)
            if not data:
                continue
            job_id, job_title, company, company_location, job_link, job_type, linkedin_verified = data
            if job_id and int(job_id) not in seen:
                seen.add(int(job_id))
                ordered.append((job_id, job_title, company, company_location, job_link, job_type, linkedin_verified, job_category, "LinkedIn"))
                logger.info(f"{job_id}, {job_title}, {company}, {company_location}, {job_link}, {job_type}, {linkedin_verified}, {job_category}, LinkedIn")
        except StaleElementReferenceException:
            logger.error("StaleElementReferenceException encountered while extracting job details.")
            continue

def scrape_jobs(driver,seen,ordered,ul,wait, scrollable, job_category):
    stalls = 0
    last_visible_count = 0
    max_iterations = const.MAX_ITERATION_COUNT  # Set a reasonable limit to prevent infinite loops
    iterations = 0
    while iterations < max_iterations:
        iterations += 1
        # Re-anchor if the list re-rendered
        try:
            lis = ul.find_elements(By.CSS_SELECTOR, elem.ITEMS_IN_LIST)
            extract_job_details(driver, lis, seen, ordered, job_category)
        except StaleElementReferenceException:
            ul = get_ul(wait, driver)
            scrollable = get_scrollable(driver, ul)
            logger.error("StaleElementReferenceException encountered while finding list items.")
            continue

        # Extract from all currently visible lis (force-render per li)
        # Smooth incremental scroll (no PAGE_DOWN, no jump-to-end)
        try:
            driver.execute_script(scripts.SMOOTH_SCROLL,scrollable)
        except StaleElementReferenceException:
            ul = get_ul(wait, driver)
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
            ul = get_ul(wait, driver)
            scrollable = get_scrollable(driver, ul)
            logger.error("StaleElementReferenceException encountered while scraping jobs.")
            continue


        at_bottom = driver.execute_script(scripts.SCROLL_TO_BOTTOM,scrollable)
        if at_bottom and stalls >= const.ITEM_COUNTS_PER_SCROLL:
            break

    if iterations >= max_iterations:
        logger.info("Reached maximum iterations. Exiting to prevent infinite loop.")

def chrome_sign_in() -> Options:
    opts = Options()
    load_options_arguments(opts)
    return opts

def linkedin_data_scraper(opts: Options, job_ids_in_db: set, user: str, password: str, dsn: str):
    seen = job_ids_in_db
    urls = const.LINKEDIN_RECOMMENDED_JOB_URL
    for url in urls:
        driver = webdriver.Chrome(options=opts)
        wait = WebDriverWait(driver, const.TIMEOUT_BEFORE_DATA_SCRAPING)
        job_category = job_category_map.get_job_category(url)
        direct_to_jobs_page(driver,url)
        count = scrape_top_picks_results_count(wait)
        loops = int(count / const.ITEMS_PER_PAGE) + 1
        logger.info (f"Estimated loops: {loops}")
        for loop in range(loops):
            ordered = []
            scrape_results_in_every_page(loop, url, driver, wait, seen, ordered, job_category)
            logger.info(f"Loaded {len(ordered)} jobs in order.")
            fetch_data_to_db(ordered, user, password, dsn)
        time.sleep(const.TIMEOUT_BEFORE_CLOSING_DRIVER)
        driver.quit()

def fetch_data_to_db(ordered, user: str, password: str, dsn: str):
    if ordered:
        conn = setup_db_connection(user, password, dsn)
        insert_job_posts(conn, ordered)

def scrape_results_in_every_page(loop, url, driver, wait, seen, ordered, job_category) :
    query_params = f"?start={loop * const.ITEMS_PER_PAGE}"
    redirect_url = url + query_params
    direct_to_jobs_page(driver, redirect_url)
    ul = get_ul(wait, driver)
    if not ul:
        logger.info(f"No jobs on page `{redirect_url}`. Moving to next page.")
        return
    scrollable = get_scrollable(driver, ul)
    if not scrollable:
        logger.info(f"Scrollable element not found on page `{redirect_url}`. Moving to next page.")
        return
    scrape_jobs(driver, seen, ordered, ul, wait, scrollable, job_category)
    time.sleep(const.TIMEOUT_AFTER_DATA_SCRAPING)

def scrape_top_picks_results_count(wait: WebDriverWait) -> int:
    # case-insensitive helper in XPath
    ci = "translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz')"

    # Try several DOM variants LinkedIn uses
    candidates = [
        # direct: header -> the next <small> with "results"
        f"//h2[contains({ci}, 'top job picks for you')]/following::small[contains({ci}, 'results')][1]",
        # header inside a container (section/div)
        f"//section[.//h2[contains({ci}, 'top job picks for you')]]//small[contains({ci}, 'results')]",
        f"//div[.//h2[contains({ci}, 'top job picks for you')]]//small[contains({ci}, 'results')]",
        # ultra fallback: any small with "results" in left rail
        f"(//aside//small[contains({ci}, 'results')] | //main//small[contains({ci}, 'results')])[1]",
    ]

    count_el = None
    for xp in candidates:
        try:
            count_el = wait.until(EC.presence_of_element_located((By.XPATH, xp)))
            if count_el:
                break
        except TimeoutException as e:
            logger.error("Top Picks results not found")
            TimeoutException("Top Picks results not found")

    text = count_el.text.strip()  # e.g., "4 results", "28 results"
    m = re.search(r"\d+", text)
    n = int(m.group()) if m else 0
    count = n
    logger.info(f"{count} results")
    return count

