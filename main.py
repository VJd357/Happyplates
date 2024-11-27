import fitz  # PyMuPDF
import os
import base64
import json
import pandas as pd
from openai import OpenAI, OpenAIError
import yaml
import streamlit as st
from prompt import MenuPrompt
import logging

# Configure logging
logging.basicConfig(filename='process_log.log', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

class PDFProcessor:
    def __init__(self, pdf_path):
        """
        Initialize the PDFProcessor with the path to a PDF file.

        Parameters:
        - pdf_path (str): The file path to the PDF document.

        Attributes:
        - base_name (str): The base name of the PDF file without extension and spaces replaced by underscores.
        - output_folder (str): The folder name where screenshots will be saved.
        """
        self.pdf_path = pdf_path
        self.base_name = os.path.splitext(os.path.basename(pdf_path))[0].replace(" ", "_")
        self.output_folder = self.base_name

    def take_screenshots_of_menu_sections(self):
        """
        Take screenshots of each page in the PDF and save them as PNG files.

        Returns:
        - str: The path to the folder containing the screenshots if successful.
        - None: If an error occurs during processing.
        """
        try:
            if not os.path.exists(self.output_folder):
                os.makedirs(self.output_folder)
            
            document = fitz.open(self.pdf_path)
            for page_num in range(document.page_count):
                page = document.load_page(page_num)
                pix = page.get_pixmap()
                output_path = f"{self.output_folder}/menu_section_page_{page_num + 1}.png"
                pix.save(output_path)
            document.close()
            return self.output_folder
        except Exception as e:
            print(f"An error occurred: {e}")
            return None

class OpenAIClient:
    def __init__(self, api_key):
        """
        Initialize the OpenAIClient with an API key.

        Parameters:
        - api_key (str): The API key for authenticating with the OpenAI service.

        Attributes:
        - client (OpenAI): The OpenAI client instance for making API requests.
        """
        self.client = OpenAI(api_key=api_key)

    def process_image(self, image_path, prompt_full_menu):
        """
        Process an image by sending it to the OpenAI API along with a text prompt.

        Parameters:
        - image_path (str): The file path to the image to be processed.
        - prompt_full_menu (str): The text prompt to be sent to the OpenAI API.

        Returns:
        - pd.DataFrame: A DataFrame containing the processed menu data if successful.
        - None: If an error occurs during processing or if the response is empty.
        """
        base64_image = self.encode_image(image_path)
        try:
            # Log the request details
            logging.info(f"Sending request to OpenAI API with prompt: {prompt_full_menu} and image: {image_path}")

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt_full_menu,
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                },
                            },
                        ],
                    }
                ],
            )

            # Log the full response content
            response_content = response.choices[0].message.content
            logging.info(f"Received response content: {response_content}")

            # Check if response_content is empty
            if not response_content:
                logging.error("Received empty response content from OpenAI API.")
                return None

            json_start = response_content.find('```json') + len('```json')
            json_end = response_content.rfind('```')
            json_string = response_content[json_start:json_end].strip()

            # Check if json_string is empty
            if not json_string:
                logging.error("Extracted JSON string is empty. Check if the response format has changed.")
                return None

            menu_data = json.loads(json_string)
            menu_df = pd.json_normalize(menu_data, record_path=['items'], meta=['item_type'])

            # Log the JSON content and DataFrame
            logging.info(f"JSON content: {json_string}")
            logging.info(f"DataFrame: {menu_df}")

            return menu_df
        except OpenAIError as e:
            logging.error(f"OpenAIError occurred: {e}")
            return None
        except json.JSONDecodeError as e:
            logging.error(f"JSONDecodeError: {e} - JSON string: {json_string}")
            return None

    @staticmethod
    def encode_image(image_path):
        """
        Encode an image file to a base64 string.

        Parameters:
        - image_path (str): The file path to the image to be encoded.

        Returns:
        - str: The base64 encoded string of the image.
        """
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

