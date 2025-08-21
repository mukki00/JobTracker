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

def chrome_sign_in():
    URL = "https://www.linkedin.com/jobs/collections/recommended"
    opts = Options()
    opts.add_argument(r"user-data-dir=C:\Selenium\Profiles\B_Automation")
    opts.add_argument(r"profile-directory=Default")
    # opts.add_argument("--headless=new")  # remove if you want to see the browser
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-first-run")
    opts.add_argument("--no-default-browser-check")

    driver = webdriver.Chrome(options=opts)
    driver.get(URL)
    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.ID, "global-nav"))
        )
        WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.ID, "global-nav-search")))
        print("Homepage loaded successfully.")
    except TimeoutException:
        print("Timeout: Unable to locate the global navigation search bar. Verifying page content...")
        print(driver.page_source)
    time.sleep(60)
    wait = WebDriverWait(driver, 20)

    def get_ul():
        # UL right after the sentinel (works across class changes)
        return wait.until(EC.presence_of_element_located(
            (By.XPATH, "//div[@data-results-list-top-scroll-sentinel]/following-sibling::ul[1]")
        ))

    def get_scrollable(el):
        return driver.execute_script("""
        let e = arguments[0];
        while (e && e !== document.body) {
          const s = getComputedStyle(e);
          if ((s.overflowY==='auto'||s.overflowY==='scroll') && e.scrollHeight>e.clientHeight) return e;
          e = e.parentElement;
        }
        return document.scrollingElement;
        """, el)

    wait_short = WebDriverWait(driver, 2)
    def extract_li(li):
        # Force render: bring card into viewport
        try:
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", li)
        except StaleElementReferenceException:
            return None
        time.sleep(0.15)

        # job id (on li or inner div)
        job_id = li.get_attribute("data-occludable-job-id")
        job_title = li.find_element(By.CLASS_NAME, "job-card-list__title--link").text
        linkedin_verified = False
        if '\n' in job_title:
            if 'verification' in job_title.split('\n')[1].lower():
                linkedin_verified = True
            job_title = job_title.split('\n')[0]
        company = li.find_element(By.CLASS_NAME, "artdeco-entity-lockup__subtitle").text
        company_location = li.find_element(By.CLASS_NAME, "job-card-container__metadata-wrapper").text
        job_type = "Not Specified"
        if '(' and ')' in company_location:
            job_type = company_location.split('(')[1].split(')')[0]
            company_location = company_location.split('(')[0]
        job_link = li.find_element(By.TAG_NAME, "a").get_attribute("href")
        # filter ghost rows
        if not (job_id or job_title or company or job_link):
            return None
        return job_id, job_title, company, company_location, job_link, job_type, linkedin_verified
    # ---- MAIN SCROLL/COLLECT LOOP (replace your while True block) ----
    seen, ordered = set(), []
    ul = get_ul()
    scrollable = get_scrollable(ul)

    stalls = 0
    last_visible_count = 0

    while True:
        # Re-anchor if the list re-rendered
        try:
            lis = ul.find_elements(By.CSS_SELECTOR, "li[data-occludable-job-id], li[id^='ember']")
        except StaleElementReferenceException:
            ul = get_ul()
            scrollable = get_scrollable(ul)
            continue

        # Extract from all currently visible lis (force-render per li)
        for li in lis:
            try:
                data = extract_li(li)
                if not data:
                    continue
                job_id, job_title, company, company_location, job_link, job_type, linkedin_verified = data
                if job_id and job_id not in seen:
                    seen.add(job_id)
                    ordered.append((job_id, job_title, company, company_location, job_link, job_type, linkedin_verified))
                    print(job_id, job_title, company, company_location, job_link, job_type, linkedin_verified)
            except StaleElementReferenceException:
                continue

        # Smooth incremental scroll (no PAGE_DOWN, no jump-to-end)
        try:
            driver.execute_script(
                "arguments[0].scrollTop = arguments[0].scrollTop + Math.floor(arguments[0].clientHeight*0.65);",
                scrollable
            )
        except StaleElementReferenceException:
            ul = get_ul()
            scrollable = get_scrollable(ul)
            continue

        time.sleep(0.6)

        # Stall detection: compare visible li count (like-for-like)
        try:
            now_visible_count = len(ul.find_elements(By.CSS_SELECTOR, "li[data-occludable-job-id], li[id^='ember']"))
        except StaleElementReferenceException:
            ul = get_ul()
            scrollable = get_scrollable(ul)
            continue

        if now_visible_count <= last_visible_count:
            stalls += 1
        else:
            stalls = 0
            last_visible_count = now_visible_count

        at_bottom = driver.execute_script(
            "const el=arguments[0]; return Math.abs(el.scrollHeight - el.scrollTop - el.clientHeight) < 4;",
            scrollable
        )
        if at_bottom and stalls >= 5:
            break

    print(f"Loaded {len(ordered)} jobs in order.")

