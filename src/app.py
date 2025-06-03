from flask import Flask, jsonify, render_template, request
import os
import json
from qa_system import QASystem
from confluence_fetcher import ConfluenceFetcher
from flask_cors import CORS  # Add this import at the top

app = Flask(__name__, template_folder='Templates')
CORS(app, resources={r"/ask": {"origins": "*"}, r"/api/chat": {"origins": "*"}})  # Add CORS support
qa_system = QASystem()  # Initialize the QA system

# Function to check and reinitialize QA system if needed
def ensure_qa_system():
    global qa_system
    try:
        # Try to access the collection to check if it's valid
        _ = qa_system.collection.count()
    except Exception as e:
        print(f"QA system error, reinitializing: {str(e)}")
        # Reinitialize the QA system
        qa_system = QASystem()

@app.route('/')
def home():
    return jsonify({
        "status": "online",
        "message": "Confluence chatbot is running"
    })

@app.route('/widget')
def widget():
    return render_template('widget.html')

@app.route('/embed')
def embed():
    """Render the embedded chat interface"""
    return render_template('embed.html')

@app.route('/embed-code')
def embed_code():
    """Render the embed code page"""
    domain = request.host_url.rstrip('/')
    return render_template('embed_code.html', domain=domain)

@app.route('/ask', methods=['POST'])
def ask():
    try:
        # Ensure QA system is initialized
        ensure_qa_system()
        
        data = request.json
        if not data or 'text' not in data:
            return jsonify({"error": "Missing 'text' field"}), 400
            
        question = data.get('text', '')
        print(f"Received question: {question}")
        
        # Use the QA system to get an answer
        result = qa_system.get_answer(question)
        
        return jsonify(result)
    except Exception as e:
        print(f"Error processing request: {str(e)}")
        return jsonify({"error": str(e), "answer": "Sorry, I encountered an error processing your request."}), 500

@app.route('/clear-kb', methods=['POST'])
def clear_knowledge_base():
    """Completely clear the knowledge base"""
    try:
        # Call the clear method
        result = qa_system.clear_knowledge_base()
        
        if result["success"]:
            return jsonify({
                "status": "success",
                "message": result["message"]
            })
        else:
            return jsonify({
                "status": "error",
                "message": result["message"]
            }), 500
    except Exception as e:
        print(f"Error clearing knowledge base: {str(e)}")
        return jsonify({"error": str(e)}), 500
