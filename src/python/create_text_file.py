from dotenv import load_dotenv
import os
import sys
import requests

# Import functions from library Rich (https://github.com/Textualize/rich)
from rich import print
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt
from rich.style import Style
from rich.syntax import Syntax
from rich.traceback import install
from rich.progress import Progress, TextColumn, BarColumn, TimeRemainingColumn

load_dotenv()
github_token = os.getenv('GITHUB_TOKEN')

def get_github_token():
    TOKEN = os.getenv('GITHUB_TOKEN', github_token)
    if TOKEN == 'default_token_here':
        raise EnvironmentError("GITHUB_TOKEN environment variable not set.")

    headers = {"Authorization": f"token {TOKEN}"}
    return headers


def process_directory(url, repo_content):
    headers = get_github_token()
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    files = response.json()

    for file in files:
        if file["type"] == "file" and is_allowed_filetype(file["name"]):
            print(f"Processing {file['path']}...")

            temp_file = f"temp_{file['name']}"
            download_file(file["download_url"], temp_file)

            repo_content.append(f'<file name="{escape_xml(file["path"])}">') 
            if file["name"].endswith(".ipynb"):
                repo_content.append(escape_xml(process_ipynb_file(temp_file)))
            else:
                with open(temp_file, "r", encoding='utf-8', errors='ignore') as f:
                    repo_content.append(escape_xml(f.read()))
            repo_content.append('</file>')
            os.remove(temp_file)

        elif file["type"] == "dir":
            process_directory(file["url"], repo_content)
        else:
            print(f"Skipped {file}")


def process_github_repo(repo_url):
    api_base_url = "https://api.github.com/repos/"
    repo_url_parts = repo_url.split("https://github.com/")[-1].split("/")
    repo_name = "/".join(repo_url_parts[:2])

    # Detect if we have a branch or tag reference
    branch_or_tag = ""
    subdirectory = ""
    if len(repo_url_parts) > 2 and repo_url_parts[2] == "tree":
        # The branch or tag name should be at index 3
        if len(repo_url_parts) > 3:
            branch_or_tag = repo_url_parts[3]
        # Any remaining parts after the branch/tag name form the subdirectory
        if len(repo_url_parts) > 4:
            subdirectory = "/".join(repo_url_parts[4:])
    
    contents_url = f"{api_base_url}{repo_name}/contents"
    if subdirectory:
        contents_url = f"{contents_url}/{subdirectory}"
    if branch_or_tag:
        contents_url = f"{contents_url}?ref={branch_or_tag}"

    repo_content = [f'<source type="github_repository" url="{repo_url}">']

    process_directory(contents_url, repo_content)
    repo_content.append('</source>')
    print("All files processed.")

    return "\n".join(repo_content)


def main():
    console = Console()

    intro_text = Text("\nInput Paths or URLs Processed:\n", style="dodger_blue1")
    input_types = [
        ("• Local folder path (flattens all files into text)", "bright_white"),
        ("• GitHub repository URL (flattens all files into text)", "bright_white"),
        ("• GitHub pull request URL (PR + Repo)", "bright_white"),
        ("• GitHub issue URL (Issue + Repo)", "bright_white"),
        ("• Documentation URL (base URL)", "bright_white"),
        ("• YouTube video URL (to fetch transcript)", "bright_white"),
        ("• ArXiv Paper URL", "bright_white"),
        ("• DOI or PMID to search on Sci-Hub", "bright_white"),
    ]

    for input_type, color in input_types:
        intro_text.append(f"\n{input_type}", style=color)

    intro_panel = Panel(
        intro_text,
        expand=False,
        border_style="bold",
        title="[bright_white]Copy to File and Clipboard[/bright_white]",
        title_align="center",
        padding=(1, 1),
    )
    console.print(intro_panel)

    # If an argument is passed, use it. Otherwise, prompt user to pass an argument
    if len(sys.argv) > 1:
        input_path = sys.argv[1]
    else:
        input_path = Prompt.ask("\n[bold dodger_blue1]Enter the path or URL[/bold dodger_blue1]", console=console)
    
    console.print(f"\n[bold bright_green]You entered:[/bold bright_green] [bold bright_yellow]{input_path}[/bold bright_yellow]\n")

    output_file = "uncompressed_output.txt"
    processed_file = "compressed_output.txt"
    urls_list_file = "processed_urls.txt"

    with Progress(
        TextColumn("[bold bright_blue]{task.description}"),
        BarColumn(bar_width=None),
        TimeRemainingColumn(),
        console=console,
    ) as progress:

        task = progress.add_task("[bright_blue]Processing...", total=100)

        # Parse the input path to call the correct function
        try:
            # Git functions
            if "github.com" in input_path:
                if "/pull/" in input_path:
                    final_output = process_github_pull_request(input_path)
                elif "/issues/" in input_path:
                    final_output = process_github_issue(input_path)
                else:
                    final_output = process_github_repo(input_path)

            # # URL functions
            # elif urlparse(input_path).scheme in ["http", "https"]:
            #     if "youtube.com" in input_path or "youtu.be" in input_path:
            #         final_output = fetch_youtube_transcript(input_path)
            #     elif "arxiv.org" in input_path:
            #         final_output = process_arxiv_pdf(input_path)
            #     else:
            #         crawl_result = crawl_and_extract_text(input_path, max_depth=2, include_pdfs=True, ignore_epubs=True)
            #         final_output = crawl_result['content']
            #         with open(urls_list_file, 'w', encoding='utf-8') as urls_file:
            #             urls_file.write('\n'.join(crawl_result['processed_urls']))
            
            # # Scientific papers from https://sci-hub.se/
            # elif input_path.startswith("10.") and "/" in input_path or input_path.isdigit():
            #     final_output = process_doi_or_pmid(input_path)
            
            # Local folder
            # else:
            #     final_output = process_local_folder(input_path)

            progress.update(task, advance=50)

            # Write the uncompressed output
            with open(output_file, "w", encoding="utf-8") as file:
                file.write(final_output)


            # Process the compressed output
            preprocess_text(output_file, processed_file)

            progress.update(task, advance=50)

            compressed_text = safe_file_read(processed_file)
            compressed_token_count = get_token_count(compressed_text)
            console.print(f"\n[bright_green]Compressed Token Count:[/bright_green] [bold bright_cyan]{compressed_token_count}[/bold bright_cyan]")

            uncompressed_text = safe_file_read(output_file)
            uncompressed_token_count = get_token_count(uncompressed_text)
            console.print(f"[bright_green]Uncompressed Token Count:[/bright_green] [bold bright_cyan]{uncompressed_token_count}[/bold bright_cyan]")

            console.print(f"\n[bold bright_yellow]{processed_file}[/bold bright_yellow] and [bold bright_blue]{output_file}[/bold bright_blue] have been created in the working directory.")

            pyperclip.copy(uncompressed_text)
            console.print(f"\n[bright_white]The contents of [bold bright_blue]{output_file}[/bold bright_blue] have been copied to the clipboard.[/bright_white]")

        except Exception as e:
            console.print(f"\n[bold red]An error occurred:[/bold red] {str(e)}")
            console.print("\nPlease check your input and try again.")
            raise  # Re-raise the exception for debugging purposes


if __name__ == "__main__":
    main()
