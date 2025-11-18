import os
import sys
import logging

"""Prevents multiple instances of the scraper from running simultaneously."""

def prevent_multiple_instances():
    PID_FILE = "/tmp/scraper.pid"

    if os.path.exists(PID_FILE):
        logging.critical("Instance Already Exists")
        sys.exit(1)

    with open(PID_FILE, "w") as f:
        f.write(str(os.getpid()))

    return PID_FILE