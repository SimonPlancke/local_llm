# Import Python native packages
import os
from dotenv import load_dotenv

# Import langchain methods
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings

# Import project scripts
from config import config

# from sentence_transformers import SentenceTransformer

# Load the .env script in the repo
# This script should contain the HUGGINGFACEHUB_API_TOKEN
load_dotenv()
huggingfacehub_api_token = os.getenv('HUGGINGFACEHUB_API_TOKEN')

# Step 1: Read the file
def read_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

# Step 2: Preprocess the data
def preprocess_text(text):
    # Clean and split the text into chunks
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1200, chunk_overlap=300)
    return text_splitter.split_text(text)

# Step 3: Vectorization and Indexing
def create_vector_store(docs):
    # Use SentenceTransformer for embeddings
    # model = SentenceTransformer('all-MiniLM-L6-v2')
    # embeddings = model.encode(docs) #, convert_to_tensor=True)  # Generate embeddings for all documents
    embeddings = HuggingFaceEmbeddings()
    text_embeddings = embeddings.embed_documents(docs)
    text_embedding_pairs = zip(docs, text_embeddings)
    vector_store = FAISS.from_embeddings(text_embedding_pairs, embeddings)

    vector_store.save_local("vector_database")  # Save the index locally
    return vector_store

# Main function to run the program
def main():
    text_folder = config.text_file_path
    file_path = 'uncompressed_output.txt'
    text = read_file(file_path)
    docs = preprocess_text(text)
    vector_store = create_vector_store(docs)


if __name__ == "__main__":
    main()