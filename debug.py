import requests
from dotenv import load_dotenv
import os 

load_dotenv()
github_token = os.getenv('GITHUB_TOKEN')

def get_github_token():
    TOKEN = os.getenv('GITHUB_TOKEN', github_token)
    if TOKEN == 'default_token_here':
        raise EnvironmentError("GITHUB_TOKEN environment variable not set.")

    headers = {"Authorization": f"token {TOKEN}"}
    return headers

repo_url = 'https://github.com/SimonPlancke/local_llm'

api_base_url = "https://api.github.com/repos/"
repo_url_parts = repo_url.split("https://github.com/")[-1].split("/")
repo_name = "/".join(repo_url_parts[:2])
contents_url = f"{api_base_url}{repo_name}/contents"


headers = get_github_token()
response = requests.get(contents_url, headers=headers)
response.raise_for_status()
files = response.json()
print(files)