from langchain_huggingface import HuggingFaceEmbeddings, HuggingFaceEndpoint
from langchain_community.vectorstores import FAISS

import os
import re
import html
import importlib

# codestral_config = {
#     'class_name': 'CodeStral',
#     'model_name': 'your_model_name',
# }


# def load_llm(config):
#     # if config['api_key']:
#     #     os.environ['OPENAI_API_KEY'] = config['api_key']

#     # Import the LLM class
#     module_name = f'langchain_community.llms.{config["class_name"]}'
#     imported_module = importlib.import_module(module_name)

#     # Create the LLM instance
#     llm_class = getattr(imported_module, config['class_name'])
#     return llm_class(model_name=config['model_name'])


# Step 1: Set up the LLM
def load_llm():
    return HuggingFaceEndpoint(repo_id="mistralai/Mixtral-8x7B-Instruct-v0.1")

# Step 2: Query function
def query_llm(llm, vector_store, user_query):
    retriever = vector_store.as_retriever()
    # context = retriever.retrieve(user_query)
    # Retrieve relevant documents
    relevant_docs = retriever.invoke(user_query)

    # Combine the context with the user query
    context = " ".join(doc.page_content for doc in relevant_docs)
    response = llm.generate([context + user_query])
    return response

def format_text(raw_text):
    # Replace escaped newlines with actual newlines
    formatted_text = raw_text.replace('\\n', '\n')
    
    # Convert HTML entities back to their respective characters
    formatted_text = html.unescape(formatted_text)
    
    # Remove excessive whitespace while preserving line breaks
    formatted_text = re.sub(r'\s+', ' ', formatted_text).strip()
    
    # Split by lines and clean each line
    formatted_text = '\n'.join(line.strip() for line in formatted_text.splitlines())
    
    return formatted_text

def write_answers_to_folder(user_query, raw_text):
    # Create the 'answers' directory if it doesn't exist
    answers_folder = 'answers'
    os.makedirs(answers_folder, exist_ok=True)

    print(raw_text)
    # Extract the relevant text from the raw input
    match = re.search(r"text='(.*?)'", raw_text, re.DOTALL)
    if match:
        extracted_text = match.group(1).strip()
    else:
        print("No text found in the input.")
        return

    # Format the extracted text for readability
    formatted_text = format_text(extracted_text)

    # Create the filename using the user_query
    file_name = f"{user_query}.txt"

    # Write the formatted text to the file
    file_path = os.path.join(answers_folder, file_name)
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(formatted_text)

    print(f"Answers written to {file_path}")


# Main function to run the program
def main():
    user_query = input("Ask a question: \n")
    llm = load_llm()
    embeddings = HuggingFaceEmbeddings()
    vector_store = FAISS.load_local("vector_database", embeddings, allow_dangerous_deserialization=True)
    answer = query_llm(llm, vector_store, user_query)
    # print("Answer:", answer)
    write_answers_to_folder(user_query, str(answer))

if __name__ == "__main__":
    main()