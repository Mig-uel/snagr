import json
import math
from datetime import datetime
from pathlib import Path
import asyncio
from playwright.async_api import async_playwright
import logging

from db import get_existing_job_links, get_supabase
from telegram import send_telegram_message
from utils import (
    BLACKLISTED_COMPANIES,
    IS_HEADLESS,
    SOURCE_URL,
    is_valid_job_title,
    normalize_job_link,
    prevent_multiple_instances
)

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


async def main():
    try:
        # Get Supabase client
        supabase = get_supabase()

        # Fetch existing links from database
        existing_links = get_existing_job_links()

        # Get parent directory (scraper)
        parent_dir = Path(__file__).resolve().parent 

        # Get cookies file path
        cookies_file_path = Path.joinpath(parent_dir, "linkedin_cookies.json")

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=IS_HEADLESS)
            context = await browser.new_context(viewport={"width": 1400, "height": 3500})

            # Add cookies to context
            with open(cookies_file_path, "r") as f:
                cookies = json.load(f)
                await context.add_cookies(cookies)
            
            page = await context.new_page()
            await page.goto(SOURCE_URL)

            # Wait for specific element to load
            results_element = page.locator("small.jobs-search-results-list__text")
            results_text = await results_element.text_content()
            results_count = int(results_text.strip().split(" ")[0].replace(",", "").replace("+", ""))
            
            # Send initial Telegram message
            now = datetime.now().strftime("%B %d, %Y @ %I:%M %p")
            send_telegram_message(
                message=f"<code>{now}</code>\n<b>ℹ️ | Running scraper</b>"
            )

            # Calculate results stats
            results_per_page = 25
            total_pages = math.ceil(results_count / results_per_page)

            # Send stats message
            send_telegram_message(
                message=f"<b>✨ | Stats</b>\n\nEstimated Total Results: ~{results_count}\nEstimated Total Pages: ~{total_pages}"
            )


            # Pagination variables
            current_page = 1
            jobs = []
            total_jobs = 0
            seen_links = set()
            skipped_links = 0
            blacklisted_links = 0

            # Outer pagination loop for pages
            while True:
                send_telegram_message(f"🔵 | <b>Page #{current_page}</b>")

                try:
                    # Find all job cards on the page
                    current_job_cards_elements = page.locator(".job-card-container")
                    current_job_cards = await current_job_cards_elements.all()

                    # Count total jobs on current page
                    total_jobs += len(current_job_cards)

                    # Process each job card
                    for job in current_job_cards:
                        try:
                            # Extract company name
                            company = await job.locator(
                                    ".artdeco-entity-lockup__subtitle"
                                ).first.inner_text()
                            
                            # Skip blacklisted companies
                            if company.strip().lower() in BLACKLISTED_COMPANIES:
                                blacklisted_links += 1
                                logging.info(f"Blacklisted Company: {company}")
                                continue
                            
                            # Extract job title
                            try:
                                title = await job.locator("strong").first.inner_text(timeout=2000)
                            except Exception as e:
                                logging.error(f"Title Not Found/Timeout: {e}")
                                continue
                            
                            # Skip certain job titles/keywords
                            if not is_valid_job_title(title=title):
                                skipped_links += 1
                                logging.info(f"Invalid Title: {title}")
                                continue

                            # Extract LinkedIn URL
                            raw_linkedin_url = await job.locator("a").first.get_attribute("href")
                            parsed_linkedin_url = normalize_job_link(raw_linkedin_url)


                        except Exception as e:
                            logging.error(f"Error Extracting Job Details: {e}")
                            continue
                    break
                except Exception as e:
                    logging.critical(f"Scraper Failed: {e}")
                    send_telegram_message(f"⚠️ | <b>Scraper failed:</b>\n<code>{e}</code>")
                    raise

            await context.close()
            await browser.close()

    except Exception as e:
        logging.critical(f"⚠️ | Error initializing scraper: {e}")
        return

asyncio.run(main())













# try:
#     # Create a PID file to prevent multiple instances
#     PID_FILE = prevent_multiple_instances()

#     PARENT_DIR = Path(__file__).resolve().parent  # parent dir (scraper)

#     supabase = get_supabase()
#     existing_links = get_existing_job_links()  # fetch existing links from db

#     with async_playwright() as p:
#         browser = await p.chromium.launch(headless=IS_HEADLESS)
#         context = browser.new_context()

