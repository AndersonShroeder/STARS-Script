import requests
import pandas as pd
from bs4 import BeautifulSoup
from scraper import Scraper
import streamlit as st
import time

# Constants for column names in the CSV file
DESCRIPTION_COLUMN_NAME = "description"
COURSE_URL_COLUMN_NAME = "url"
COURSE_EVAL_NAME = "categ"
COURSE_TITLE_NAME = "name"

class Processor:
    """
    A class to process course data, extracting descriptions and evaluating keywords 
    for sustainability and inclusivity assessments.
    """

    def __init__(self, course_data: pd.DataFrame, new_csv_path: str, keyword_path: str = None):
        """
        Initialize the Processor with course data and output file paths.

        :param course_data: DataFrame containing course information.
        :param new_csv_path: The file path for saving the processed data.
        :param keyword_path: Optional path to a text file containing keywords.
        """
        self.data = course_data
        self.new_csv_path = new_csv_path
        self.keyword_path = keyword_path
        self.keywords = set()

    def extract_text_path(self, url: str) -> str:
        """
        Extract the course description from the course webpage.

        :param url: The URL of the course page.
        :return: The course description text or an error message.
        """
        try:
            response = requests.get(url, allow_redirects=True, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            for i in range(9, 12):  # Adjust indices based on HTML structure
                target_div = soup.select_one(f'body > div > div:nth-child(6) > div:nth-child(2) > div > div:nth-child({i})')
                if self.check_description(target_div):
                    return target_div.get_text(strip=True)

            return ""
        except Exception as e:
            return f"An error occurred: {str(e)}"

    def check_description(self, text) -> bool:
        """
        Check if the given text is a valid course description.

        :param text: The text to check.
        :return: True if it's a description, False otherwise.
        """
        return text and text.get_text(strip=True).startswith("Description")

    def read_keyword_txt(self):
        """
        Read keywords from the specified text file and store them in a set.
        """
        if self.keyword_path:
            with open(self.keyword_path, "r") as file:
                for line in file:
                    self.keywords.add(line.lower().strip())

    def check_keywords(self) -> list:
        """
        Check for the presence of keywords in the course descriptions and titles.

        :return: List of assessment results based on keyword presence.
        """
        results_desc = []
        results_title = []
        
        # Check descriptions for keywords
        for desc in self.data[DESCRIPTION_COLUMN_NAME]:
            if pd.notna(desc):
                words = desc.lower().split()
                results_desc.append(1 if any(word in self.keywords for word in words) else 0)
            else:
                results_desc.append(0)

        # Check titles for keywords
        for title in self.data[COURSE_TITLE_NAME]:
            if pd.notna(title):
                words = title.lower().split()
                results_title.append(1 if any(word in self.keywords for word in words) else 0)
            else:
                results_title.append(0)

        # Combine results for evaluation
        results = []
        for d, t in zip(results_desc, results_title):
            if d == 1 and t == 1:
                results.append("2")
            elif d == 1 or t == 1:
                results.append("1")
            else:
                results.append("0")

        self.data[COURSE_EVAL_NAME] = results
        return results

    def output(self):
        """
        Save the processed data to a CSV file.
        """
        self.data.to_csv(self.new_csv_path, index=False)

    def run_keywords(self) -> list:
        """
        Execute the keyword checking process.

        :return: List of assessment results based on keyword presence.
        """
        self.read_keyword_txt()
        results = self.check_keywords()
        return results

    def run_description(self):
        """
        Extract descriptions for courses where the description is missing.
        """
        progress_text = "Fetching course descriptions, please wait."
        my_bar = st.progress(0, text=progress_text)
        for i in range(len(self.data)):
            my_bar.progress(i/len(self.data), text=progress_text)
            if pd.notna(self.data[COURSE_URL_COLUMN_NAME].iloc[i]) and pd.isna(self.data[DESCRIPTION_COLUMN_NAME].iloc[i]):
                text_content = self.extract_text_path(self.data[COURSE_URL_COLUMN_NAME].iloc[i])
                self.data.at[i, DESCRIPTION_COLUMN_NAME] = text_content if text_content else pd.NA
