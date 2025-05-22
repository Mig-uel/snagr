import os
import time

import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from supabase import Client, create_client
from webdriver_manager.chrome import ChromeDriverManager

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

# create supabase client
supabase: Client = create_client(url, key)


# check + insert
def job_exists(link):
    result = supabase.table("jobs").select("job_link").eq("job_link", link).execute()
    return len(result.data) > 0


options = Options()
options.add_argument("--headless")
options.add_argument("--window-size=1920, 1080")

# set up driver
driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()), options=options
)

# LinkedIn job search URL
url = "https://www.linkedin.com/jobs/search/?f_TPR=r3600&keywords=junior%20software%20engineer&location=United%20States&origin=JOB_SEARCH_PAGE_JOB_FILTER"

# open the page
driver.get(url)
time.sleep(3)

# scroll to load more jobs
for _ in range(3):
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)

# parse job listings
jobs = driver.find_elements(By.CLASS_NAME, "base-card")

job_list = []

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
        title = job.find_element(By.CLASS_NAME, "base-search-card__title").text
        company = job.find_element(By.CLASS_NAME, "base-search-card__subtitle").text
        location = job.find_element(By.CLASS_NAME, "job-search-card__location").text
        job_link = job.find_element(By.TAG_NAME, "a").get_attribute("href")

        if not job_exists(job_link):
            supabase.table("jobs").insert(
                {
                    "title": title,
                    "company": company,
                    "location": location,
                    "job_link": job_link,
                }
            ).execute()

            job_list.append(
                {
                    "Title": title,
                    "Company": company,
                    "Location": location,
                    "Job Page Link": job_link,
                }
            )

    except Exception as e:
        print("Skipping a job due to error:", e)

driver.quit()

# Save to DataFrame
df = pd.DataFrame(job_list)
print(df.head())

# Optionally save to CSV
df.to_csv("linkedin_jobs.csv", index=False)