#         # load saved cookies
#         with open(Path.joinpath(PARENT_DIR, "linkedin_cookies.json"), "r") as f:
#             cookies = json.load(f)
#             context.add_cookies(cookies)

#         page = context.new_page()
#         page.goto(SOURCE_URL)
#         page.wait_for_timeout(3000)


#         # TODO: work on detecting cookie expiration
#         # if "login" in page.url:
#         #     send_telegram_message(
#         #         "⚠️ <b>LinkedIn session expired. Please upload a new cookie.</b>"
#         #     )
#         #     raise Exception("⚠️ <b>Session Expired</b>")


#         while True:
#             send_telegram_message(f"🔵 | <b>Page #{page_num}</b>")

#                 for job in job_cards:
#                     try:
#                         # extract company name
#                         company = job.locator(
#                             ".artdeco-entity-lockup__subtitle"
#                         ).first.inner_text()

#                         # skip blacklisted companies
#                         if company.strip().lower() in BLACKLISTED_COMPANIES:
#                             blacklisted_links += 1
#                             print(f"🚫 | Skip (blacklisted company: {company})")
#                             continue

#                         title_locator = job.locator("strong").first
#                         # try:
#                         #     title_locator.wait_for(
#                         #         timeout=3000
#                         #     )  # wait up to 3s for it to appear
#                         title = title_locator.inner_text(timeout=2000)
#                         # except Exception as e:
#                         #     print(f"⚠️ Title not found or timeout: {e}")
#                         #     continue

#                         if is_valid_job_title(title=title):
#                             pass
#                         else:
#                             skipped_links += 1
#                             print("🚫 | Skip (title keywords not found in title)")
#                             print(f"⛔ | {title}")
#                             continue

#                         # extract job link and normalize
#                         raw_link = job.locator("a").first.get_attribute("href")
#                         if not raw_link:
#                             continue
#                         parsed_link = normalize_job_link(
#                             f"https://linkedin.com{raw_link}"
#                         )

#                         # skip if link already in db or seen
#                         if parsed_link in existing_links:
#                             skipped_links += 1
#                             print("🚫 | Skip (job already in database)")
#                             continue
#                         if parsed_link in seen_links:
#                             skipped_links += 1
#                             print("🚫 | Skip (job already parsed)")
#                             continue

#                         location = job.locator(
#                             ".artdeco-entity-lockup__caption"
#                         ).first.inner_text()

#                         jobs_list.append(
#                             {
#                                 "title": title,
#                                 "company": company,
#                                 "location": location,
#                                 "job_link": parsed_link,
#                             }
#                         )

#                         seen_links.add(parsed_link)

#                         send_telegram_message(
#                             title=title, company=company, href=parsed_link
#                         )
#                         time.sleep(0.2)

#                     except Exception as e:
#                         print(
#                             f"⚠️ | <b>Skipping job due to error:</b>\n<code>{e}</code>"
#                         )

#                 # find next button
#                 next_btn = page.locator('button[aria-label="View next page"]')

#                 if next_btn.is_visible() and not next_btn.is_disabled():
#                     next_btn.click()
#                     page.wait_for_timeout(2000)
#                     page_num += 1
#                 else:
#                     print("✅ | Reached last page.")
#                     break
#             except Exception as e:
#                 send_telegram_message(f"⚠️ | <b>Scraper failed:</b>\n<code>{e}</code>")
#                 context.close()
#                 browser.close()
#                 raise

#         context.close()
#         browser.close()

#         try:
#             if jobs_list:
#                 supabase.table("jobs").insert(jobs_list).execute()
#                 send_telegram_message(
#                     f"🟢 | <b>Scraper finished!</b>\n\nTotal Jobs Found: {total_jobs}\nJobs Collected: {len(jobs_list)}\nJobs Skipped: {skipped_links}\nBlacklisted Jobs: {blacklisted_links}"
#                 )
#             else:
#                 send_telegram_message(
#                     f"⚪ | <b>No new jobs to insert.</b>\nTotal Jobs Found: {total_jobs}"
#                 )
#         except Exception as e:
#             send_telegram_message(
#                 f"⚠️ | <b>Supabase insertion failed:</b>\n<code>{e}</code>"
#             )

# finally:
#     os.remove(PID_FILE)
