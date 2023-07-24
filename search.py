from langchain.embeddings.sentence_transformer import SentenceTransformerEmbeddings
from langchain.vectorstores import Chroma
from src.embedding import embedding_function

def semantic_search(query):

    db = Chroma(host='localhost', port=8000, embedding_function=embedding_function())

    retriever = db.as_retriever(search_type="mmr", search_kwargs={"k": 10})
    suggestions = retriever.get_relevant_documents(query)

    return suggestions

if __name__ == "__main__":
    suggestions = semantic_search("charlesb03824")
    [print(pwd.page_content) for pwd in suggestions]