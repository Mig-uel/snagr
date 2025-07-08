import os

from dotenv import load_dotenv

load_dotenv(override=True)

SOURCE_URL = "https://www.linkedin.com/jobs/search/?f_TPR=r3600&keywords=software%20developer&geoId=103644278&origin=JOB_SEARCH_PAGE_JOB_FILTER"  # LinkedIn Job Search Source URL


IS_HEADLESS = os.getenv("HEADLESS", "True") == "True"  # Varies depending on environment
