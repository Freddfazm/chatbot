import os
import json
import chromadb
from chromadb.utils import embedding_functions

def verify_kb_import(json_file_path="confluence_content.json"):
    """
    Verify if documents from the JSON file have been imported into the knowledge base.
    """
    # Initialize ChromaDB client with persistent storage - use the same path
    chroma_client = chromadb.PersistentClient(path="./chroma_db")
    openai_ef = embedding_functions.OpenAIEmbeddingFunction(
        api_key=os.getenv('OPENAI_API_KEY'),
        model_name="text-embedding-ada-002"
    )    
    # Try to get the collection
    try:
        collection = chroma_client.get_collection(
            name="confluence_kb",
            embedding_function=openai_ef
        )
    except Exception as e:
        return f"Error accessing collection: {str(e)}"
    
    # Get count of documents in collection
    doc_count = collection.count()
    
    # Read the JSON file to compare
    try:
        with open(json_file_path, 'r', encoding='utf-8') as file:
            confluence_data = json.load(file)
    except Exception as e:
        return f"Error reading the JSON file: {str(e)}"
    
    print(f"Knowledge base contains {doc_count} documents.")
    print(f"JSON file contains {len(confluence_data)} documents.")
    
    # Check for specific documents
    if doc_count > 0:
        # Check a few specific documents by ID
        sample_size = min(5, len(confluence_data))
        for i in range(sample_size):
            page_id = confluence_data[i].get('id', 'unknown_id')
            page_title = confluence_data[i].get('title', 'Untitled')
            doc_id = f"confluence_{page_id}"
            
            # Try to retrieve the document by ID
            try:
                result = collection.get(ids=[doc_id])
                if result and result['ids']:
                    print(f"✓ Found document: '{page_title}' (ID: {doc_id})")
                else:
                    print(f"✗ Document not found: '{page_title}' (ID: {doc_id})")
            except Exception as e:
                print(f"✗ Error checking document '{page_title}': {str(e)}")
        
        # Perform a simple query to test retrieval
        print("\nPerforming a test query...")
        query_results = collection.query(query_texts=["company policy"], n_results=1)
        if query_results and query_results['documents'] and query_results['documents'][0]:
            print(f"Query returned: '{query_results['metadatas'][0][0]['title']}'")
            print(f"URL: {query_results['metadatas'][0][0]['url']}")
        else:
            print("Query did not return any results.")
    
    return f"Verification complete. KB: {doc_count} docs, JSON: {len(confluence_data)} docs."

if __name__ == "__main__":
    result = verify_kb_import("confluence_content.json")
    print(result)
