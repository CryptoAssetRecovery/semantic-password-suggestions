# update_vector_db.py

import os
import time
import faiss
import sqlite3
import argparse
import numpy as np
from tqdm import tqdm
from typing import List
from langchain.embeddings.sentence_transformer import SentenceTransformerEmbeddings
from datetime import timedelta, datetime

CHUNK_SIZE = 25000  # Number of lines to read at a time
DIMENSION = 384  # Dimension for FAISS index
NLIST = 100
TRAINING_BATCH_SIZE = 100000

def compute_embeddings(passwords: List[str]):
    embedding_function = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
    return embedding_function.embed_documents(passwords)


def create_table(cursor):
    cursor.execute('''CREATE TABLE IF NOT EXISTS passwords
                     (id INTEGER PRIMARY KEY, password TEXT)''')


def initialize_faiss_index(dimension):
    quantizer = faiss.IndexFlatL2(dimension)
    index = faiss.IndexIVFFlat(quantizer, dimension, NLIST)
    return index


def update_db(password_file: str):
    # Initialize the index
    index = initialize_faiss_index(DIMENSION)

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

    # Create table if not exists
    create_table(c)

    total_lines = sum(1 for _ in open(password_file, "r"))  # get total lines for progress calculation

    start = time.time()

    with open(password_file, "r") as f:
        chunk = []
        for i, line in enumerate(f):
            chunk.append(line.strip())
            if (i + 1) % CHUNK_SIZE == 0:
                # Compute embeddings for this chunk and add to the index
                embeddings = np.array(compute_embeddings(chunk), dtype='float32')
                ids = np.array(range(len(embeddings)), dtype='int64')  # create an array of IDs
                index.add_with_ids(embeddings, ids)

                # Insert the passwords into the database
                c.executemany('INSERT INTO passwords VALUES (?,?)', 
                              [(j, pw) for j, pw in enumerate(chunk, start=i-len(chunk)+1)])
                conn.commit()
                chunk = []

                elapsed = time.time() - start
                estimated_total_time = elapsed * (total_lines / (i+1))
                estimated_end_time = start + estimated_total_time
                remaining_time = estimated_total_time - elapsed
                print(f'Progress: {i+1}/{total_lines} lines processed, {((i+1)/total_lines)*100:.2f}% done. '
                      f'Estimated end time: {datetime.fromtimestamp(estimated_end_time).strftime("%Y-%m-%d %H:%M:%S")}. '
                      f'Remaining time: {timedelta(seconds=remaining_time)}.', end='\r')

        # Handle the last chunk
        if chunk:
            embeddings = np.array(compute_embeddings(chunk), dtype='float32')
            ids = np.array(range(len(embeddings)), dtype='int64')
            index.add_with_ids(embeddings, ids)
            c.executemany('INSERT INTO passwords VALUES (?,?)', 
                          [(j, pw) for j, pw in enumerate(chunk, start=i-len(chunk)+1)])
            conn.commit()

    # Save the index to disk
    faiss.write_index(index, 'faiss_index/final.index')
    conn.close()

    return "done"


def main():
    parser = argparse.ArgumentParser(description="An implementation of FAISS for password search.",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-w", "--wordlist", help="The password list you'd like to create the index from.", required=True)
    args = parser.parse_args()

    start = time.time()
    update_db(args.wordlist)
    print(f"\nDone in {time.time() - start} seconds.")


if __name__ == "__main__":
    main()
