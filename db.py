# create the chroma client
from langchain.embeddings import HuggingFaceEmbeddings
import chromadb
from chromadb.config import Settings
import uuid
from src.embedding import embedding_function as ef
import time

def update_db():
    client = chromadb.HttpClient(host='localhost', port=8000, settings=Settings(anonymized_telemetry=False))
    try:
        client.delete_collection("passwords")
    except:
        pass
    collection = client.create_collection(name="passwords")
    with open("passwords/top50k.txt", "r") as f:
        passwords = f.read().splitlines()

    if len(passwords) > 25000:
        # make a number of lists of max 25000
        passwords = [passwords[i:i + 25000] for i in range(0, len(passwords), 25000)]

    for pwd_list in passwords:
        ids = [str(uuid.uuid4()) for pwd in pwd_list]
        metadata = [{'source':'top100k', 'length':len(pwd)} for pwd in pwd_list]

        collection.add(
            ids=ids,
            metadatas=metadata,
            documents=pwd_list,
        )

    return "done"

if __name__ == "__main__":
    startTime = time.time()
    update_db()
    endTime = time.time()
    print(str((endTime-startTime)/60) + " minutes")

