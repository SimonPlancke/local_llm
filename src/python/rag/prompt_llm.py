from langchain_huggingface import HuggingFaceEmbeddings, HuggingFaceEndpoint
from langchain_community.vectorstores import FAISS

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


# Main function to run the program
def main():
    user_query = input("Ask a question: \n")
    llm = load_llm()
    embeddings = HuggingFaceEmbeddings()
    vector_store = FAISS.load_local("faiss_AiDoc", embeddings, allow_dangerous_deserialization=True)
    answer = query_llm(llm, vector_store, user_query)
    print("Answer:", answer)

if __name__ == "__main__":
    main()