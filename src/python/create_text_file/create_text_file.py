import sys
from urllib.parse import urlparse

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

# Repository classes and scripts
from git_methods import GitMethods
import generic_functions as generic_functions
from file_processing import TextFileMethods, PDFFileMethods, FolderMethods, TranscriptionMethods

def safe_file_read(filepath, fallback_encoding:str='latin1') -> str:
    """
    Safely reads the content of a file, attempting to handle encoding issues.

    This function first tries to read the file using UTF-8 encoding. If a UnicodeDecodeError occurs, 
    it attempts to read the file again using the specified fallback encoding.

    Parameters:
    ----------
    fallback_encoding : str, optional
        The encoding to use if the file cannot be read with UTF-8. 
        Default is 'latin1'.

    Returns:
    -------
    str
        The content of the file as a string.

    Raises:
    ------
    FileNotFoundError
        If the specified file does not exist.
    IOError
        If there is an error reading the file (e.g., permission issues).

    """
    try:
        with open(filepath, "r", encoding='utf-8') as file:
            return file.read()
    except UnicodeDecodeError:
        with open(filepath, "r", encoding=fallback_encoding) as file:
            return file.read()
        


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
                gitmethods_object = GitMethods()
                final_output = gitmethods_object.handle_git_url()

            # URL functions
            elif urlparse(input_path).scheme in ["http", "https"]:
                if "youtube.com" in input_path or "youtu.be" in input_path:
                    final_output = TranscriptionMethods.fetch_youtube_transcript(input_path)
                elif "arxiv.org" in input_path:
                    final_output = PDFFileMethods.process_arxiv_pdf(input_path)
                # else:
                #     crawl_result = crawl_and_extract_text(input_path, max_depth=2, include_pdfs=True, ignore_epubs=True)
                #     final_output = crawl_result['content']
                #     with open(urls_list_file, 'w', encoding='utf-8') as urls_file:
                #         urls_file.write('\n'.join(crawl_result['processed_urls']))
            
            # Scientific papers from https://sci-hub.se/
            elif input_path.startswith("10.") and "/" in input_path or input_path.isdigit():
                final_output = PDFFileMethods.process_doi_or_pmid(input_path)
            
            # Local folder
            else:
                final_output = FolderMethods.process_local_folder(input_path)

            progress.update(task, advance=50)

            # Write the uncompressed output
            with open(output_file, "w", encoding="utf-8") as file:
                file.write(final_output)


            # Process the compressed output
            TextFileMethods.parse_text_as_xml(output_file, processed_file)

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
