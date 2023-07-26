# import
from langchain.embeddings.sentence_transformer import SentenceTransformerEmbeddings
from langchain.vectorstores import Chroma
import uuid
from src.embedding import embedding_function as ef
import time

def update_db():
    embedding_function = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
    with open("passwords/top500k.txt", "r") as f:
        passwords = f.read().splitlines()

    interval = 10000
    passwords = [passwords[i:i + interval] for i in range(0, len(passwords), interval)]
    
    db = None
    startTime = time.time()
    
    completed = []
    times = []

    for i, pwd_list in enumerate(passwords):
        ids = [str(uuid.uuid4()) for pwd in pwd_list]
        metadata = [{'source':'top50k', 'length':len(pwd)} for pwd in pwd_list]
        if i == 0 or db == None:
            db = Chroma.from_texts(
                pwd_list, 
                embedding_function, 
                persist_directory="./chroma_db"
            )
            db.persist()
            elapsed_time = (time.time()-startTime)/60
            print("Completed num: " + str((i+1)*interval) + " in " + "{:.2f}".format(elapsed_time) + " min.\n")
        else:
            db._collection.add(
                ids=ids,
                metadatas=metadata,
                documents=pwd_list,
            )
            db.persist()
            elapsed_time = (time.time()-startTime)/60
            print("Completed num: " + str((i+1)*interval) + " in " + "{:.2f}".format(elapsed_time) + " min.\n")

        # Add number of completed records and time to lists
        completed.append((i+1)*interval)
        times.append(elapsed_time)

    print(f"Done.\n {str((time.time()-startTime)/60)} minutes in total.")
    
    # Plot the benchmark
    plot_benchmark(completed, times)

    return "done"

import matplotlib.pyplot as plt

def plot_benchmark(completed, times):
    plt.plot(times, completed)
    plt.xlabel('Time (minutes)')
    plt.ylabel('Number of completed passwords')
    plt.title('Benchmark of Password Processing')
    plt.show()


if __name__ == "__main__":
    update_db()

