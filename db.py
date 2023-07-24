# create the chroma client
import chromadb
import uuid
from chromadb.config import Settings
from src.embedding import embedding_function
import time

def update_db():

    client = chromadb.HttpClient(settings=Settings(allow_reset=True))
    client.delete_collection("passwords")
    collection = client.create_collection("passwords", embedding_function=embedding_function())

    # load the document and split it into chunks
    with open("passwords/top15k.txt", "r") as f:
        passwords = f.read().splitlines()

    ids = [str(uuid.uuid1()) for pwd in passwords]
    metadata = [{'source':'top15k'} for pwd in passwords]

    collection.add(
        ids=ids,
        metadatas=metadata,
        documents=passwords,
    )

    return "done"

if __name__ == "__main__":
    startTime = time.time()
    update_db()
    endTime = time.time()
    print(str(endTime-startTime))

