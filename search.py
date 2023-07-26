from langchain.embeddings.sentence_transformer import SentenceTransformerEmbeddings
from langchain.vectorstores import Chroma
from chromadb.config import Settings
import chromadb
from chromadb.utils import embedding_functions

def semantic_search(query):

    client = chromadb.HttpClient(host='localhost', port=8000, settings=Settings(anonymized_telemetry=False))

    collection = client.get_collection("passwords")

    suggestions = collection.query(
        query_texts=[query],
        n_results=100,
    )

    return suggestions

if __name__ == "__main__":
    suggestions = semantic_search("charlesb03824")
    [print(pwd) for pwd in suggestions['documents'][0]]