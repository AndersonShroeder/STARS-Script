import requests
import sys
from bs4 import BeautifulSoup
import pandas as pd

DESCRIPTION_COLUMN_NAME = "Description"
COURSE_URL_COLUMN_NAME = "Course URL"

class Processor:
    def __init__(self, csv_path, new_csv_path, keyword_path = None):
        self.data = pd.read_csv(csv_path)
        self.csv_path = csv_path
        self.new_csv_path = new_csv_path
        self.keyword_path = keyword_path
        self.keywords = set()

    def extract_text_path(self, url):
        try:
            # Send a GET request to the URL with following redirects
            response = requests.get(url, allow_redirects=True, timeout=1)
            response.raise_for_status()  # Raise an exception for bad responses

            # Parse the HTML content
            soup = BeautifulSoup(response.text, 'html.parser')

            # Use the selector path to find the desired div
            for i in range(9, 12):
                target_div = soup.select_one(f'body > div > div:nth-child(6) > div:nth-child(2) > div > div:nth-child({i})')
                if self.check_description(target_div):
                    return target_div.text
                
            return ""

        except Exception as e:
            return f"An error occurred: {str(e)}"
        
    def check_description(self, text):
        # Check if the div is found
            if text:
                if text.text[:11] == "Description":
                    return True
            else:
                return False
            
    def read_keyword_txt(self):
        keywords = set()
        with open(self.keyword_path, "r") as file:
            line = file.readline()
            while line:
                keywords.add(line.strip("\n"))
                line = file.readline()

        self.keywords = keywords
    
    def check_keywords(self):
        # Convert keywords list to a set for faster lookup
        results = []
        for description in self.data[DESCRIPTION_COLUMN_NAME]:
            # Split description into words
            if not pd.isna(description):
                words = description.split()
                # Check if any word in the description is in the set of keywords
                if any(word in self.keywords for word in words):
                    results.append("Y")
                else:
                    results.append("N")
            else:
                results.append(False)
        
        self.data["Assessment of Sustainability Focused or Inclusive"] = results
        return results
        
    def output(self):
        self.data.to_csv(self.new_csv_path)

    def run_keywords(self):
        self.read_keyword_txt()
        self.check_keywords()

    def run_description(self):
        for i in range(len(self.data[:100])):
            if not pd.isna(self.data[COURSE_URL_COLUMN_NAME][i]) and pd.isna(self.data[DESCRIPTION_COLUMN_NAME][i]):
                text_content = self.extract_text_path(self.data[COURSE_URL_COLUMN_NAME][i])
                if text_content:
                    self.data.loc[i, DESCRIPTION_COLUMN_NAME] = text_content

                else:
                    self.data.loc[i, DESCRIPTION_COLUMN_NAME] = pd.NA

def main(argv):
    # The remaining elements of argv are the command-line arguments
    if len(argv) < 3 or len(argv) > 4:
        print("Usage: python scraper.py <csv_path> <new_file_name>")
        return

    # Process command-line arguments
    print("Reading Data...")
    p = Processor(*argv[1:])

    print("Parsing Descriptions...")
    p.run_description()

    if p.keyword_path == "GPT":
        print("Parsing Description With GPT...")
    elif p.keyword_path != None:
        print("Parsing Keywords...")
        p.run_keywords()

    print("Saving Data...")
    p.output()

if __name__ == "__main__":
    # Pass sys.argv to the main function
    main(sys.argv)