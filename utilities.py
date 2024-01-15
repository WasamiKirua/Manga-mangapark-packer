from urllib.parse import urlparse
#from playwright.async_api import async_playwright
from playwright.sync_api import sync_playwright
from selectolax.parser import HTMLParser
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from io import BytesIO
from PIL import Image
import requests
import time
import os
import requests
import zipfile

class URLValidator:
    """
    A class to validate URLs with a replaceable part.
    """
    def __init__(self, base_url):
        """
        Initializes the URLValidator with a base URL.
        """
        self.base_url = base_url

    def is_valid_url(self, replacement):
        """
        Checks if the URL with the replacement is valid.
        """

        # Replace 'REPLACEMENT' in the base URL with the actual replacement value
        url_with_replacement = self.base_url.replace('REPLACEMENT', replacement)

        # Parse the URL and validate the scheme and netloc (domain)
        parsed_url = urlparse(url_with_replacement)
        return all([parsed_url.scheme, parsed_url.netloc])

def setup_driver():
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")  # Run headless Chrome
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def fetch_chapters(url, retries=5):
    attempt = 0
    while attempt < retries:
        try:
            with sync_playwright() as p:
                print(f"Fathing Chapter: {url} ... Attempt {attempt + 1}")
                print("\n")
                # Launch the browser (Chromium, Firefox, or WebKit)
                browser = p.chromium.launch()
                page = browser.new_page()
                # Go to the webpage
                page.goto(url)
                time.sleep(2)
                # Get the page content
                content = page.content()
                # Parse the HTML
                tree = HTMLParser(content)
        
                chapter_list = []

                for chapter in tree.css('div.space-x-1'):
                    for a_tag in chapter.css('a'):
                        href = a_tag.attributes.get('href')
                        chapter_list.append(href)

                browser.close()
                return chapter_list
        except Exception as e:
            print(f"An error occurred: {e}. Retrying in 5 seconds...")
            print("\n")
            time.sleep(2)
            attempt += 1
    print("Failed to fetch chapters after several attempts.")
    print("\n")
    return []

def download_image(image_urls, chapter_link, main_dir, retries=5):
    # Check if chapter_link is None
    if chapter_link is None:
        print("No chapter link provided. Skipping image download.")
        return None
    
    chapter = chapter_link.split('/')[-1]
    destination_dir = os.path.join(main_dir, chapter)
    
    if os.path.exists(destination_dir):
        print(f"Chapter folder {destination_dir} already exists. Skipping download.")
        return None
    
    print(f"Processing download of {main_dir}{chapter}, total of {len(image_urls)}")
    print("\n")
    
    for index, img in enumerate(image_urls, start=1):
        attempt = 0
        while attempt < retries:
            try:
                response = requests.get(img)
                if response.status_code == 200:
                    with Image.open(BytesIO(response.content)) as img_file:
                        img_file.save(f"{destination_dir}/image_{index}.jpg")
                        print(f"Image saved as {destination_dir}/image_{index}.jpg")
                        time.sleep(2)
                        break  # Exit the while loop if the image is saved successfully
                else:
                    print(f"Failed to download image. HTTP status code: {response.status_code}")
                    attempt += 1
                    time.sleep(3)
            except Exception as e:
                print(f"An error occurred while downloading the image: {e}")
                attempt += 1
                time.sleep(3)

        if attempt == retries:
            print(f"Failed to download image after {retries} attempts: {img}")

def process_chapters(chapter_link, main_dir, retries=5):
    # Check if chapter_link is None
    if chapter_link is None:
        print("No chapter link provided. Skipping processing.")
        return None
    
    # Making destination folder
    chapter_folder = chapter_link.split('/')[-1]
    folder_path = f"{main_dir}/{chapter_folder}"

    # Check if the directory already exists
    if os.path.exists(folder_path):
        print(f"Chapter folder {folder_path} already exists. Skipping processing.")
        return None
    
    attempt = 0
    while attempt < retries:
        try:
            print(f"Processing Chapter: https://mangapark.net{chapter_link}")
            print("\n")
            url = f"https://mangapark.net{chapter_link}"

            # Create the directory since it doesn't exist
            os.makedirs(folder_path, exist_ok=True)

            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)  # Using headless mode
                page = browser.new_page()
                page.goto(url)
                time.sleep(7)  # Allow time for the page to load

                # Use Selectolax to parse the HTML content
                html_content = page.content()
                tree = HTMLParser(html_content)
                image_tags = tree.css('div.cursor-pointer img')
                image_urls = [img.attrs['src'] for img in image_tags]
                # Closing browser
                browser.close()
            return image_urls
        except Exception as e:
            print(f"An error occurred: {e}. Retrying in 5 seconds...")
            print("\n")
            time.sleep(5)
            attempt += 1

    print(f"Failed to process chapter {chapter_link} after several attempts.")
    print("\n")

def create_cbz(main_dir, cbz_folder):
    # Initialize a dictionary to hold the file names for each subfolder
    subfolder_files = {}

    # Check if the base folder exists
    if os.path.exists(main_dir) and os.path.isdir(main_dir):
        # List all entries in the base folder
        entries = os.listdir(main_dir)
        # Filter out subfolders and sort them
        subfolders = [entry for entry in entries]
        # Sorting the chapters numerically
    else:
        print(f"Error: destination folder '{main_dir}' does not exists")
    for chapter in subfolders:
        chapter_path = os.path.join(main_dir, chapter)
        if os.path.isdir(chapter_path):
            # List files in the chapter folder
            chapter_files = os.listdir(chapter_path)
            # Sorting the files numerically (assuming filenames are numeric or have numeric prefixes)
            sorted_files = sorted(chapter_files, key=lambda x: int(x.split('_')[1].split('.')[0]))
            subfolder_files[chapter] = sorted_files
    for chapter, files in subfolder_files.items():
        # Create the path for the CBZ file
        cbz_file_path = os.path.join(cbz_folder, f"{chapter}.cbz")

        # Create a ZIP file
        with zipfile.ZipFile(cbz_file_path, 'w') as zipf:
            for file in files:
                # Add each JPG file to the ZIP archive
                zipf.write(os.path.join(main_dir, chapter, file), file)