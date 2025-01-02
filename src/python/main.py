from langchain_community.document_loaders import TextLoader # Text loader
from langchain.text_splitter import CharacterTextSplitter # Text splitter
from langchain_community.embeddings import OllamaEmbeddings # Ollama embeddings
# import weaviate # Vector database
import chromadb 
from langchain.prompts import ChatPromptTemplate # Chat prompt template
from langchain_community.chat_models import ChatOllama # ChatOllma chat model
from langchain.schema.runnable import RunnablePassthrough
from langchain.schema.output_parser import StrOutputParser # Output parser
from langchain_community.vectorstores import Chroma # Vector database
# from weaviate.embedded import EmbeddedOptions # Vector embedding options
import requests


# loading file
loader = TextLoader('uncompressed_output.txt')
documents = loader.load()


text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
chunks = text_splitter.split_documents(documents)

client = chromadb.Client(
    embedded_options=EmbeddedOptions()
)

vectorstore = Chroma.from_documents(
    client=client,
    documents=chunks,
    embedding=OllamaEmbeddings(model="llama3"),
    by_text=False
)

# retriever
retriever = vectorstore.as_retriever()

# LLM prompt template
template = """You are an assistant for specific knowledge query tasks. 
   Use the following pieces of retrieved context to answer the question. 
   If you don't know the answer, just say that you don't know. 
   Question: {question} 
   Context: {context} 
   Answer:
   """
prompt = ChatPromptTemplate.from_template(template)


llm = ChatOllama(model="llama3", temperature=0.2)
rag_chain = (
        {"context": retriever, "question": RunnablePassthrough()} # context window
        | prompt
        | llm
        | StrOutputParser()
)

# begin to query and get feedback from specific knowledge 
query = "What are the best side hustles for 2025?"
print(rag_chain.invoke(query))