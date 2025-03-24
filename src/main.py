from confluence_fetcher import ConfluenceFetcher
import json
import os
from flask import Flask, jsonify

app = Flask(__name__)

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
    # Fetch content on startup (optional)
    # fetch_confluence_content()
    # Run the app
    app.run(host='0.0.0.0', port=port)