import os


# check if an instance of a scraper is already active
def is_scraper_running():
    if os.path.exists("/tmp/scraper.pid"):
        try:
            with open("/tmp/scraper.pid", "r") as f:
                pid = int(f.read().strip())
            os.kill(pid, 0)  # Check if process exists
        except (ValueError, ProcessLookupError):
            return False  # PID file is stale
        return True
    return False
