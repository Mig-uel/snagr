from urllib.parse import urlparse


def normalize_job_link(url):
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
