import re
import os
import requests
import wget

from generic_functions import get_stopword_list, escape_xml, is_allowed_filetype, process_ipynb_file, download_file
from git_methods import GitMethods

import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from PyPDF2 import PdfReader
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter


class TextFileMethods():
    def __init__(self, filepath:str):
        self.filepath = filepath

    @staticmethod
    def clean_text(text):
        # Remove new-line characters
        text = re.sub(r"[\n\r]+", "\n", text)
        # Remove unwanted characters
        text = re.sub(r"[^a-zA-Z0-9\s_.,!?:;@#$%^&*()+\-=[\]{}|\\<>`~'\"/]+", "", text)
        # Normalize Whitespace
        text = re.sub(r"\s+", " ", text)
        # Convert to Lowercase
        text = text.lower()
        # Split into words
        words = text.split()

        # Drop stop words (the, is, in...)
        stop_words = get_stopword_list()
        words = [word for word in words if word not in stop_words]
        
        return " ".join(words)


    def parse_text_as_xml(self, input_file, output_file):
        with open(input_file, "r", encoding="utf-8") as input_file:
            input_text = input_file.read()

        try:
            # Try to parse the input as XML
            root = ET.fromstring(input_text)

            # Process text content while preserving XML structure
            for elem in root.iter():
                if elem.text:
                    elem.text = self.clean_text(elem.text)
                if elem.tail:
                    elem.tail = self.clean_text(elem.tail)

            # Write the processed XML to the output file
            tree = ET.ElementTree(root)
            tree.write(output_file, encoding="utf-8", xml_declaration=True)
            print("Text preprocessing completed with XML structure preserved.")
        except ET.ParseError:
            # If XML parsing fails, process the text without preserving XML structure
            processed_text = self.clean_text(input_text)
            with open(output_file, "w", encoding="utf-8") as out_file:
                out_file.write(processed_text)
            Warning("XML parsing failed. Text preprocessing completed without XML structure.")

class PDFFileMethods():

    def add_xml_tags_for_paper(self, text):
        paper_xml_formatted_text = '<paper>\n'
        paper_xml_formatted_text += escape_xml(' '.join(text))
        paper_xml_formatted_text += '\n</paper>\n'

        return paper_xml_formatted_text

    def process_pdf(self, url):
        # Download PDF content
        response = requests.get(url)
        response.raise_for_status()
        content = response.content

        with open('temp.pdf', 'wb') as pdf_file:
            pdf_file.write(content)

        text = []
        with open('temp.pdf', 'rb') as pdf_file:
            pdf_reader = PdfReader(pdf_file)
            for page in range(len(pdf_reader.pages)):
                text.append(pdf_reader.pages[page].extract_text())

        os.remove('temp.pdf')
        return ' '.join(text)

    def process_arxiv_pdf(self, arxiv_abs_url):
        pdf_url = arxiv_abs_url.replace("/abs/", "/pdf/") + ".pdf"
        text = self.process_pdf(pdf_url)

        formatted_text = f'<source type="arxiv_paper" url="{arxiv_abs_url}">\n'
        formatted_text += self.add_xml_tags_for_paper(text)
        formatted_text += '</source>'

        os.remove('temp.pdf')
        print("ArXiv paper processed successfully.")

        return formatted_text

    def process_doi_or_pmid(self, identifier):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36',
            'Connection': 'keep-alive'
        }

        try:
            payload = {
                'sci-hub-plugin-check': '',
                'request': identifier
            }

            base_url = 'https://sci-hub.se/'
            response = requests.post(base_url, headers=headers, data=payload, timeout=60)
            soup = BeautifulSoup(response.content, 'html.parser')
            pdf_element = soup.find(id='pdf')

            if pdf_element is None:
                raise ValueError(f"No PDF found for identifier {identifier}. Sci-hub might be inaccessible or the document is not available.")

            content = pdf_element.get('src').replace('#navpanes=0&view=FitH', '').replace('//', '/')

            if content.startswith(('/downloads', '/tree', '/uptodate')):
                pdf_url = 'https://sci-hub.se' + content
            else:
                pdf_url = 'https:/' + content

            pdf_filename = f"{identifier.replace('/', '-')}.pdf"
            wget.download(pdf_url, pdf_filename)

            with open(pdf_filename, 'rb') as pdf_file:
                pdf_reader = PdfReader(pdf_file)
                text = ""
                for page in range(len(pdf_reader.pages)):
                    text += pdf_reader.pages[page].extract_text()

            formatted_text = f'<source type="sci_hub_paper" identifier="{escape_xml(identifier)}">\n'
            formatted_text += self.add_xml_tags_for_paper(text)
            formatted_text += '</source>'

            os.remove(pdf_filename)
            print(f"Identifier {identifier} processed successfully.")
            return formatted_text
        
        except (requests.RequestException, ValueError) as e:
            error_text = f'<source type="sci_hub_paper" identifier="{escape_xml(identifier)}">\n'
            error_text += f'<error>{escape_xml(str(e))}</error>\n'
            error_text += '</source>'
            print(f"Error processing identifier {identifier}: {str(e)}")
            print("Sci-hub appears to be inaccessible or the document was not found. Please try again later.")
            return error_text

