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
        self.pdf_path = pdf_path
        self.base_name = os.path.splitext(os.path.basename(pdf_path))[0].replace(" ", "_")
        self.output_folder = self.base_name

    def take_screenshots_of_menu_sections(self):
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
        self.client = OpenAI(api_key=api_key)

    def process_image(self, image_path, prompt_full_menu):
        base64_image = self.encode_image(image_path)
        try:
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
            response_content = response.choices[0].message.content
            json_start = response_content.find('```json') + len('```json')
            json_end = response_content.rfind('```')
            json_string = response_content[json_start:json_end].strip()
            menu_data = json.loads(json_string)
            menu_df = pd.json_normalize(menu_data, record_path=['items'], meta=['item_type'])

            # Log the prompt, JSON content, and DataFrame
            logging.info(f"Processed image: {image_path}")
            logging.info(f"Prompt used: {prompt_full_menu}")
            logging.info(f"JSON content: {json_string}")
            logging.info(f"DataFrame: {menu_df}")

            return menu_df
        except OpenAIError as e:
            print(f"An error occurred: {e}")
            return None

    @staticmethod
    def encode_image(image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

class CSVProcessor:
    @staticmethod
    def process_images_in_folder(path, prompt_full_menu, client):
        output_folder = f"{os.path.basename(path)}_output"
        os.makedirs(output_folder, exist_ok=True)
        
        for filename in os.listdir(path):
            if filename.endswith(('.png', '.jpg', '.jpeg')):
                image_path = os.path.join(path, filename)
                menu_df = client.process_image(image_path, prompt_full_menu)
                if menu_df is not None:
                    csv_filename = os.path.splitext(filename)[0] + '.csv'
                    csv_path = os.path.join(output_folder, csv_filename)
                    menu_df.to_csv(csv_path, index=False)
                    print(f"Saved CSV for {filename} to {csv_path}")
        return output_folder

    @staticmethod
    def combine_csvs(output_folder):
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
    st.title("Menu PDF to CSV Converter")
    uploaded_file = st.file_uploader("Upload a PDF file", type="pdf")
    api_key = st.text_input("Enter your OpenAI API key", type="password")
    
    if uploaded_file is not None and api_key:
        with open("uploaded_file.pdf", "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        pdf_processor = PDFProcessor("uploaded_file.pdf")
        path = pdf_processor.take_screenshots_of_menu_sections()
        
        prompt_full_menu = MenuPrompt.get_prompt_full_menu()
        client = OpenAIClient(api_key=api_key)
        
        output_folder = CSVProcessor.process_images_in_folder(path, prompt_full_menu, client)
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
