import os, argparse
import time
import sqlite3
import numpy as np
import faiss
from typing import List
from langchain.embeddings.sentence_transformer import SentenceTransformerEmbeddings

CHUNK_SIZE = 50000  # Number of lines to read at a time

def compute_embeddings(passwords: List[str]):
    embedding_function = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
    embeddings = embedding_function.embed_documents(passwords)
    return embeddings

def update_db(password_file: str):
    # Initialize the index
    d = 384  # dimension
    nlist = 100
    quantizer = faiss.IndexFlatL2(d)  # the other index
    index = faiss.IndexIVFFlat(quantizer, d, nlist)
    TRAINING_BATCH_SIZE = 100000

    # Compute embeddings for the first batch
    with open(password_file, "r") as f:
        first_batch = [next(f).strip() for _ in range(TRAINING_BATCH_SIZE)]
    first_batch_embeddings = np.array(compute_embeddings(first_batch))

    assert not index.is_trained
    index.train(first_batch_embeddings)
    assert index.is_trained

    # Create a database connection and a cursor
    conn = sqlite3.connect('faiss_index/pwd_index.db')
    c = conn.cursor()

    # Create table
    c.execute('''CREATE TABLE passwords
                 (id INTEGER PRIMARY KEY, password TEXT)''')

    total_lines = sum(1 for line in open(password_file, "r"))  # get total lines for progress calculation

    with open(password_file, "r") as f:
        chunk = []
        for i, line in enumerate(f):
            chunk.append(line.strip())
            if (i + 1) % CHUNK_SIZE == 0:
                # Compute embeddings for this chunk
                embeddings = compute_embeddings(chunk)
                # Add embeddings to the index
                ids = np.array(range(len(embeddings)), dtype='int64')  # create an array of IDs
                index.add_with_ids(np.array(embeddings, dtype='float32'), ids)
                # Insert the passwords into the database
                c.executemany('INSERT INTO passwords VALUES (?,?)', 
                              [(i, pw) for i, pw in enumerate(chunk, start=i-len(chunk)+1)])
                # Commit the changes
                conn.commit()
                # Reset chunk
                chunk = []

                # Report progress
                print(f'Progress: {i+1}/{total_lines} lines processed, {((i+1)/total_lines)*100:.2f}% done.')

        # Don't forget the last chunk
        if chunk:
            embeddings = compute_embeddings(chunk)
            ids = np.array(range(len(embeddings)), dtype='int64')  # create an array of IDs
            index.add_with_ids(np.array(embeddings, dtype='float32'), ids)
            c.executemany('INSERT INTO passwords VALUES (?,?)', 
                          [(i, pw) for i, pw in enumerate(chunk, start=i-len(chunk)+1)])
            conn.commit()

    # Save the index to disk
    faiss.write_index(index, 'faiss_index/final.index')

    # Close the connection
    conn.close()

    return "done"

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="An implementation of FAISS for password search.",
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-w", "--wordlist", help="The password list you'd like to create the index from.", required=True)
    args = parser.parse_args()

    start = time.time()
    update_db(args.wordlist)
    print(f"Done in {time.time()-start} seconds.")