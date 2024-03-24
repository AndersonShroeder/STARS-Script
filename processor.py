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
        self.client = None
        self.provider = None

    def init_GPT(self):
        """
        Initialize GPT (Generative Pre-trained Transformer) model for text completion.
        """
        provider = RetryProvider([FreeChatgpt, Liaobots], shuffle=False)
        client = Client(provider=provider)

        self.client, self.provider = client, provider

    def run_GPT(self, prompt):
        """
        Run GPT to generate responses based on the given prompt.

        Parameters:
        - prompt (str): Prompt for GPT model.

        Returns:
        - Response from the GPT model.
        """
        response = self.client.chat.completions.create(
            model="",
            messages=[{"role": "user", "content": f"{prompt}"}],
            provider=self.provider
        )

        return response

    def generate_prompts(self):
        """
        Generate prompts for GPT based on course descriptions.

        Returns:
        - List of prompts for GPT.
        """
        prompts = []
        for desc in self.data[DESCRIPTION_COLUMN_NAME]:
            prompt = f"""A course description is provided below:\n\n{desc}\n\nBased on this course description does this class promote sustainability? 
                        Please assess it with a 1 (sustainable) or 0 (not sustainable) and provide a one sentence explanation why.
                        The format should be 1 or 0: [Reason]"""
            prompts.append(prompt)

        return prompts
    
    def parse_response(self, response):
        """
        Parse response from GPT.

        Parameters:
        - response: Response from GPT model.

        Returns:
        - Eval and reason extracted from response.
        """
        evals, reasons = [], []
        for line in response.choices[0].message.content.split('\n'):
            i, j = line.split(': ', 1)
            evals.append(i)
            reasons.append(j)
        
        return evals, reasons

    def exponential_backoff(self, func, args, max_retries=5, base_delay=1, max_delay=32):
        """
        Execute a function with exponential backoff retry strategy.

        Parameters:
        - func: The function to execute.
        - args (list): Arguments to pass to the function.
        - max_retries (int): The maximum number of retries.
        - base_delay (float): The initial delay between retries in seconds.
        - max_delay (float): The maximum delay between retries in seconds.

        Returns:
        - Result of the function if successful.
        """
        retries = 0
        while True:
            try:
                return func(*args)
            except Exception as e:
                if retries >= max_retries:
                    raise e  # If max retries reached, raise the last exception
                retries += 1
                delay = min(max_delay, base_delay * (2 ** retries) + random.uniform(0, 1))
                print(f"Retrying in {delay:.2f} seconds (attempt {retries} of {max_retries})...")
                time.sleep(delay)
    
    def run_keywords_GPT(self):
        """
        Run GPT to evaluate course descriptions based on keywords.
        """
        evals, reasons = [], []
        prompts = self.generate_prompts()
        count = 50
        while count < len(prompts):
            response = self.exponential_backoff(self.run_GPT, [prompts[count-50:count]])
            eval, reason = self.parse_response(response)
            evals += eval
            reasons += reason
            count += 50
        
        self.data[COURSE_EVAL_REASON_NAME] = reasons
        self.data[COURSE_EVAL_NAME] = evals

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
        results = []
        for desc in self.data[DESCRIPTION_COLUMN_NAME]:
            if not pd.isna(desc):
                words = desc.split()
                if any(word in self.keywords for word in words):
                    results.append("Y")
                else:
                    results.append("N")
            else:
                results.append(False)
        
        self.data[COURSE_EVAL_REASON_NAME] = results
        return results
        
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

    print("Parsing Descriptions...")   
    p.run_description()

    if p.keyword_path == "GPT":
        print("Parsing Description With GPT...")
        p.init_GPT()
        p.run_keywords_GPT()
    elif p.keyword_path is not None:
        print("Parsing Keywords...")
        p.run_keywords()

    print("Saving Data...")
    p.output()

if __name__ == "__main__":
    # Pass sys.argv to the main function
    main(sys.argv)