import os

from dotenv import load_dotenv

load_dotenv(override=True)

# LinkedIn Job Search URL
SOURCE_URL = "https://www.linkedin.com/jobs/search/?f_TPR=r3600&keywords=software%20developer&geoId=103644278&origin=JOB_SEARCH_PAGE_JOB_FILTER"

# Headless mode varies depending on environment
HEADLESS = os.getenv("HEADLESS", "True") == "True"
