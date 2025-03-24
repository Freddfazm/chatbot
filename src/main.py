from flask import Flask, jsonify, render_template, request, abort
import os
import json
from confluence_fetcher import ConfluenceFetcher

app = Flask(__name__, 
            template_folder='Templates')  # Case-sensitive folder name

# Define placeholder for Confluence content
confluence_content = []

# Get content from Confluence and store it
def fetch_confluence_content():
    fetcher = ConfluenceFetcher()
    
    # Get all pages
    pages = fetcher.get_all_pages()
    
    # Extract content
    content = fetcher.extract_content(pages)
    
    # Save to JSON file
    with open('confluence_content.json', 'w', encoding='utf-8') as f:
        json.dump(content, f, ensure_ascii=False, indent=4)
    
    return content

# Route for home page
@app.route('/')
def home():
    return jsonify({
        "status": "online",
        "message": "Confluence chatbot is running"
    })

# Route for widget - using the existing template
@app.route('/widget')
def widget():
    try:
        return render_template('widget.html')
    except Exception as e:
        return f"Error loading template: {str(e)}", 500

# API endpoint for the chatbot to ask questions
@app.route('/ask', methods=['POST'])
def ask():
    data = request.json
    if not data or 'text' not in data:
        abort(400, "Missing 'text' field in request")
    
    question = data.get('text', '')
    
    # Simple placeholder response - replace with real implementation
    return jsonify({
        "answer": f"Echo: {question}"
    })

# Route to fetch content
@app.route('/fetch-content')
def get_content():
    try:
        content = fetch_confluence_content()
        return jsonify({
            "status": "success",
            "message": "Content fetched successfully",
            "count": len(content)
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

if __name__ == "__main__":
    # Get port from environment variable (Heroku sets this)
    port = int(os.environ.get("PORT", 5000))
    
    # Print diagnostic information
    print(f"Starting Flask app on port {port}")
    print(f"Current directory: {os.getcwd()}")
    print(f"Directory contents: {os.listdir()}")
    print(f"Template folder: {os.path.join(os.getcwd(), 'src', 'Templates')}")
    print(f"Template folder exists: {os.path.exists(os.path.join(os.getcwd(), 'src', 'Templates'))}")
    
    # Run the app - THIS MUST BE THE LAST THING IN THE FILE
    app.run(host='0.0.0.0', port=port)