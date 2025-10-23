import sys
import requests
from bs4 import BeautifulSoup as Soup
import os
import csv 
import urllib3
import logging

# Configure logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger(__name__)

# Turn off SSL certification warnings 〃(* ¯ ³¯)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Set constants for attributes from sitemap
ATTRS = ["loc", "lastmod", "priority"]

def parse_sitemap(url, csv_filename="urls.csv"):
    """Parse the sitemap at the given URL and add links to CSV file"""
    if not url:
        logger.error("No URL provided")
        return False
    
    logger.info(f"Fetching sitemap: {url}")
    try:
        response = requests.get(url, verify=False, timeout=15) # Do not verify SSL cert
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed for {url}: {e}")
        return False
    
    # Ensure response code is 200 "ok" (ദ്ദി ๑>؂•̀๑)
    if response.status_code !=200:
        logger.warning(f"Failed to fetch {url} (status {response.status_code})")
        return False
    
    # Parse response for extensible markup language (XML) data
    soup = Soup(response.content, "xml")

    # Recursively parse nested sitemaps
    sitemaps = soup.find_all("sitemap")
    if sitemaps:
        logger.info(f"Found {len(sitemaps)} nested sitemaps in {url}")
        for sitemap in sitemaps:
            loc = sitemap.find("loc")
            if loc and loc.text:
                parse_sitemap(loc.text, csv_filename)
    
    # Find all URLs in the sitemap
    urls = soup.find_all("url")
    logger.info(f"Found {len(urls)} URLs in {url}")

    if not urls:
        return False

    # Define root dir for CSV file
    root = os.path.dirname(os.path.abspath(__file__))
    # Check if the file exists
    file_path = os.path.join(root, csv_filename)
    file_exists = os.path.isfile(file_path)

    # Initialize new list ⊹₊⟡⋆
    rows = []
    for url_tag in urls:
        row = []
        for attr in ATTRS:
            found_attr = url_tag.find(attr)
            row.append(found_attr.text if found_attr else "n/a")
        rows.append(row)

    # Append the data ଘ( ੭˘͈ ᵕ ˘͈)੭* ✩
    try:
        with open(file_path, "a+", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            # Write the header only if the filed doesn't exist
            if not file_exists:
                writer.writerow(ATTRS)
            writer.writerows(rows)
        logger.info(f"Saved {len(rows)} URLs from {url}")
    except Exception as e:
        logger.error(f"Failed to write to {csv_filename}: {e}")

# Only run code inside this block if file is executed directly
if __name__ == "__main__":
    if len(sys.argv) < 2:
        logger.error(
            "Usage: uv run find_links.py <sitemap_url> [output_filename.csv]"
            )
        sys.exit(1)

    sitemap_url = sys.argv[1]
    csv_filename = sys.argv[2] if len(sys.argv) > 2 else "urls.csv"
    parse_sitemap(sitemap_url, csv_filename)