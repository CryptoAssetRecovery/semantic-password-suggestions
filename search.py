from langchain.embeddings.sentence_transformer import SentenceTransformerEmbeddings
from langchain.vectorstores import Chroma
from src.embedding import get_embedding_function

def semantic_search(query):

    db = Chroma(persist_directory="./chroma_db", embedding_function=get_embedding_function())
    suggestions = db.semantic_search(query, k=10)

    return suggestions

if __name__ == "__main__":
    suggestions = semantic_search("skihouse")
    [print(pwd.page_content) for pwd in suggestions]