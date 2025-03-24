import os
import json
import openai
from chromadb.utils import embedding_functions
import chromadb
import hashlib

def load_confluence_to_kb(json_file_path="confluence_content.json", clear_existing=True):
    """
    Load Confluence content from a JSON file into the knowledge base.
    
    The JSON file should contain Confluence pages with their content.
    """
    # Read the JSON file
    try:
        with open(json_file_path, 'r', encoding='utf-8') as file:
            confluence_data = json.load(file)
        print(f"Successfully loaded JSON file. Found {len(confluence_data)} pages.")
    except Exception as e:
        return f"Error reading the JSON file: {str(e)}"

    # Initialize ChromaDB client with persistent storage
    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(os.path.dirname(base_dir), "chroma_db")
    print(f"Storing ChromaDB at: {db_path}")
    
    chroma_client = chromadb.PersistentClient(path=db_path)
    openai_ef = embedding_functions.OpenAIEmbeddingFunction(
        api_key=os.getenv('OPENAI_API_KEY'),
        model_name="text-embedding-ada-002"
    )
    
    # Delete the existing collection if clear_existing is True
    if clear_existing:
        try:
            chroma_client.delete_collection(name="confluence_kb")
            print("Deleted existing collection to start fresh")
        except Exception as e:
            print(f"Note: No existing collection to delete or error: {str(e)}")
    
    # Create a new collection
    collection = chroma_client.create_collection(
        name="confluence_kb",
        embedding_function=openai_ef
    )
    
    # Prepare data for ChromaDB
    ids = []
    contents = []
    metadatas = []
    
    # Process the Confluence data
    for page in confluence_data:
        # You might need to adjust these keys based on your JSON structure
        page_id = page.get('id', 'unknown_id')
        page_title = page.get('title', 'Untitled Page')
        page_content = page.get('content', '')
        page_url = page.get('url', '')
        
        # Generate a unique ID for each page
        doc_id = f"confluence_{page_id}"
        
        ids.append(doc_id)
        contents.append(page_content)
        metadatas.append({
            'url': page_url,
            'title': page_title,
            'source': 'Confluence'
        })
    
    # Add documents to the collection
    if ids:
        collection.add(
            ids=ids,
            documents=contents,
            metadatas=metadatas
        )
        return f"Added {len(ids)} Confluence pages to the knowledge base."
    else:
        return "No valid Confluence pages found in the JSON file."

if __name__ == "__main__":
    # You can specify the path to your JSON file or keep the default
    result = load_confluence_to_kb("confluence_content.json", clear_existing=True)
    print(result)