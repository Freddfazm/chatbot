from flask import Flask, jsonify, render_template, request
import os
from qa_system import QASystem

app = Flask(__name__, template_folder='Templates')
qa_system = QASystem()  # Initialize the QA system

@app.route('/')
def home():
    return jsonify({
        "status": "online",
        "message": "Confluence chatbot is running"
    })

@app.route('/widget')
def widget():
    return render_template('widget.html')

@app.route('/ask', methods=['POST'])
def ask():
    try:
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
        # Check for admin key (for security)
        admin_key = request.headers.get('X-Admin-Key')
        if admin_key != os.environ.get('ADMIN_SECRET_KEY'):
            return jsonify({"error": "Unauthorized"}), 401
            
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
        # Check for admin key (for security)
        admin_key = request.headers.get('X-Admin-Key')
        if admin_key != os.environ.get('ADMIN_SECRET_KEY'):
            return jsonify({"error": "Unauthorized"}), 401
            
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

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))    
    app.run(host='0.0.0.0', port=port)