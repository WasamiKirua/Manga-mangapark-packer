import os
import time
from utilities import URLValidator, fetch_chapters, process_chapters, download_image, create_cbz

def main():
    url_input = input("Enter the Mangaforfree URL: ")

    # Validate URL
    url_replacement = url_input.split('/')[-1]
    base_url = "https://mangapark.net/title/REPLACEMENT"
    url_validator = URLValidator(base_url)
    is_valid = url_validator.is_valid_url(url_replacement)


    # Run fetchers
    if is_valid:
        destination_folder = input("Destination's folder: ")
        print("\n")
        # Making dirs
        os.makedirs(f"{destination_folder}/chapters", exist_ok=True)
        os.makedirs(f"{destination_folder}/CBZ_files", exist_ok=True)
        chapters_list = fetch_chapters(url_input)
        # Processing Chapters
        for chapter_link in chapters_list:
            image_urls = process_chapters(chapter_link, main_dir=f"{destination_folder}/chapters")
            download_image(image_urls, chapter_link, main_dir=f"{destination_folder}/chapters")
        # Making CBZ
        create_cbz(main_dir=f"{destination_folder}/chapters", 
            cbz_folder=f"{destination_folder}/CBZ_files")
        
main()

