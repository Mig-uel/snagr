from datetime import datetime

from playwright.sync_api import sync_playwright

from utils.blacklisted_companies import blacklisted
from utils.constants import SOURCE_URL
from utils.normalize_link import normalize_link
from utils.supabase_client import get_supabase
from utils.telegram_send_message import send_telegram_message

# send new batch message
timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
send_telegram_message(
    message=f"<code>{timestamp}</code> - 🚀 Starting new job scraping batch..."
)


supabase = get_supabase()

existing_links = {
    item["job_link"]
    for item in supabase.table("jobs").select("job_link").execute().data
}

with sync_playwright() as p:
    browser = p.chromium.launch()

    page = browser.new_page()
    page.goto(SOURCE_URL)

    page.wait_for_timeout(3000)

    print(page.title())

    prev_count = 0
    # scroll to load more jobs
    while True:
        jobs = page.locator(".base-card")

        current_count = jobs.count()

        if current_count == prev_count:
            break  # no new jobs loaded

        prev_count = current_count

        page.evaluate("window.scrollTo(0, document.body.scrollHeight);")

        page.wait_for_timeout(2000)

    jobs = page.locator(".base-card").all()
    jobs_list = []
    seen_links = set()

    try:
        for job in jobs:
            try:
                # extract raw link from job card
                link_element = job.locator("a").first
                raw_link = link_element.get_attribute("href")

                # normalize link (i.e. remove search params)
                parsed_link = normalize_link(raw_link)

                # extract company name
                company_element = job.locator(".base-search-card__subtitle").first
                company = company_element.inner_text()

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

                # extract job title
                title_element = job.locator(".base-search-card__title").first
                title = title_element.inner_text()

                # extract job location
                location_element = job.locator(".job-search-card__location").first
                location = location_element.inner_text()

                jobs_list.append(
                    {
                        "title": title,
                        "company": company,
                        "location": location,
                        "job_link": parsed_link,
                    }
                )

                # append current link to seen list
                seen_links.add(parsed_link)

                send_telegram_message(title=title, company=company, href=parsed_link)
            except Exception as e:
                print(f"⚠️ Skipping job due to error: {e}")
    except Exception as e:
        send_telegram_message(f"⚠️ Scraper failed:\n<code>{e}</code>")
        browser.close()
        raise

    browser.close()

    try:
        supabase.table("jobs").insert(jobs_list).execute()
        send_telegram_message(
            f"✅ <b>Scraper finished!</b>\nTotal Jobs Found: {len(jobs)}\nJobs Collected: {len(jobs_list)}\nJobs Skipped {len(jobs) - len(jobs_list)}"
        )
    except Exception as e:
        send_telegram_message(f"⚠️ Scraper failed:\n<code>{e}</code>")
