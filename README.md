# Course Description Processor

This repository contains a Python script for processing course descriptions stored in a CSV file. It extracts descriptions from URLs, evaluates them using GPT-3 or keyword-based approaches, and saves the processed data to a new CSV file.

## Features

- Extracts course descriptions from URLs.
- Evaluates course descriptions for sustainability focus or inclusivity.
- Supports GPT-3-based evaluation or keyword-based evaluation.
- Exponential backoff for retrying failed operations.
- Command-line interface for easy usage.

## Dependencies

- Python 3.x
- Libraries:
  - pandas
  - requests
  - beautifulsoup4
  - g4f (GPT-3 client)
  - nest_asyncio

## Usage

1. Clone the repository to your local machine:

   ```bash
   git clone https://github.com/your-username/course-description-processor.git
   ```

2. Install the required dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Prepare your input CSV file with course data. The CSV file should contain at least two columns: one for course descriptions and another for course URLs.

4. Run the script with the following command:

   ```bash
   python processor.py <csv_path> <new_file_name>
   ```

   Replace `<csv_path>` with the path to your input CSV file and `<new_file_name>` with the desired name for the output CSV file.

5. Follow the prompts to choose the evaluation method (GPT-3 or keyword-based).

6. Once the script finishes processing, you'll find the processed data saved in the specified output CSV file.

## Command-line Arguments

- `<csv_path>`: Path to the input CSV file containing course data.
- `<new_file_name>`: Name for the output CSV file with processed data.

## Contributing

Contributions are welcome! If you find any issues or have suggestions for improvements, please open an issue or submit a pull request.

## License

This project is licensed under the [MIT License](LICENSE).
