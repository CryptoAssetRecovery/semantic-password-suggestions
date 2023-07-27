# search.py

import json
import faiss
import sqlite3
import argparse
import numpy as np
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
    distances, ans = index.search(new_password_embedding, k)

    data = {}
    for i, ans_index in enumerate(ans[0]):
        # Create a dictionary of the distances and the answers, sorted by distances
        data[str(ans_index)] = {"distance": distances[0][i], "password": None}

    # Connect to the database
    with closing(sqlite3.connect(DATABASE_FILE)) as conn:
        c = conn.cursor()

        # Retrieve the original passwords
        for index in ans[0]:
            password = c.execute('SELECT password FROM passwords WHERE id=?', (str(index),)).fetchone()[0]
            data[str(index)]["password"] = password

    # Now, we convert the dictionary to a list of dictionaries to be able to sort by distance
    data_list = [{"index": key, "distance": value["distance"], "password": value["password"]} for key, value in data.items()]
    sorted_data_list = sorted(data_list, key=lambda x: x['distance'])

    #json_data = json.dumps(sorted_data_list)
    return sorted_data_list

def main():
    parser = argparse.ArgumentParser(description="An implementation of FAISS for password search.",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-p", "--password", help="The password you would like to query for.", required=True)
    args = parser.parse_args()

    for password in get_similar_passwords(args.password):
        print(password)

if __name__ == "__main__":
    main()
