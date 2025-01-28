# Import libraries
import requests
import re

# Import classes and functions
from nbconvert import PythonExporter
from nbformat import reads
from nltk.corpus import stopwords
from nltk import download
from urllib.parse import urlparse


def is_allowed_filetype(filename):
    allowed_extensions = ['.py', '.txt', '.js', '.tsx', '.ts', '.md', '.cjs', '.html', '.json', '.ipynb', '.h', '.localhost', '.sh', '.yaml', '.example', '.ps1', '.sql']
    return any(filename.endswith(ext) for ext in allowed_extensions)
    

def download_file(url, target_path, headers):
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    with open(target_path, "wb") as f:
        f.write(response.content)


def escape_xml(text):
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        # Remove the following lines to stop converting apostrophes and quotes
        # .replace("\"", "&quot;")
        # .replace("'", "&apos;")
    )


def process_ipynb_file(temp_file):
    """
    Processes an IPyNB file.

    Args:
    filepath (str): Path to the input file.
    """
    with open(temp_file, "r", encoding='utf-8', errors='ignore') as f:
        notebook_content = f.read()

    exporter = PythonExporter()
    python_code, _ = exporter.from_notebook_node(reads(notebook_content, as_version=4))
    return python_code




## NEW: TO CHECK
def is_same_domain(base_url, new_url):
    return urlparse(base_url).netloc == urlparse(new_url).netloc

def is_within_depth(base_url, current_url, max_depth):
    base_parts = urlparse(base_url).path.rstrip('/').split('/')
    current_parts = urlparse(current_url).path.rstrip('/').split('/')

    if current_parts[:len(base_parts)] != base_parts:
        return False

    return len(current_parts) - len(base_parts) <= max_depth


def extract_links(input_file, output_file):
    """
    Extract links from the given input file.

    Args:
    input_file (str): Path to the input file.
    output_file (str): Path to the output file.
    """
    url_pattern = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
    
    with open(input_file, 'r', encoding='utf-8') as file:
        content = file.read()
        urls = re.findall(url_pattern, content)
    
    with open(output_file, 'w', encoding='utf-8') as output:
        for url in urls:
            output.write(url + '\n')

def get_stopword_list():
    download("stopwords", quiet=True)
    stop_words = set(stopwords.words("english"))
    return stop_words