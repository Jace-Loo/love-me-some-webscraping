# Import dependencies
import csv
import pandas as pd
# import time
import sys
import re
import os
import logging
from playwright.sync_api import sync_playwright
from concurrent.futures import ThreadPoolExecutor

# Configure logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger(__name__)

# Create folders for screenshots and article text
SCREENSHOTS_DIR = "screenshots"
ARTICLES_DIR = "articles"
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
os.makedirs(ARTICLES_DIR, exist_ok=True)

# Run process and either save articles, take a screenshot of articles, or create a dataframe
def run(playwright, url, take_screenshot, to_dataframe, data_list=None):
    browser = playwright.chromium.launch(headless=True)
    page = browser.new_page()
    
    logger.info(f"Navigating to {url}")
    page.goto(url)
    
    if take_screenshot:
        __capture_screenshot(page, url)
        if to_dataframe and data_list is not None:
            # Get title, and URL for data frame but no text
            data_list.append({
                "url": url,
                "title": page.title(),
                "text": None,
                "screenshot": True
            })
    else:
        if to_dataframe and data_list is not None:
            # Get article title, url, and body text
            title = page.title()
            main_content = page.query_selector("body")
            main_text = main_content.inner_text() if main_content else "Not found"
            data_list.append({
                "url": url,
                "title": title,
                "text": main_text,
                "screenshot": False
            })
        else:
            __save_page_text(page, "body", url)
    
    browser.close()
    logger.info("browser closed")

def process_url(url, take_screenshot, to_dataframe=False, data_list=None):
    with sync_playwright() as playwright:
        run(playwright, url, take_screenshot, to_dataframe, data_list)

# Save URL title and body text
def __save_page_text(page, selector, url):
    title = page.title()
    main_content = page.query_selector(selector)
    main_text = (
        main_content.inner_text() if main_content else "Not found"
        )

    filename = __safe_filename_from(title)
    filepath= os.path.join(ARTICLES_DIR, filename)

    # Write the page title and text to a file named with page title
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"URL: {url}\n")
        f.write(f"Title: {title}\n\n")
        f.write(main_text)

    logger.info(f"Data saved as {filepath}")

# Save the URL content with a safe filename
def __safe_filename_from(title):
    safe_title = re.sub(r"[^\w\s-]", "", title).strip().replace(" ", "_")
    return f"{safe_title}.txt"

# Take a screenshot /[◉"]＼_・)
def __capture_screenshot(page, url):
    filename = __safe_filename_for_screenshot(page.title()) + ".png"
    filepath = os.path.join(SCREENSHOTS_DIR, filename)
    page.screenshot(path=filepath, full_page=True)
    logger.info(f"Screenshot saved as {filepath} for {url}")

# save screenshot with a safe filename
def __safe_filename_for_screenshot(title):
    safe_title = re.sub(r"[^\w\s-]", "", title).strip().replace(" ", "_")
    return f"{safe_title}.png"

# Read links from csv
def __read_urls_from_csv(file_path):
    urls = []
    try:
        with open(file_path, newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                urls.append(row["loc"])
        logger.info(f"Read {len(urls)} URLS from {file_path}")
    except Exception as e:
        logger.error(f"Failed to read URLs from {file_path}: {e}")
    return urls

# Only run code inside this block if file is executed directly
if __name__ == "__main__":
    # Check for csv
    if len(sys.argv) < 2:
        logger.error("Usage: python main.py <csv_file> [--screenshot] [--to_dataframe]")
        sys.exit(1) # Exit if not csv

    csv_file = sys.argv[1] # Get csv
    take_screenshot = '--screenshot' in sys.argv # Check for screenshot flag
    to_dataframe = '--to_dataframe' in sys.argv # Check for df flag

    urls = __read_urls_from_csv(csv_file)
    urls = urls[2:15] # Only process like 12, to keep things easy

    data_list = [] if to_dataframe else None

    # Run parallel ৻(•̀ᗜ•́ ৻)
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(process_url, url, take_screenshot, to_dataframe, data_list) for url in urls]
        for future in futures:
            try:
                future.result()
            except Exception as e:
                logger.error(f"Error processing URL: {e}")

if to_dataframe:
    df = pd.DataFrame(data_list)
    output_file = "article_text.csv"
    df.to_csv(output_file, index=False)
    logger.info(f"Data saved to {output_file}")

    # print(df)

"""
      ♡  ╱|、
        (˚.。7  
        |、˜〵          
        じしˍ,)ノ
"""