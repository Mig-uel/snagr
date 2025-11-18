from urllib.parse import urlparse

def normalize_job_link(url):
    if not url:
        return None
    
    url = f"https://linkedin.com{url}" if url.startswith("/") else url
    parsed = urlparse(url)

    # Remove query parameters and fragments
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"