import time
from datetime import datetime

from playwright.sync_api import sync_playwright
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

from utils.blacklisted_companies import blacklisted
from utils.constants import SOURCE_URL
from utils.normalize_link import normalize_link
from utils.supabase_client import get_supabase
from utils.telegram_send_message import send_telegram_message

# SUPABASE
supabase = get_supabase()

options = Options()
options.add_argument("--headless")
options.add_argument("--window-size=1920,1080")

# set up driver
driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()), options=options
)


# open the page
driver.get(SOURCE_URL)
time.sleep(3)

# send new batch message
timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
send_telegram_message(
    message=f"<code>{timestamp}</code> - 🚀 Starting new job scraping batch..."
)

# previous jobs count
prev_count = 0

# scroll to load more jobs
while True:
    jobs = driver.find_elements(By.CLASS_NAME, "base-card")
    current_count = len(jobs)

    if current_count == prev_count:
        break  # no new jobs loaded

    prev_count = current_count

    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)

# parse job listings
jobs = driver.find_elements(By.CLASS_NAME, "base-card")
jobs_list = []
seen_links = []


# get existing links from DB
existing_links = {
    item["job_link"]
    for item in supabase.table("jobs").select("job_link").execute().data
}

try:
    for job in jobs:
        try:
            # Scroll job into view and click to load details
            driver.execute_script("arguments[0].scrollIntoView();", job)
            # job.click()

            # # Wait for the Apply button in the side panel
            # apply_btn = WebDriverWait(driver, 5).until(
            #     EC.element_to_be_clickable((By.CLASS_NAME, "jobs-apply-button"))
            # )

            # # Get the data-tracking-control-name attribute
            # tracking_attr = apply_btn.get_attribute("data-tracking-control-name")

            # # Only continue if it's the external application button
            # if tracking_attr != "public_jobs_apply-link-offsite_sign-up-modal":
            #     print("Skipping internal or modal-only job")
            #     continue

            # Now extract basic job info again (from the original card)
            raw_link = job.find_element(By.TAG_NAME, "a").get_attribute("href")
            parsed_link = normalize_link(raw_link)

            company = job.find_element(By.CLASS_NAME, "base-search-card__subtitle").text

            if company.lower() in blacklisted:
                send_telegram_message(
                    message=f"🚫 Skipped blacklisted company: <b>{company}</b>"
                )
                continue

            if parsed_link in seen_links:
                print("🚫 Skipped adding job, already seen!")
                continue

            if parsed_link in existing_links:
                print("🚫 Skipped adding job, already in database!")
                continue

            title = job.find_element(By.CLASS_NAME, "base-search-card__title").text
            location = job.find_element(By.CLASS_NAME, "job-search-card__location").text

            jobs_list.append(
                {
                    "title": title,
                    "company": company,
                    "location": location,
                    "job_link": parsed_link,
                }
            )

            seen_links.append(parsed_link)

            send_telegram_message(title=title, company=company, href=parsed_link)

        except Exception as e:
            print("Skipping a job due to error:", e)
except Exception as e:
    send_telegram_message(f"⚠️ Scraper failed:\n<code>{e}</code>")
    driver.quit()
    raise

driver.quit()

try:
    supabase.table("jobs").insert(jobs_list).execute()
    send_telegram_message(
        f"✅ <b>Scraper finished!</b>\nTotal Jobs Found: {len(jobs)}\nJobs Collected: {len(jobs_list)}\nJobs Skipped {len(jobs) - len(jobs_list)}"
    )
except Exception as e:
    send_telegram_message(f"⚠️ Scraper failed:\n<code>{e}</code>")
