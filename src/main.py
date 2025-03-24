from confluence_fetcher import ConfluenceFetcher
import json
import os
from flask import Flask

app = Flask(__name__)

@app.route('/')
def index():
    return "Confluence Content Fetcher is running!"

@app.route('/fetch')
def fetch_content():
    fetcher = ConfluenceFetcher()
    pages = fetcher.get_all_pages()
    content = fetcher.extract_content(pages)
    
    # Save to JSON file
    with open('confluence_content.json', 'w', encoding='utf-8') as f:
        json.dump(content, f, ensure_ascii=False, indent=4)
    
    return "Content fetched successfully!"

if __name__ == "__main__":
    # Run the Flask app
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)