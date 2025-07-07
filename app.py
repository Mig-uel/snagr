import json
import time
from datetime import datetime
from pathlib import Path

from playwright.sync_api import sync_playwright

from utils.blacklisted_companies import blacklisted
from utils.constants import HEADLESS, SOURCE_URL
from utils.existing_links import get_existing_job_links
from utils.normalize_link import normalize_link
from utils.supabase_client import get_supabase
from utils.telegram_send_message import send_telegram_message

parent_dir = Path(__file__).resolve().parent

supabase = get_supabase()

existing_links = get_existing_job_links()


with sync_playwright() as p:
    browser = p.chromium.launch(headless=HEADLESS)
    context = browser.new_context()

    # Load saved cookies
    with open(Path.joinpath(parent_dir, "linkedin_cookies.json"), "r") as f:
        cookies = json.load(f)
        context.add_cookies(cookies)

    page = context.new_page()
    page.goto(SOURCE_URL)
    page.wait_for_timeout(3000)

    # send new batch message
    now = datetime.now()
    timestamp = now.strftime("%B %d, %Y @ %I:%M %p")

    send_telegram_message(
        message=f"<code>{timestamp}</code>\n<b>⏳ | Running scraper</b>"
    )

    # TODO: work on detecting cookie expiration
    # if "login" in page.url:
    #     send_telegram_message(
    #         "⚠️ <b>LinkedIn session expired. Please upload a new cookie.</b>"
    #     )
    #     raise Exception("⚠️ <b>Session Expired</b>")

    # pagination
    page_num = 1
    jobs_list = []
    total_jobs = 0

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
                page.wait_for_timeout(2000)

                page.locator(".jobs-search-pagination").scroll_into_view_if_needed()

                # Wait until more jobs load
                page.wait_for_timeout(3000)

            job_cards = page.locator(".job-card-container").all()
            total_jobs += len(job_cards)

            send_telegram_message(f"🔵 | <b>Page #{page_num}</b>")

            for job in job_cards:
                try:
                    # extract company name
                    company = job.locator(
                        ".artdeco-entity-lockup__subtitle"
                    ).first.inner_text()

                    # skip blacklisted companies
                    if company.strip().lower() in blacklisted:
                        blacklisted_links += 1
                        print(f"🚫 | Skipped blacklisted company: {company}")
                        # send_telegram_message(message=f"🚫 | Skipped blacklisted company: <b>{company}</b>")
                        continue

                    title_locator = job.locator("strong").first
                    # try:
                    #     title_locator.wait_for(
                    #         timeout=3000
                    #     )  # wait up to 3s for it to appear
                    title = title_locator.inner_text(timeout=2000)
                    # except Exception as e:
                    #     print(f"⚠️ Title not found or timeout: {e}")
                    #     continue

                    # TODO: optimize conditional
                    if (
                        "lead" in title.strip().lower()
                        or "senior" in title.strip().lower()
                        or "sr" in title.strip().lower()
                        or "staff" in title.strip().lower()
                        or "principal" in title.strip().lower()
                    ):
                        skipped_links += 1
                        print("🚫 | Skipped job, contains unwanted terms!")
                        continue

                    # extract job link and normalize
                    raw_link = job.locator("a").first.get_attribute("href")
                    if not raw_link:
                        continue
                    parsed_link = normalize_link(f"https://linkedin.com{raw_link}")

                    # skip if link already in db or seen
                    if parsed_link in existing_links:
                        skipped_links += 1
                        print("🚫 | Skipped job, already in database!")
                        continue
                    if parsed_link in seen_links:
                        skipped_links += 1
                        print("🚫 | Skipped job, already seen!")
                        continue

                    location = job.locator(
                        ".artdeco-entity-lockup__caption"
                    ).first.inner_text()

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
                    time.sleep(0.2)

                except Exception as e:
                    print(f"⚠️ | <b>Skipping job due to error:</b>\n<code>{e}</code>")

            # find next button
            next_btn = page.locator('button[aria-label="View next page"]')

            if next_btn.is_visible() and not next_btn.is_disabled():
                next_btn.click()
                page.wait_for_timeout(2000)
                page_num += 1
            else:
                print("✅ | Reached last page.")
                break
        except Exception as e:
            send_telegram_message(f"⚠️ | <b>Scraper failed:</b>\n<code>{e}</code>")
            context.close()
            browser.close()
            raise

    context.close()
    browser.close()

    try:
        if jobs_list:
            supabase.table("jobs").insert(jobs_list).execute()
            send_telegram_message(
                f"🟢 | <b>Scraper finished!</b>\n\nTotal Jobs Found: {total_jobs}\nJobs Collected: {len(jobs_list)}\nJobs Skipped: {skipped_links}\nBlacklisted Jobs: {blacklisted_links}"
            )
        else:
            send_telegram_message(
                f"⚪ | <b>No new jobs to insert.</b>\nTotal Jobs Found: {total_jobs}"
            )
    except Exception as e:
        send_telegram_message(
            f"⚠️ | <b>Supabase insertion failed:</b>\n<code>{e}</code>"
        )
