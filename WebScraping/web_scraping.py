import re
from selenium import webdriver
from selenium.webdriver.common.by import By
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
    option.add_argument("--headless=new")  # remove if you want to see the browser
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

def extract_job_details(driver, lis, seen, ordered, job_category):
    for li in lis:
        try:
            data = extract_li(driver, li)
            if not data:
                continue
            job_id, job_title, company, company_location, job_link, job_type, linkedin_verified = data
            if job_id and int(job_id) not in seen:
                seen.add(int(job_id))
                ordered.append((job_id, job_title, company, company_location, job_link, job_type, linkedin_verified, job_category))
                print(job_id, job_title, company, company_location, job_link, job_type, linkedin_verified, job_category)
        except StaleElementReferenceException:
            continue

def scrape_jobs(driver,seen,ordered,ul,wait, scrollable, job_category):
    stalls = 0
    last_visible_count = 0
    max_iterations = 10  # Set a reasonable limit to prevent infinite loops
    iterations = 0
    while iterations < max_iterations:
        iterations += 1
        # Re-anchor if the list re-rendered
        try:
            lis = ul.find_elements(By.CSS_SELECTOR, elem.ITEMS_IN_LIST)
            extract_job_details(driver, lis, seen, ordered, job_category)
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

    if iterations >= max_iterations:
        print("Reached maximum iterations. Exiting to prevent infinite loop.")

def chrome_sign_in() -> Options:
    opts = Options()
    load_options_arguments(opts)
    return opts

def linkedin_data_scraper(opts: Options, job_ids_in_db: set):
    seen = job_ids_in_db
    ordered = []
    driver = webdriver.Chrome(options=opts)
    wait = WebDriverWait(driver, const.TIMEOUT_BEFORE_DATA_SCRAPING)
    urls = const.LINKEDIN_RECOMMENDED_JOB_URL
    for url in urls:
        job_category = "Recommended"
        if "recommended" in url:
            job_category = "Recommended"
        elif "easy-apply" in url:
            job_category = "Easy Apply"
        elif "remote-jobs" in url:
            job_category = "Remote"
        elif "it-services-and-it-consulting" in url:
            job_category = "IT"
        elif "human-resources" in url:
            job_category = "HR"
        elif "financial-services" in url:
            job_category = "Finance"
        elif "sustainability" in url:
            job_category = "Sustainability"
        elif "hybrid" in url:
            job_category = "Hybrid"
        elif "pharmaceuticals" in url:
            job_category = "Pharma"
        elif "part-time-jobs" in url:
            job_category = "Part-time"
        elif "social-impact" in url:
            job_category = "Social impact"
        elif "manufacturing" in url:
            job_category = "Manufacturing"
        elif "real-estate" in url:
            job_category = "Real estate"
        elif "hospitals-and-healthcare" in url:
            job_category = "Healthcare"
        elif "government" in url:
            job_category = "Government"
        elif "biotechnology" in url:
            job_category = "Biotech"
        elif "defense-and-space" in url:
            job_category = "Defense and space"
        elif "operations" in url:
            job_category = "Operations"
        elif "construction" in url:
            job_category = "Construction"
        elif "small-business" in url:
            job_category = "Small biz"
        elif "human-services" in url:
            job_category = "Human services"
        elif "publishing" in url:
            job_category = "Publishing"
        elif "retail" in url:
            job_category = "Retail"
        elif "hospitality" in url:
            job_category = "Hospitality"
        elif "education" in url:
            job_category = "Education"
        elif "media" in url:
            job_category = "Media"
        elif "restaurants" in url:
            job_category = "Restaurants"
        elif "transportation-and-logistics" in url:
            job_category = "Logistics"
        elif "digital-security" in url:
            job_category = "Digital security"
        elif "marketing-and-advertising" in url:
            job_category = "Marketing"
        elif "career-growth" in url:
            job_category = "Career growth"
        elif "higher-edu" in url:
            job_category = "Higher ed"
        elif "food-and-beverages" in url:
            job_category = "Food & bev"
        elif "non-profits" in url:
            job_category = "Non-profit"
        elif "gaming" in url:
            job_category = "Gaming"
        elif "staffing-and-recruiting" in url:
            job_category = "Recruiting"
        elif "veterinary-medicine" in url:
            job_category = "Veterinary med"
        elif "civil-eng" in url:
            job_category = "Civil eng"
        elif "work-life-balance" in url:
            job_category = "Work-life balance"
        elif "apparel-and-fashion" in url:
            job_category = "Fashion"
        direct_to_jobs_page(driver,url)
        count = scrape_top_picks_results_count(wait)
        loops = int(count / 24) + 1
        print (f"Estimated loops: {loops}")
        for loop in range(loops):
            scrape_results_in_every_page(loop, url, driver, wait, seen, ordered, job_category)
    driver.quit()
    print(f"Loaded {len(ordered)} jobs in order.")
    return ordered

def scrape_results_in_every_page(loop, url, driver, wait, seen, ordered, job_category) :
    query_params = f"?start={loop * 24}"
    redirect_url = url + query_params
    direct_to_jobs_page(driver, redirect_url)
    ul = get_ul(wait)
    scrollable = get_scrollable(driver, ul)
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
            TimeoutException("Top Picks results not found")

    text = count_el.text.strip()  # e.g., "4 results", "28 results"
    m = re.search(r"\d+", text)
    n = int(m.group()) if m else 0
    count = n
    print(f"{count} results")
    return count

