#!/usr/bin/env python3
from pymilvus import connections, Collection

connections.connect(host='localhost', port='19530')
try:
    Collection('qa_pairs').drop()
    print("Dropped collection 'qa_pairs'.")
except Exception as e:
    print(f"Could not drop collection 'qa_pairs': {e}") 