import os
import gc
import time
import math
import faiss
import argparse
import numpy as np
import psycopg2
from tqdm import tqdm
from typing import List
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from datetime import timedelta, datetime
from faiss.contrib.ondisk import merge_ondisk

load_dotenv()

CHUNK_SIZE = int(os.getenv('CHUNK_SIZE'))  # Number of lines to read at a time
DIMENSION = int(os.getenv('DIMENSION'))  # all-MiniLM-L6-v2
INDEX_DIR = os.getenv('INDEX_DIR') # Directory to save the temporary index parts
FINAL_DIR = os.getenv('FINAL_DIR')

def compute_embeddings(passwords: List[str]):
    embedding_function = SentenceTransformer('all-MiniLM-L6-v2')
    embeddings = embedding_function.encode(passwords)
    del embedding_function
    gc.collect()
    return embeddings

def create_table(cursor):
    cursor.execute('''DROP TABLE IF EXISTS passwords;''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS passwords
                     (id SERIAL PRIMARY KEY, password TEXT)''')

def initialize_faiss_index(dimension, nlist):
    quantizer = faiss.IndexFlatL2(dimension)
    index = faiss.IndexIVFPQ(quantizer, dimension, nlist, 8, 8)  # 8 is the bits per sub-vector. Adjust as needed.
    return index

def update_db(password_file: str):
    total_lines = sum(1 for _ in open(password_file, "r", encoding='latin-1', errors='ignore'))

    nlist = int(math.sqrt(total_lines))
    TRAINING_BATCH_SIZE = min(40 * nlist, total_lines)  # 5 times nlist or total_lines, whichever is smaller

    print(f"Training batch size: {TRAINING_BATCH_SIZE}")
    print(f"NLIST: {nlist}")

    index = initialize_faiss_index(DIMENSION, nlist)

    with open(password_file, "r", encoding='latin-1', errors='ignore') as f:
        first_batch = [next(f).strip() for _ in range(TRAINING_BATCH_SIZE)]
    first_batch_embeddings = np.array(compute_embeddings(first_batch))

    assert not index.is_trained
    index.train(first_batch_embeddings)
    assert index.is_trained
    faiss.write_index(index, INDEX_DIR + "trained.index")
    del first_batch_embeddings
    del first_batch

    # Establish connection to PostgreSQL
    conn = psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT")
    )
    c = conn.cursor()
    create_table(c)

    start = time.time()

    current_id = 0
    block_no = 0
    with open(password_file, "r", encoding='latin-1', errors='ignore') as f:
        chunk = []
        for line in tqdm(f, total=total_lines, desc="Overall Progress"):
            chunk.append(line.strip())
            if (len(chunk) % CHUNK_SIZE) == 0:
                embeddings = compute_embeddings(chunk)
                ids = np.array(range(current_id+1, current_id + len(embeddings)+1), dtype='int64')
                index = faiss.read_index(INDEX_DIR + "trained.index")
                index.add_with_ids(np.asarray(embeddings, dtype=np.float32), ids)
                faiss.write_index(index, INDEX_DIR + f"block_{block_no}.index")
                block_no += 1

                c.executemany('INSERT INTO passwords (password) VALUES (%s)', [(pw,) for pw in chunk])
                conn.commit()

                current_id += len(chunk)

                del embeddings
                del ids
                chunk.clear()
                gc.collect()

    # Handle the last chunk
    if chunk:
        embeddings = compute_embeddings(chunk)
        ids = np.array(range(current_id+1, current_id + len(embeddings)+1), dtype='int64')
        index = faiss.read_index(INDEX_DIR + "trained.index")
        index.add_with_ids(np.asarray(embeddings, dtype=np.float32), ids)
        faiss.write_index(index, INDEX_DIR + f"block_{block_no}.index")
        c.executemany('INSERT INTO passwords (password) VALUES (%s)', [(pw,) for pw in chunk])
        conn.commit()

    # Merging all blocks
    print("Merging index blocks...")
    index = faiss.read_index(INDEX_DIR + "trained.index")
    block_filenames = [INDEX_DIR + f"block_{bno}.index" for bno in range(block_no+1)]
    merge_ondisk(index, block_filenames, INDEX_DIR + "merged_index.ivfdata")
    faiss.write_index(index, FINAL_DIR + '/final.index')

    conn.close()
    print("Done.")
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