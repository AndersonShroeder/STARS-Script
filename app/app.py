import streamlit as st
import os
from scraper import Scraper  # Ensure this matches your script's filename
from processor import Processor
import pandas as pd

# Ensure necessary directories exist
os.makedirs('uploads', exist_ok=True)
os.makedirs('results', exist_ok=True)

def get_url(year):
    return f'https://courses.rice.edu/courses/!SWKSCAT.cat?p_action=CATALIST&p_acyr_code={year}'

def main():
    st.title("Course Data Processor")
    st.write("Input the catalog year to parse the course data.")

    # Input for catalog year
    catalog_year = st.text_input("Catalog Year (e.g., 2025)", "2025")

    new_csv_name = st.text_input("New CSV File Name", "processed_courses.csv")
    keyword_file = st.file_uploader("Upload Keywords File", type=["txt"])

    if st.button("Process"):
        if not catalog_year.isdigit() or len(catalog_year) != 4:
            st.error("Please enter a valid 4-digit catalog year.")
            return
        if not keyword_file:
            st.error("Must provide keywords for sustainability matching.")
            return
        if not new_csv_name.endswith('.csv'):
            st.error("New CSV file name must end with '.csv'.")
            return

        with st.spinner("Processing data..."):
            try:
                new_csv_path = os.path.join("results", new_csv_name)
                keyword_path = os.path.join("uploads", keyword_file.name)
                with open(keyword_path, "wb") as f:
                    f.write(keyword_file.getbuffer())

                # Create Scraper instance and generate CSV
                scraper = Scraper(get_url(catalog_year))
                soup = scraper.fetch_page()
                courses = scraper.extract_courses(soup)

                st.success(f"Scraped {len(courses)} courses from course catalog!")

                processor = Processor(course_data=pd.DataFrame(courses), new_csv_path=new_csv_path, keyword_path=keyword_path)
                processor.run_description()  # Extract missing descriptions
                results = processor.run_keywords()  # Check for keywords

                st.success("Processing Complete!")

                # Write stats
                st.write(f"**Count of '2':** {results.count('2')}")
                st.write(f"**Count of '1':** {results.count('1')}")

            except Exception as e:
                st.error(f"An error occurred during processing: {e}")
                return

        # Provide download button for the new CSV
        if os.path.exists(new_csv_path):
            with open(new_csv_path, "rb") as f:
                st.download_button(
                    label="Download Processed CSV",
                    data=f,
                    file_name=new_csv_name,
                    mime="text/csv"
                )
        else:
            st.error("Processed CSV file not found.")

if __name__ == "__main__":
    main()
