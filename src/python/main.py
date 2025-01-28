import create_vector_db
import create_text_file
import prompt_llm
from config import Config
import sys
import importlib
from rich.prompt import Prompt
from rich.console import Console
# orchestrator.py

def main():
    # console = Console()

    # if len(sys.argv) > 1:
    #     rag_name = sys.argv[1]
    # else:
    #     rag_name = Prompt.ask("\n[bold dodger_blue1]Enter the working name for the RAG: [/bold dodger_blue1]", console=console)
    
    # text_export_directory = "./text_files/"

    # Create a configuration object with the provided parameters
    config = Config(**params)

    create_text_file.main()
    create_vector_db.main()

    while True:
        prompt_llm.main()

if __name__ == "__main__":
    # Example of parsing command-line arguments
    params = {}
    for arg in sys.argv[1:]:
        key, value = arg.split('=')
        params[key] = value

    main(params)