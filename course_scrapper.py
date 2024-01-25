import requests
from bs4 import BeautifulSoup

def extract_text_from_website(url, parent_class='col-lg-12 course', child_element='div'):
    try:
        # Send a GET request to the URL with following redirects
        response = requests.get(url, allow_redirects=True, timeout=1)
        response.raise_for_status()  # Raise an exception for bad responses

        # Parse the HTML content
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find the parent div with the specified class
        parent_div = soup.find('div', class_=parent_class)

        # If the parent div is found, find the child divs (classless) and extract text
        if parent_div:
            child_divs = parent_div.find_all(child_element, class_=False)
            text_data = '\n'.join([child_div.get_text() for child_div in child_divs])
            return text_data.split('\n')[-1]
        else:
            return "Parent div not found."

    except Exception as e:
        return f"An error occurred: {str(e)}"

# # Example usage
# database_url = 'https://courses.rice.edu/courses/courses/!SWKSCAT.cat?p_action=CATALIST&p_acyr_code=2022&p_crse_numb=299&p_subj=ASIA'
# text_content = extract_text_from_website(database_url, parent_class='col-lg-12 course', child_element='div')

# print(text_content)
