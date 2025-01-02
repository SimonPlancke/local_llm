import os
from sentence_transformers import SentenceTransformer
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings, HuggingFaceEndpoint
from dotenv import load_dotenv

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
    model = SentenceTransformer('all-MiniLM-L6-v2')
    # embeddings = model.encode(docs) #, convert_to_tensor=True)  # Generate embeddings for all documents
    embeddings = HuggingFaceEmbeddings()
    text_embeddings = embeddings.embed_documents(docs)
    text_embedding_pairs = zip(docs, text_embeddings)
    vector_store = FAISS.from_embeddings(text_embedding_pairs, embeddings)

    # text_embeddings = list(zip(docs, embeddings))
    # vector_store = FAISS.from_embeddings(text_embeddings=docs) #, embedding=embeddings)  # Pass only embeddings
    vector_store.save_local("faiss_AiDoc")  # Save the index locally
    return vector_store

# Step 4: Set up the LLM
def load_llm():
    return HuggingFaceEndpoint(repo_id="mistralai/Mixtral-8x7B-Instruct-v0.1")

# Step 5: Query function
def query_llm(llm, vector_store, user_query):
    retriever = vector_store.as_retriever()
    context = retriever.retrieve(user_query)
    response = llm.generate(context + user_query)
    return response

# Main function to run the program
def main():
    file_path = 'uncompressed_output.txt'
    text = read_file(file_path)
    docs = preprocess_text(text)
    vector_store = create_vector_store(docs)
    # llm = load_llm()

    # Example query
    # user_query = input("Ask a question: ")
    # answer = query_llm(llm, vector_store, user_query)
    # print("Answer:", answer)

if __name__ == "__main__":
    main()