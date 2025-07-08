import json

from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context()

    page = context.new_page()
    page.goto("https://www.linkedin.com/login")

    print("👉 Please log in manually in the opened browser.")
    page.wait_for_timeout(30000)  # wait 30 sec

    # Save cookies
    cookies = context.cookies()
    with open("linkedin_cookies.json", "w") as f:
        json.dump(cookies, f)

    print("✅ Cookies saved to linkedin_cookies.json")

    browser.close()
