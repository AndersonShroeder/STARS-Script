import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np

class Scraper:
    """
    A class to scrape course data from the Rice University Course Catalog, 
    extract URLs, course names, and split the course names into Subject Code and Course Number.
    """

    def __init__(self, base_url):
        """
        Initialize the Scraper with the base URL of the course catalog.

        :param base_url: The URL of the Rice University Course Catalog page.
        """
        self.base_url = base_url
        self.course_data = []

    def fetch_page(self):
        """
        Fetch the HTML content of the course catalog page.

        :return: Parsed HTML content of the page.
        """
        response = requests.get(self.base_url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            return soup
        else:
            raise Exception(f"Failed to fetch page with status code {response.status_code}")

    def extract_courses(self, soup):
        """
        Extract course details such as course URL, course name, subject code, and course number.

        :param soup: Parsed HTML content.
        :return: List of dictionaries with course URL, name, subject code, and course number.
        """
        courses = []
        # Find all table rows that contain course information
        rows = soup.find_all('tr')

        for row in rows:
            # Find the cell containing the course link
            course_cell = row.find('td', class_='cataCourse')
            if course_cell:
                # Extract the course URL and full course name (e.g., "ARCH 645")
                course_link = course_cell.find('a')
                if course_link:
                    href = course_link['href']
                    full_course_name = course_link.get_text(strip=True)

                    # Split the course name into Subject Code (e.g., "ARCH") and Course Number (e.g., "645")
                    subject_code, course_number = self.split_course_name(full_course_name)

                    courses.append({
                        'name': full_course_name,
                        'department': subject_code,
                        'number': course_number,
                        'categ': np.nan,
                        'url': f"https://courses.rice.edu{href}",
                        'description': np.nan,
                    })
        
        self.course_data = courses
        
        return courses

    def split_course_name(self, full_course_name):
        """
        Split the full course name into Subject Code and Course Number.

        :param full_course_name: The full course name, e.g., "ARCH 645".
        :return: A tuple containing the Subject Code and Course Number.
        """
        parts = full_course_name.split()
        subject_code = parts[0]  # The first part is the subject code
        course_number = parts[1]  # The second part is the course number
        return subject_code, course_number

    def to_dataframe(self):
        """
        Convert the course data into a Pandas DataFrame.

        :return: Pandas DataFrame containing the course data.
        """
        if not self.course_data:
            raise Exception("No course data to convert. Please run extract_courses() first.")
        
        return pd.DataFrame(self.course_data)

    def save_to_csv(self, file_name):
        """
        Save the extracted course data to a CSV file.

        :param file_name: The name of the CSV file to save the data to.
        """
        df = self.to_dataframe()
        df.to_csv(file_name, index=False)

