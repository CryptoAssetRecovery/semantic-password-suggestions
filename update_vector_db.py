# update_vector_db.py

import os
import time
import faiss
import sqlite3
import argparse
import numpy as np
from tqdm import tqdm
from typing import List
from sentence_transformers import SentenceTransformer
from datetime import timedelta, datetime

CHUNK_SIZE = 25000  # Number of lines to read at a time
DIMENSION = 384  # Dimension for FAISS index
NLIST = 100
TRAINING_BATCH_SIZE = 75000

embedding_function = SentenceTransformer('all-MiniLM-L12-v2')

def compute_embeddings(passwords: List[str]):
    return embedding_function.encode(passwords)


def create_table(cursor):
    cursor.execute('''CREATE TABLE IF NOT EXISTS passwords
                     (id INTEGER PRIMARY KEY, password TEXT)''')


def initialize_faiss_index(dimension):
    quantizer = faiss.IndexFlatL2(dimension)
    index = faiss.IndexIVFFlat(quantizer, dimension, NLIST)
    return index


def update_db(password_file: str):
    index = initialize_faiss_index(DIMENSION)

    with open(password_file, "r") as f:
        first_batch = [next(f).strip() for _ in range(TRAINING_BATCH_SIZE)]
    first_batch_embeddings = np.array(compute_embeddings(first_batch))

    assert not index.is_trained
    index.train(first_batch_embeddings)
    assert index.is_trained

    conn = sqlite3.connect('faiss_index/pwd_index.db')
    c = conn.cursor()

    create_table(c)

    total_lines = sum(1 for _ in open(password_file, "r"))
    start = time.time()

    current_id = 0
    with open(password_file, "r") as f:
        chunk = []
        for i, line in enumerate(f):
            chunk.append(line.strip())
            if (i + 1) % CHUNK_SIZE == 0:
                embeddings = np.array(compute_embeddings(chunk), dtype='float32')
                ids = np.array(range(current_id, current_id + len(embeddings)), dtype='int64')
                index.add_with_ids(embeddings, ids)

                c.executemany('INSERT INTO passwords VALUES (?,?)',
                              [(j, pw) for j, pw in enumerate(chunk, start=current_id)])
                conn.commit()
                current_id += len(chunk)
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
            ids = np.array(range(current_id, current_id + len(embeddings)), dtype='int64')
            index.add_with_ids(embeddings, ids)
            c.executemany('INSERT INTO passwords VALUES (?,?)',
                          [(j, pw) for j, pw in enumerate(chunk, start=current_id)])
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
