# search.py

import faiss
import sqlite3
import argparse
import numpy as np
from sentence_transformers import SentenceTransformer
from contextlib import closing
from update_vector_db import compute_embeddings

FAISS_INDEX_FILE = 'faiss_index/final.index'
DATABASE_FILE = 'faiss_index/pwd_index.db'

def get_similar_passwords(new_password: str, k: int = 15):
    # Compute the embedding of the new password
    new_password_embedding = np.array(compute_embeddings([new_password]))

    # Load the FAISS index from disk
    index = faiss.read_index(FAISS_INDEX_FILE)

    # Retrieve the n most similar passwords
    D, I = index.search(new_password_embedding, k)

    # Connect to the database
    with closing(sqlite3.connect(DATABASE_FILE)) as conn:
        c = conn.cursor()

        # Retrieve the original passwords
        similar_passwords = [c.execute('SELECT password FROM passwords WHERE id=?', (i,)).fetchone()[0] 
                            for i in I[0]]
    return similar_passwords

def main():
    parser = argparse.ArgumentParser(description="An implementation of FAISS for password search.",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-p", "--password", help="The password you would like to query for.", required=True)
    args = parser.parse_args()

    for password in get_similar_passwords(args.password):
        print(password)

if __name__ == "__main__":
    main()
