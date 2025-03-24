from flask import Flask, jsonify, render_template, request
import os
import json
import re

app = Flask(__name__, template_folder='Templates')

# Cache for the knowledge base
knowledge_base = None

def load_knowledge_base():
    """Load the knowledge base from the JSON file"""
    global knowledge_base
    
    if knowledge_base is not None:
        return knowledge_base
    
    try:
        # Try to load from the saved JSON file
        kb_path = 'confluence_content.json'
        # If running on Heroku, the file may be in a different location
        if not os.path.exists(kb_path):
            kb_path = os.path.join(os.path.dirname(__file__), '..', 'confluence_content.json')
        
        if os.path.exists(kb_path):
            with open(kb_path, 'r', encoding='utf-8') as f:
                knowledge_base = json.load(f)
                print(f"Loaded {len(knowledge_base)} items from knowledge base")
                return knowledge_base
        else:
            print(f"Knowledge base file not found at {kb_path}")
            # Create a simple fallback knowledge base
            knowledge_base = [
                {
                    "title": "Unlock a listing",
                    "content": "To unlock a listing, go to the listing page and click on the 'Unlock' button in the top right corner. You need admin permissions to do this."
                },
                {
                    "title": "Knowledge Base Info",
                    "content": "The knowledge base is being built. Please check back later for more information."
                }
            ]
            return knowledge_base
    except Exception as e:
        print(f"Error loading knowledge base: {str(e)}")
        return []

def search_knowledge_base(query):
    """Search the knowledge base for relevant content"""
    kb = load_knowledge_base()
    if not kb:
        return "I couldn't access the knowledge base. Please try again later."
    
    # Convert query to lowercase for case-insensitive matching
    query_lower = query.lower()
    
    # Simple keyword-based search
    matches = []
    for item in kb:
        title = item.get("title", "").lower()
        content = item.get("content", "").lower()
        
        # Calculate a simple relevance score
        score = 0
        
        # Check for exact phrase matches (weighted higher)
        if query_lower in title:
            score += 10
        if query_lower in content:
            score += 5
            
        # Check for individual word matches
        words = re.findall(r'\w+', query_lower)
        for word in words:
            if len(word) > 3:  # Only consider words longer than 3 chars
                if word in title:
                    score += 3
                if word in content:
                    score += 1
                    
        if score > 0:
            matches.append({
                "item": item,
                "score": score
            })
    
    # Sort by relevance score
    matches.sort(key=lambda x: x["score"], reverse=True)
    
    if matches:
        # Return the most relevant item
        best_match = matches[0]["item"]
        return f"According to our knowledge base: {best_match['content']}"
    else:
        return "I couldn't find information about that in our knowledge base. Please try rephrasing your question or contact support."

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

@app.route('/')
def home():
    return jsonify({
        "status": "online",
        "message": "Confluence chatbot is running"
    })

@app.route('/widget')
def widget():
    return render_template('widget.html')

@app.route('/ask', methods=['POST', 'OPTIONS'])
def ask():
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        data = request.json
        print(f"Received request at /ask: {data}")
        
        if not data or 'text' not in data:
            return jsonify({"error": "Missing 'text' field"}), 400
            
        question = data.get('text', '')
        print(f"Question: {question}")
        
        # Search the knowledge base for an answer
        answer = search_knowledge_base(question)
        
        return jsonify({
            "answer": answer
        })
    except Exception as e:
        print(f"Error processing request: {str(e)}")
        return jsonify({"error": str(e)}), 500
        
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)