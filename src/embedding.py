from langchain.embeddings.sentence_transformer import SentenceTransformerEmbeddings
import langchain

def embedding_function():
    return SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")