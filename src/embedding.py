from langchain.embeddings.sentence_transformer import SentenceTransformerEmbeddings

def embedding_function():
    return SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")