class FolderMethods():
    def __init__(self, filepath):
        self.filepath = filepath

    def process_local_directory(self):
        content = [f'<source type="local_directory" path="{escape_xml(self.local_path)}">']
        for root, files in os.walk(self.local_path):
            for file in files:
                if is_allowed_filetype(file):
                    print(f"Processing {os.path.join(root, file)}...")

                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, self.local_path)
                    content.append(f'<file name="{escape_xml(relative_path)}">')

                    if file.endswith(".ipynb"):
                        content.append(escape_xml(process_ipynb_file(file_path)))
                    else:
                        with open(file_path, "r", encoding='utf-8', errors='ignore') as f:
                            content.append(escape_xml(f.read()))

                    content.append('</file>')

        content.append('</source>')
        return '\n'.join(content)

    def process_local_folder(self, local_path):

        formatted_content = self.process_local_directory(local_path)
        print("All files processed.")
        return formatted_content
    
    def process_directory(self, url, output):
        headers = GitMethods.get_github_token()
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        files = response.json()

        for file in files:
            if file["type"] == "file" and is_allowed_filetype(file["name"]):
                print(f"Processing {file['path']}...")

                temp_file = f"temp_{file['name']}"
                download_file(file["download_url"], temp_file)

                output.write(f"# {'-' * 3}\n")
                output.write(f"# Filename: {file['path']}\n")
                output.write(f"# {'-' * 3}\n\n")

                if file["name"].endswith(".ipynb"):
                    output.write(process_ipynb_file(temp_file))
                else:
                    with open(temp_file, "r", encoding='utf-8', errors='ignore') as f:
                        output.write(f.read())

                output.write("\n\n")
                os.remove(temp_file)
            elif file["type"] == "dir":
                self.process_directory(file["url"], output)

class TranscriptionMethods():

    def __init__(self, url):
        self.url = url

    def extract_video_id(self, url):
        pattern = r'(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|\S*?[?&]v=)|youtu\.be\/)([a-zA-Z0-9_-]{11})'
        match = re.search(pattern, url)
        if match:
            return match.group(1)
        return None


    def fetch_youtube_transcript(self):
        video_id = self.extract_video_id(self.url)
        if not video_id:
            return f'<source type="youtube_transcript" url="{escape_xml(self.url)}">\n<error>Could not extract video ID from URL.</error>\n</source>'

        try:
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
            formatter = TextFormatter()
            transcript = formatter.format_transcript(transcript_list)
            
            formatted_text = f'<source type="youtube_transcript" url="{escape_xml(self.url)}">\n'
            formatted_text += '<transcript>\n'
            formatted_text += escape_xml(transcript)
            formatted_text += '\n</transcript>\n'
            formatted_text += '</source>'
            
            return formatted_text
        except Exception as e:
            return f'<source type="youtube_transcript" url="{escape_xml(self.url)}">\n<error>{escape_xml(str(e))}</error>\n</source>'
