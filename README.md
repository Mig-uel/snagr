# Snagr - A LinkedIn Job Scraper

Snagr is a Python-based web scraping tool designed to extract job postings from LinkedIn. It utilizes the Playwright library for browser automation.

## Features

### Scraper

- Scrapes job postings from LinkedIn
- Filters jobs by location, job title, and company (soon)
- Requires a LinkedIn cookie for authentication
- Stores scraped data in a Supabase database

### Telegram Bot

- Provides a Telegram bot interface for interacting with the scraper
- Allows users to start the scraper and receive job postings directly in Telegram
- Supports various commands to control the scraper:
  - `/run` - Starts the bot and provides instructions
  - `/status` - Checks the status of the scraper
  - `/help` - Provides help information
  - More commands coming soon...

## To Do

- Implement job filtering by company
- Add more commands to the Telegram bot
- Improve error handling and logging
- Optimize scraping performance
- Add CSV export functionality
- Implement user authentication for the Telegram bot
- Add support for multiple job locations
- Enhance the user interface of the Telegram bot

## Installation

### Scraper Setup

1. Clone the repository:

```bash
   git clone https://github.com/mig-uel/snagr.git
   cd snagr
```

2. Create a virtual environment and activate it:

```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
```

3. Install the required dependencies:

```bash
  pip install -r requirements.txt
```

```bash
  python -m venv venv
  source venv/bin/activate  # On Windows use `venv\Scripts\activate`
```

4. Install the required dependencies:

```bash
  pip install -r requirements.txt
```

5. Set up environment variables:

- Create a `.env` file in the root directory and add your credentials as shown in the `.env.example` file.

6. Edit the source URL in `utils/constants.py` to match your LinkedIn job search URL.

```python
   # utils/constants.py
   LINKEDIN_JOBS_URL = "https://www.linkedin.com/jobs/search/?f_TPR=<SET_TIME_RANGE>&keywords=<YOUR_JOB_TITLE>&geoId=<YOUR_LOCATION_ID>"
```

Replace `YOUR_JOB_TITLE` and `YOUR_LOCATION` with your desired job title and location.

7. Run the application:

```bash
   python app.py
```

### Telegram Bot Setup

Installation information coming soon...

## Feedback and Contributions

We welcome feedback and contributions to Snagr! If you have suggestions, feature requests, or bug reports, please open an issue on the GitHub repository.
