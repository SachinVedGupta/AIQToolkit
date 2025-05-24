#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) 2025, NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import argparse
import logging
from typing import List
import numpy as np

from pymilvus import Collection, connections
from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_qa_collection():
    """Create the Q&A collection in Milvus if it doesn't exist."""
    connections.connect(host='localhost', port='19530')
    
    # Define collection schema
    from pymilvus import CollectionSchema, FieldSchema, DataType
    fields = [
        FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
        FieldSchema(name="question", dtype=DataType.VARCHAR, max_length=65535),
        FieldSchema(name="answer", dtype=DataType.VARCHAR, max_length=65535),
        FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=768)
    ]
    schema = CollectionSchema(fields=fields, description="Q&A pairs collection")
    
    # Create collection if it doesn't exist
    try:
        collection = Collection("qa_pairs", schema)
        logger.info("Collection 'qa_pairs' created successfully")
    except Exception as e:
        logger.info(f"Collection 'qa_pairs' already exists: {e}")
        collection = Collection("qa_pairs")
    
    # Create index
    index_params = {
        "metric_type": "L2",
        "index_type": "IVF_FLAT",
        "params": {"nlist": 1024}
    }
    collection.create_index(field_name="embedding", index_params=index_params)
    return collection

def add_qa_pair(question: str, answer: str, collection: Collection):
    """Add a Q&A pair to the Milvus collection."""
    # Initialize embedder
    embedder = NVIDIAEmbeddings(model="nvidia/nv-embedqa-e5-v5", truncate="END")
    
    # Generate embedding for the question
    question_embedding = embedder.embed_query(question)
    
    # Convert embedding to numpy array and ensure it's the right shape
    embedding_array = np.array(question_embedding, dtype=np.float32)
    logger.info(f"Embedding shape: {embedding_array.shape}")
    
    if embedding_array.shape[0] != 768:
        raise ValueError(f"Expected embedding dimension 768, got {embedding_array.shape[0]}")
    
    # Insert into Milvus - using the correct format for each field type
    data = [
        {
            "question": question,
            "answer": answer,
            "embedding": embedding_array.tolist()  # Convert to list for Milvus
        }
    ]
    
    collection.insert(data)
    collection.flush()
    logger.info(f"Added Q&A pair to collection: {question[:50]}...")

def main():
    parser = argparse.ArgumentParser(description="Add Q&A pairs to Milvus database")
    parser.add_argument("--question", required=True, help="The question to store")
    parser.add_argument("--answer", required=True, help="The answer to store")
    args = parser.parse_args()
    
    collection = create_qa_collection()
    add_qa_pair(args.question, args.answer, collection)

if __name__ == "__main__":
    main() 