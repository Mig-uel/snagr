import os
import sys

"""Prevents multiple instances of the scraper from running simultaneously."""

PID_FILE = "/tmp/scraper.pid"
def prevent_multiple_instances():
    if os.path.exists(PID_FILE):
        print("⛔ Scraper already running")
        sys.exit(1)

    with open(PID_FILE, "w") as f:
        f.write(str(os.getpid()))

    return PID_FILE