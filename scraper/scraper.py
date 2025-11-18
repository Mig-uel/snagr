import json
import math
from datetime import datetime
import os
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
    prevent_multiple_instances,
)

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

seen_links = set()

async def main():
    try:
        # Prevent multiple instances
        PID_FILE = prevent_multiple_instances()

        # Get Supabase client
        supabase = get_supabase()

        # Fetch existing links from database
        existing_links = get_existing_job_links()

        # Get parent directory (scraper)
        parent_dir = Path(__file__).resolve().parent 

        # Get cookies file path
        cookies_file_path = Path.joinpath(parent_dir, "linkedin_cookies.json")

        # Get OS
        IS_RPI = os.uname().machine.startswith("arm") or os.uname().machine.startswith("aarch64")

        async with async_playwright() as p:
            if IS_RPI:
                logger.info("Running on Raspberry Pi OS")
                browser = await p.chromium.launch(executable_path="/usr/bin/chromium", headless=IS_HEADLESS)
            else:
                browser = await p.chromium.launch(headless=IS_HEADLESS)
            context = await browser.new_context(viewport={"width": 1400, "height": 3500})

            # Add cookies to context
            with open(cookies_file_path, "r") as f:
                cookies = json.load(f)
                await context.add_cookies(cookies)
            
            page = await context.new_page()
            await page.goto(SOURCE_URL)

            # Debug: print page title
            print(await page.title())

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
            skipped_links = 0
            blacklisted_links = 0

            # Outer pagination loop for pages
            while True:
                # Send current page message
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

                            # Skip if link already in database or seen
                            if parsed_linkedin_url in existing_links:
                                skipped_links += 1
                                logging.info("Link Already in Database")
                                continue
                            if parsed_linkedin_url in seen_links:
                                skipped_links += 1
                                logging.info("Link Already Parsed")
                                continue

                            # Append job details to jobs list
                            jobs.append(
                                {
                                    "title": title,
                                    "company": company,
                                    "location": None,
                                    "job_link": parsed_linkedin_url,
                                }
                            )

                            # Mark link as seen
                            seen_links.add(parsed_linkedin_url)

                            # Send Telegram message for new job
                            send_telegram_message(
                                title=title, company=company, href=parsed_linkedin_url
                            )

                            # Throttle requests
                            await asyncio.sleep(.2)
                        except Exception as e:
                            logging.error(f"Error Extracting Job Details: {e}")
                            continue

                    # Find and click the next button
                    next_btn = page.locator('button[aria-label="View next page"]')

                    if await next_btn.is_visible() and not await next_btn.is_disabled():
                        await next_btn.click()
                        current_page += 1
                        await page.wait_for_timeout(2000)  # Wait for 2 seconds before processing next page
                    else:
                        logging.info("Reached Last Page")
                        break
                except Exception as e:
                    logging.critical(f"Scraper Failed: {e}")
                    send_telegram_message(f"⚠️ | <b>Scraper failed:</b>\n<code>{e}</code>")
                    raise

            await context.close()
            await browser.close()

            # Insert jobs into Supabase
            await insert_jobs_into_db(supabase, jobs, total_jobs, skipped_links, blacklisted_links)
    except Exception as e:
        logging.critical(f"⚠️ | Error initializing scraper: {e}")
        return
    finally:
        # Remove PID file if it exists
        os.remove(PID_FILE) 

async def insert_jobs_into_db(supabase, jobs, total_jobs, skipped_links, blacklisted_links):
        try:
            if jobs:
                supabase.table("jobs").insert(jobs).execute()
                send_telegram_message(
                    f"🟢 | <b>Scraper finished!</b>\n\nTotal Jobs Found: {total_jobs}\nJobs Collected: {len(jobs)}\nJobs Skipped: {skipped_links}\nBlacklisted Jobs: {blacklisted_links}"
                )
                logger.info(f"Inserted {len(jobs)} new jobs into the database.")
            else:
                send_telegram_message(
                    f"⚪ | <b>No new jobs to insert.</b>\nTotal Jobs Found: {total_jobs}"
                )
                logger.info("No new jobs to insert.")
        except Exception as e:
            logger.error(f"Supabase insertion failed: {e}")
            send_telegram_message(
                f"⚠️ | <b>Supabase insertion failed:</b>\n<code>{e}</code>"
            )

if __name__ == "__main__":
    asyncio.run(main())


#         # TODO: work on detecting cookie expiration
#         # if "login" in page.url:
#         #     send_telegram_message(
#         #         "⚠️ <b>LinkedIn session expired. Please upload a new cookie.</b>"
#         #     )
#         #     raise Exception("⚠️ <b>Session Expired</b>")