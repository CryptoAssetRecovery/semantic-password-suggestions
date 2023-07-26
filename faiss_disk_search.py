import faiss, sqlite3, argparse
from sentence_transformers import SentenceTransformer
import numpy as np
from faiss_disk import compute_embeddings

def get_similar_passwords(new_password: str, k: int = 15):
    # Compute the embedding of the new password
    new_password_embedding = np.array(compute_embeddings([new_password]))

    # Load the FAISS index from disk
    index = faiss.read_index('faiss_index/final.index')

    # Retrieve the n most similar passwords
    D, I = index.search(new_password_embedding, k)

    # Connect to the database
    conn = sqlite3.connect('faiss_index/pwd_index.db')
    c = conn.cursor()

    # Retrieve the original passwords
    similar_passwords = [c.execute(f'SELECT password FROM passwords WHERE id=?', (str(i),)).fetchone()[0] 
                         for i in I[0]]

    # Close the connection
    conn.close()

    return similar_passwords

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="An implementation of FAISS for password search.",
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-p", "--password", help="The password you would like to query for.", required=True)
    args = parser.parse_args()

    for i in get_similar_passwords(args.password):
        print(i)