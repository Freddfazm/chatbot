from confluence_fetcher import ConfluenceFetcher
import json

def main():
    fetcher = ConfluenceFetcher()
    
    # Get all pages
    pages = fetcher.get_all_pages()
    
    # Extract content
    content = fetcher.extract_content(pages)
    
    # Save to JSON file
    with open('confluence_content.json', 'w', encoding='utf-8') as f:
        json.dump(content, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    main()
