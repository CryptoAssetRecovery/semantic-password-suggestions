# Semantic Similarity Search for Password Canditate Generation
This is a beta demo of a semanic search password candidate generator implementing a FAISS Vector DB and embeddings. Passwords are converted to embeddings and stored in the vector db. The embeddings ids are linked to their corresponding password in an sqlite3 persistent db for reference after search.

## Installation:

### Step 1: Setup environment
To install the required dependancies, in the project root, run:
```
python3 -m venv env/ && source env/bin/activate
```

### Step 2: Build Vector DB
To load the vector db, run the following command in the project root:
```
python3 update_vector_db.py -w passwords/top100k.txt
```
Then the upload should begin:
```
Progress: 50000/14344390 lines processed, 0.35% done.
Progress: 100000/14344390 lines processed, 0.70% done.
Progress: 150000/14344390 lines processed, 1.05% done.
Progress: 200000/14344390 lines processed, 1.39% done.
```

### Step 3: Perform a Semantic Search
To perform a search on the FAISS db, you can run the command:
```
python3 search.py -p examplePa55word
```