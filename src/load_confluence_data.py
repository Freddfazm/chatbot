import os
import json
import openai
from chromadb.utils import embedding_functions
import chromadb
import hashlib
import re
from bs4 import BeautifulSoup

def clean_html_content(html_content):
    """
    Clean HTML content by removing HTML tags and normalizing whitespace.
    """
    # Use BeautifulSoup to parse HTML
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Get text content
    text = soup.get_text(separator=' ')
    
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def load_confluence_to_kb(json_file_path="confluence_content.json"):
    """
    Load Confluence content from a JSON file into the knowledge base.
    """
    # Read the JSON file
    try:
        with open(json_file_path, 'r', encoding='utf-8') as file:
            confluence_data = json.load(file)
        
        print(f"Successfully loaded JSON file. Found {len(confluence_data)} pages.")
    except Exception as e:
        return f"Error reading the JSON file: {str(e)}"

    # Initialize ChromaDB client with persistent storage using absolute path
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(base_dir, "chroma_db")
    print(f"Storing ChromaDB at: {db_path}")
    
    # Create the directory if it doesn't exist
    os.makedirs(db_path, exist_ok=True)
    
    chroma_client = chromadb.PersistentClient(path=db_path)
    openai_ef = embedding_functions.OpenAIEmbeddingFunction(
        api_key=os.getenv('OPENAI_API_KEY'),
        model_name="text-embedding-ada-002"
    )    # Get or create the collection
    collection = chroma_client.get_or_create_collection(
        name="confluence_kb",
        embedding_function=openai_ef
    )
    
    # Prepare data for ChromaDB
    ids = []
    contents = []
    metadatas = []
    
    # Process the Confluence data based on the structure provided
    for page in confluence_data:
        # Extract fields directly from the JSON structure
        page_id = page.get('id', 'unknown_id')
        page_title = page.get('title', 'Untitled Page')
        page_content = page.get('content', '')
        page_url = page.get('url', '')
        
        # Clean HTML content
        clean_content = clean_html_content(page_content)
        
        # Skip if no content
        if not clean_content:
            print(f"Skipping page '{page_title}' (ID: {page_id}) - No content after cleaning")
            continue
            
        # Generate a unique ID for each page
        doc_id = f"confluence_{page_id}"
        
        ids.append(doc_id)
        contents.append(clean_content)
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
    # Install required packages if not already installed
    try:
        import bs4
    except ImportError:
        import subprocess
        print("Installing BeautifulSoup4...")
        subprocess.check_call(["pip", "install", "beautifulsoup4"])
        print("BeautifulSoup4 installed successfully.")
    
    # You can specify the path to your JSON file or keep the default
    result = load_confluence_to_kb("confluence_content.json")
    print(result)