import requests
import sys
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
from g4f.client import Client
from g4f.Provider import RetryProvider, Phind, FreeChatgpt, Liaobots
import g4f.debug
import nest_asyncio

nest_asyncio.apply()
g4f.debug.logging = True

# Constants for column names in the CSV file
DESCRIPTION_COLUMN_NAME = "Description"
COURSE_URL_COLUMN_NAME = "Course URL"
COURSE_EVAL_NAME = "Assessment of Sustainability Focused or Inclusive"
COURSE_EVAL_REASON_NAME = "Justification for classification (including quotes from syllabi/course descriptions where applicable)"
COURSE_TITLE_NAME = "Course Title"

class Processor:
    def __init__(self, csv_path, new_csv_path, keyword_path=None):
        """
        Constructor for Processor class.

        Parameters:
        - csv_path (str): Path to the CSV file containing course data.
        - new_csv_path (str): Path to the new CSV file to save the processed data.
        - keyword_path (str): Path to a text file containing keywords for classification.
        """
        self.data = pd.read_csv(csv_path)
        self.csv_path = csv_path
        self.new_csv_path = new_csv_path
        self.keyword_path = keyword_path
        self.keywords = set()
        
    def extract_text_path(self, url):
        """
        Extract text content from the given URL.

        Parameters:
        - url (str): URL to extract text content from.

        Returns:
        - Text content extracted from the URL.
        """
        try:
            response = requests.get(url, allow_redirects=True, timeout=1)
            response.raise_for_status()  

            soup = BeautifulSoup(response.text, 'html.parser')

            for i in range(9, 12):
                target_div = soup.select_one(f'body > div > div:nth-child(6) > div:nth-child(2) > div > div:nth-child({i})')
                if self.check_description(target_div):
                    return target_div.text
                
            return ""

        except Exception as e:
            return f"An error occurred: {str(e)}"
        
    def check_description(self, text):
        """
        Check if the given text matches the description format.

        Parameters:
        - text (str): Text to check.

        Returns:
        - True if the text matches the description format, otherwise False.
        """
        if text:
            if text.text[:11] == "Description":
                return True
        else:
            return False
            
    def read_keyword_txt(self):
        """
        Read keywords from a text file and store them in a set.
        """
        keywords = set()
        with open(self.keyword_path, "r") as file:
            line = file.readline()
            while line:
                keywords.add(line.strip("\n"))
                line = file.readline()

        self.keywords = keywords
    
    def check_keywords(self):
        """
        Check if course descriptions contain any keywords.

        Returns:
        - List of results indicating whether keywords are found in descriptions.
        """
        results_desc = []
        results_title = []
        for desc in self.data[DESCRIPTION_COLUMN_NAME]:
            if not pd.isna(desc):
                words = desc.split()
                if any(word in self.keywords for word in words):
                    results_desc.append("1")
                else:
                    results_desc.append("0")
            else:
                results_desc.append("0")
            
        for title in self.data[COURSE_TITLE_NAME]:
            if not pd.isna(title):
                words = title.split()
                if any(word in self.keywords for word in words):
                    results_title.append("1")
                else:
                    results_title.append("0")
            else:
                results_title.append("0")
        
        desc_int = int("".join(x for x in results_desc), 2)
        title_int = int("".join(x for x in results_title), 2)

        focused = "{0:b}".format(desc_int & title_int)
        inclusive = "{0:b}".format(desc_int ^ title_int)
        print(focused)

        print()
        
        self.data[COURSE_EVAL_REASON_NAME] = [*focused]
        return results_desc
        
    def output(self):
        """
        Write processed data to a new CSV file.
        """
        self.data.to_csv(self.new_csv_path)

    def run_keywords(self):
        """
        Run keyword check on course descriptions.
        """
        self.read_keyword_txt()
        self.check_keywords()
        
    def run_description(self):
        """
        Extract course descriptions from URLs and populate the DataFrame.

        This method iterates over the DataFrame rows (limited to the first 100 in this implementation)
        and extracts course descriptions from URLs if they are available and if the description column 
        is empty. It uses the `extract_text_path` method to extract text content from URLs.

        """
        for i in range(len(self.data)):
            if not pd.isna(self.data[COURSE_URL_COLUMN_NAME][i]) and pd.isna(self.data[DESCRIPTION_COLUMN_NAME][i]):
                text_content = self.extract_text_path(self.data[COURSE_URL_COLUMN_NAME][i])
                if text_content:
                    self.data.loc[i, DESCRIPTION_COLUMN_NAME] = text_content
                else:
                    self.data.loc[i, DESCRIPTION_COLUMN_NAME] = pd.NA

def main(argv):
    """
    Main function for running the script.

    This function handles command-line arguments, initiates the Processor object, 
    runs data processing methods based on the provided arguments, and saves the 
    processed data to a new CSV file.

    Parameters:
    - argv (list): List of command-line arguments.

    """
    # The remaining elements of argv are the command-line arguments
    if len(argv) < 3 or len(argv) > 4:
        print("Usage: python scraper.py <csv_path> <new_file_name> <keywords_path (Optional)>")
        return

    # Process command-line arguments
    print("Reading Data...")
    p = Processor(*argv[1:])

    # print("Parsing Descriptions...")   
    # p.run_description()
    if p.keyword_path is not None:
        print("Parsing Keywords...")
        p.run_keywords()

    print("Saving Data...")
    p.output()

if __name__ == "__main__":
    # Pass sys.argv to the main function
    main(sys.argv)