@app.route('/refresh-kb', methods=['POST'])
def refresh_knowledge_base():
    """Completely refresh the knowledge base by clearing it and adding new content"""
    try:
        # Step 1: Clear the existing knowledge base
        clear_result = qa_system.clear_knowledge_base()
        if not clear_result["success"]:
            return jsonify({
                "status": "error", 
                "message": f"Failed to clear knowledge base: {clear_result['message']}"
            }), 500
            
        # Step 2: Fetch new content from Confluence
        fetcher = ConfluenceFetcher()
        pages = fetcher.get_all_pages()
        content = fetcher.extract_content(pages)
        
        # Step 3: Save to JSON file
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        json_path = os.path.join(base_dir, 'confluence_content.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(content, f, ensure_ascii=False, indent=4)
        
        # Step 4: Add content to the vector database
        added_count = add_content_to_chroma(content, qa_system.collection)
        
        return jsonify({
            "status": "success",
            "message": f"Knowledge base refreshed successfully. Cleared existing data and added {added_count} new documents."
        })
    except Exception as e:
        print(f"Error refreshing knowledge base: {str(e)}")
        return jsonify({"error": str(e)}), 500
@app.route('/admin')
def admin():
    # Optional: Add basic authentication here for security
    return render_template('admin.html')

@app.route('/update-kb', methods=['POST'])
def update_knowledge_base():
    """Force an update of the knowledge base from Confluence"""
    try:
        # Step 1: Fetch new content from Confluence
        fetcher = ConfluenceFetcher()
        pages = fetcher.get_all_pages()
        content = fetcher.extract_content(pages)
        
        # Step 2: Save to JSON file
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        json_path = os.path.join(base_dir, 'confluence_content.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(content, f, ensure_ascii=False, indent=4)
        
        # Step 3: Add content to the vector database
        added_count = add_content_to_chroma(content, qa_system.collection)
        
        return jsonify({
            "status": "success",
            "message": f"Knowledge base updated successfully. Added {added_count} documents."
        })
    except Exception as e:
        print(f"Error updating knowledge base: {str(e)}")
        return jsonify({"error": str(e)}), 500

def add_content_to_chroma(content, collection):
    """Add content to ChromaDB collection"""
    # Prepare documents for batch insertion
    documents = []
    metadatas = []
    ids = []
    
    # Process each content item
    count = 0
    for item in content:
        if 'title' in item and 'content' in item and 'url' in item:
            # Create a document with title and content
            doc = f"Title: {item['title']}\n\n{item['content']}"
            
            # Add to batches
            documents.append(doc)
            metadatas.append({"url": item['url'], "title": item['title']})
            ids.append(f"doc_{count}")
            
            count += 1
    
    # Add documents to collection in batches
    if documents:
        collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        
    return count
@app.route('/embed-code')
def get_embed_code():  # Changed function name from embed_code to get_embed_code
      """Render the page with embeddable code snippet"""
      domain = request.host_url.rstrip('/')  # Get the current domain
      return render_template('embed_code.html', domain=domain)
@app.route('/embed')
def embed():
      """Render the embedded chat interface"""
      return render_template('embed.html')
@app.route('/rebuild-kb', methods=['POST'])
def rebuild_knowledge_base():
    """Rebuild the knowledge base by recreating the collection and adding content"""
    try:
        # Step 1: Delete the existing collection
        try:
            qa_system.chroma_client.delete_collection(name="confluence_kb")
            print("Deleted existing collection")
        except Exception as e:
            print(f"Error deleting collection: {str(e)}")
        
        # Step 2: Create a new collection
        qa_system.collection = qa_system.chroma_client.create_collection(
            name="confluence_kb",
            embedding_function=qa_system.openai_ef
        )
        print("Created new collection")
        
        # Step 3: Fetch content from Confluence
        fetcher = ConfluenceFetcher()
        pages = fetcher.get_all_pages()
        content = fetcher.extract_content(pages)
        
        # Step 4: Save to JSON file
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        json_path = os.path.join(base_dir, 'confluence_content.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(content, f, ensure_ascii=False, indent=4)
        
        # Step 5: Add content to the vector database with improved error handling
        added_count = add_content_to_chroma_improved(content, qa_system.collection)
        
        return jsonify({
            "status": "success",
            "message": f"Knowledge base rebuilt successfully. Added {added_count} documents."
        })
    except Exception as e:
        print(f"Error rebuilding knowledge base: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

def add_content_to_chroma_improved(content, collection):
    """Add content to ChromaDB collection with improved error handling"""
    # Prepare documents for batch insertion
    documents = []
    metadatas = []
    ids = []
    
    # Process each content item
    count = 0
    for item in content:
        if 'title' in item and 'content' in item and 'url' in item:
            # Validate content is not None or empty
            if item['content'] is None or item['content'].strip() == '':
                print(f"Skipping item with empty content: {item['title']}")
                continue
                
            # Create a document with title and content
            doc = f"Title: {item['title']}\n\n{item['content']}"
            
            # Validate document
            if doc and len(doc.strip()) > 10:  # Ensure document has meaningful content
                # Add to batches
                documents.append(doc)
                metadatas.append({"url": item['url'], "title": item['title']})
                ids.append(f"doc_{count}")
                
                count += 1
                print(f"Added document {count}: {item['title'][:50]}...")
            else:
                print(f"Skipping document with insufficient content: {item['title']}")
    
    # Add documents to collection in batches
    if documents:
        try:
            print(f"Adding {len(documents)} documents to collection")
            collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            print("Documents added successfully")
        except Exception as e:
            print(f"Error adding documents to collection: {str(e)}")
            import traceback
            traceback.print_exc()
    else:
        print("No valid documents to add")
        
    return count

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))    
    app.run(host='0.0.0.0', port=port)