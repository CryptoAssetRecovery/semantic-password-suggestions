from langchain.vectorstores import Milvus
from src.embedding import embedding_function
import time

def update_db():
    # load the document and split it into chunks
    with open("passwords/top15k.txt", "r") as f:
        passwords = f.read().splitlines()

    # create the open-source embedding function
    Milvus.from_texts(
        passwords,
        embedding_function(),
        connection_args={"host": "127.0.0.1", "port": "19530"},
    )
    return "done"

if __name__ == "__main__":
    startTime = time.time()
    update_db()
    endTime = time.time()
    print(str(endTime-startTime))

