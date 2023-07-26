import chromadb
from chromadb.config import Settings

def check_heartbeat():
    client = chromadb.HttpClient(host='localhost', port=8000, settings=Settings(anonymized_telemetry=False))
    try:
        return client.heartbeat()
    except:
        return False
    
if __name__ == "__main__":
    print(check_heartbeat())