class CSVProcessor:
    @staticmethod
    def process_images_in_folder(path, prompt_full_menu, client, progress_bar, progress_text):
        """
        Process all images in a folder, convert them to CSV files, and update progress.

        Parameters:
        - path (str): The directory path containing images to be processed.
        - prompt_full_menu (str): The text prompt to be sent to the OpenAI API.
        - client (OpenAIClient): The OpenAI client instance for processing images.
        - progress_bar (streamlit.progress): The Streamlit progress bar to update.
        - progress_text (streamlit.empty): The Streamlit text element to update with progress.

        Returns:
        - str: The path to the folder containing the CSV files.
        """
        output_folder = f"{os.path.basename(path)}_output"
        os.makedirs(output_folder, exist_ok=True)
        
        image_files = [f for f in os.listdir(path) if f.endswith(('.png', '.jpg', '.jpeg'))]
        total_files = len(image_files)
        
        for i, filename in enumerate(image_files):
            image_path = os.path.join(path, filename)
            menu_df = client.process_image(image_path, prompt_full_menu)
            if menu_df is not None:
                csv_filename = os.path.splitext(filename)[0] + '.csv'
                csv_path = os.path.join(output_folder, csv_filename)
                menu_df.to_csv(csv_path, index=False)
                print(f"Saved CSV for {filename} to {csv_path}")
            
            # Update progress bar
            progress_bar.progress((i + 1) / total_files)
            progress_text.text(f"Processing {i + 1} of {total_files} images")
        
        return output_folder

    @staticmethod
    def combine_csvs(output_folder):
        """
        Combine all CSV files in a folder into a single DataFrame and save it.

        Parameters:
        - output_folder (str): The directory path containing CSV files to be combined.

        Returns:
        - pd.DataFrame: The combined DataFrame from all CSV files.
        - str: The file path to the combined CSV file.
        """
        combined_df = pd.DataFrame()
        for filename in os.listdir(output_folder):
            if filename.endswith('.csv'):
                csv_path = os.path.join(output_folder, filename)
                df = pd.read_csv(csv_path)
                combined_df = pd.concat([combined_df, df], ignore_index=True)
        combined_csv_path = f"{output_folder}.csv"
        combined_df.to_csv(combined_csv_path, index=False)
        return combined_df, combined_csv_path

def main():
    """
    Main function to run the Streamlit app for converting menu PDFs to CSV files.

    Functionality:
    - Upload a PDF file.
    - Enter an OpenAI API key.
    - Process the PDF to extract menu sections as images.
    - Send images to OpenAI API for processing.
    - Convert processed data to CSV and display/download the result.
    """
    st.title("Menu PDF to CSV Converter")
    uploaded_file = st.file_uploader("Upload a PDF file", type="pdf")
    api_key = st.text_input("Enter your OpenAI API key", type="password")
    
    if uploaded_file is not None and api_key:
        if st.button("Submit"):
            # Save the uploaded file to a relative path
            pdf_name = uploaded_file.name
            pdf_path = os.path.join("uploads", pdf_name)
            os.makedirs("uploads", exist_ok=True)
            with open(pdf_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            pdf_processor = PDFProcessor(pdf_path)
            path = pdf_processor.take_screenshots_of_menu_sections()
            
            if path is None:
                st.error("Failed to process the PDF. Please check the file and try again.")
                return
            
            prompt_full_menu = MenuPrompt.get_prompt_full_menu()
            client = OpenAIClient(api_key=api_key)
            
            progress_text = st.empty()
            progress_bar = st.progress(0)
            
            output_folder = CSVProcessor.process_images_in_folder(path, prompt_full_menu, client, progress_bar, progress_text)
            combined_df, combined_csv_path = CSVProcessor.combine_csvs(output_folder)
            
            st.dataframe(combined_df)
            st.download_button(
                label="Download CSV",
                data=open(combined_csv_path, "rb").read(),
                file_name=f"{os.path.basename(output_folder)}.csv",
                mime="text/csv"
            )

if __name__ == "__main__":
    main()
