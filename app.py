import json
from datetime import datetime

from playwright.sync_api import sync_playwright

from utils.blacklisted_companies import blacklisted
from utils.constants import SOURCE_URL
from utils.existing_links import get_existing_job_links
from utils.normalize_link import normalize_link
from utils.supabase_client import get_supabase
from utils.telegram_send_message import send_telegram_message

# send new batch message
timestamp = datetime.now().strftime("%A, %B %d, %Y at %-I:%M %p")
send_telegram_message(
    message=f"<code>{timestamp}</code>\n🤖 <b>Starting new job scraping batch...</b>"
)

supabase = get_supabase()

existing_links = get_existing_job_links()

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context()

    # Load saved cookies
    with open("linkedin_cookies.json", "r") as f:
        cookies = json.load(f)
        context.add_cookies(cookies)

    page = context.new_page()
    page.goto(SOURCE_URL)
    page.wait_for_timeout(3000)

    with open("page_dump.html", "w", encoding="utf-8") as f:
        f.write(page.content())

    # pagination
    page_num = 1
    jobs_list = []

    seen_links = set()
    skipped_links = 0
    blacklisted_links = 0

    while True:
        try:
            previous_count = 0
            while True:
                job_cards = page.locator(".job-card-container")
                current_count = job_cards.count()

                if current_count == previous_count:
                    break  # No new jobs loaded

                previous_count = current_count

                # Scroll the last job into view to trigger lazy load
                job_cards.nth(current_count - 1).scroll_into_view_if_needed()
                # Wait until new jobs are added
                page.wait_for_timeout(1000)

            job_cards = page.locator(".job-card-container").all()

            for job in job_cards:
                try:
                    # extract company name
                    company = job.locator(
                        ".artdeco-entity-lockup__subtitle"
                    ).first.inner_text()

                    # skip blacklisted companies
                    if company.strip().lower() in blacklisted:
                        send_telegram_message(
                            message=f"🚫 Skipped blacklisted company: <b>{company}</b>"
                        )
                        continue

                    # extract job link and normalize
                    raw_link = job.locator("a").first.get_attribute("href")
                    if not raw_link:
                        continue
                    parsed_link = normalize_link(f"https://linkedin.com{raw_link}")

                    # skip if link already seen or in db
                    if parsed_link in seen_links or parsed_link in existing_links:
                        print("🚫 Skipped adding job, already seen or in database!")
                        continue

                    location = job.locator(
                        ".artdeco-entity-lockup__caption"
                    ).first.inner_text()
                    title = job.locator("strong").first.inner_text()

                    jobs_list.append(
                        {
                            "title": title,
                            "company": company,
                            "location": location,
                            "job_link": parsed_link,
                        }
                    )

                    seen_links.add(parsed_link)

                    send_telegram_message(
                        title=title, company=company, href=parsed_link
                    )

                except Exception as e:
                    print(f"⚠️ Skipping job due to error: {e}")

            # find next button
            next_btn = page.locator('button[aria-label="View next page"]')

            if next_btn.is_visible() and not next_btn.is_disabled():
                next_btn.click()
                page.wait_for_timeout(2000)
                page_num += 1
            else:
                print("✅ Reached last page.")
                break
        except Exception as e:
            send_telegram_message(f"⚠️ Scraper failed:\n<code>{e}</code>")
            context.close()
            browser.close()
            raise

    context.close()
    browser.close()

    try:
        supabase.table("jobs").insert(jobs_list).execute()
        send_telegram_message(
            f"✅ <b>Scraper finished!</b>\nTotal Jobs Found: {len(jobs_list)}\nJobs Collected: {len(jobs_list)}"
        )
    except Exception as e:
        send_telegram_message(f"⚠️ <b>Supabase insertion failed:</b>\n<code>{e}</code>")
