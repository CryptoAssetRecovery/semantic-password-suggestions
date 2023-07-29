# search.py

import os
import json
import faiss
import psycopg2
import argparse
import numpy as np
from typing import Optional
from faiss_updatedb import compute_embeddings
from contextlib import closing
from dotenv import load_dotenv

load_dotenv()

FAISS_DIR = os.getenv("FINAL_DIR") # Directory to save the final index
OUT_FILE = os.getenv('OUT_FILE')
DB_SETTINGS = {
    'dbname': os.getenv("DB_NAME"),
    'user': os.getenv("DB_USER"),
    'password': os.getenv("DB_PASSWORD"),
    'host': os.getenv("DB_HOST"),
    'port': os.getenv("DB_PORT")
}

def get_similar_passwords(new_password: str, k: int = 15):
    # Compute the embedding of the new password
    new_password_embedding = np.array(compute_embeddings([new_password]))

    # Load the FAISS index from disk
    index_file = os.path.join(os.getcwd(), FAISS_DIR, 'final.index')  # Use an absolute path
    print(f"Loading index from: {index_file}")  # For debugging the path
    index = faiss.read_index(index_file)
    print('Index loaded')

    # Retrieve the n most similar passwords
    distances, ans = index.search(new_password_embedding, k)

    data = {}
    for i, ans_index in enumerate(ans[0]):
        data[str(ans_index)] = {"distance": distances[0][i], "password": None}

    # Connect to the database
    with closing(psycopg2.connect(**DB_SETTINGS)) as conn:
        c = conn.cursor()

        # Retrieve the original passwords
        for index in ans[0]:
            try:
                c.execute('SELECT password FROM passwords WHERE id=%s', (int(index),))
                password = c.fetchone()[0]
                data[str(index)]["password"] = password
            except:
                pass

    data_list = [{"distance": value["distance"], "password": value["password"]} for key, value in data.items()]
    sorted_data_list = sorted(data_list, key=lambda x: x['distance'])

    return sorted_data_list

class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, (np.float32, np.float64)):
            return float(obj)
        return json.JSONEncoder.default(self, obj)

def main():
    parser = argparse.ArgumentParser(description="An implementation of FAISS for password search.",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-p", "--password", help="The password you would like to query for.")
    parser.add_argument("-w", "--wordlist", help="Alternative to '-p'. A text file with line deliniated passwords to query.")
    parser.add_argument("-k", "--top_k", help="The number of suggestions you'd like displayed for each password guess.")
    args = parser.parse_args()

    if args.password and args.wordlist or not args.password and not args.wordlist:
        print('Please provide one argument: Either a single target password (-p) or a passwordlist file path (-w)')
        exit()

    data = {}
    if args.password:
        if args.top_k:
            data[args.password] = get_similar_passwords(args.password, args.top_k)
        else:
            data[args.password] = get_similar_passwords(args.password)
    
    elif args.wordlist:
        with open(args.wordlist, 'r', errors='ignore', encoding='latin-1') as f:
            for line in f:
                if not line.startswith('#'):  # Ignore comment lines
                    pwd = line.strip()  # Remove trailing newline character
                    if args.top_k:
                        data[pwd] = get_similar_passwords(pwd, args.top_k)
                    else:
                        data[pwd] = get_similar_passwords(pwd)

    with open(OUT_FILE, 'w') as f:
        json.dump(data, f, indent=4, cls=NumpyEncoder)       

if __name__ == "__main__":
    main()
