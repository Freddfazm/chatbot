from atlassian import Confluence
from config import CONFLUENCE_URL, CONFLUENCE_USERNAME, CONFLUENCE_API_TOKEN, SPACE_KEY

class ConfluenceFetcher:
    def __init__(self):
        self.confluence = Confluence(
            url=CONFLUENCE_URL,
            username=CONFLUENCE_USERNAME,
            password=CONFLUENCE_API_TOKEN,
            cloud=True
        )
        
    def get_all_pages(self):
        pages = []
        start = 0
        limit = 100
        
        while True:
            results = self.confluence.get_all_pages_from_space(
                space=SPACE_KEY,
                start=start,
                limit=limit,
                expand='body.storage,metadata.labels'
            )
            
            if not results:
                break
                
            # Only add pages without the "internal" or "mls-team" labels
            for page in results:
                # Check if the page has excluded labels
                has_excluded_label = False
                if 'metadata' in page and 'labels' in page['metadata']:
                    labels = page['metadata']['labels']
                    # Check if any label has name "internal" or "mls-team"
                    for label in labels.get('results', []):
                        if label.get('name', '').lower() in ['internal', 'mls-team']:
                            has_excluded_label = True
                            break
            
                # Only add pages without the excluded labels
                if not has_excluded_label:
                    pages.append(page)
        
            start += limit
            
            # If we received fewer results than the limit, we've reached the end
            if len(results) < limit:
                break
                
        print(f"Retrieved {len(pages)} pages (excluding internal and mls-team pages)")
        return pages    
    def extract_content(self, pages):
        content = []
        for page in pages:
            article = {
                'title': page['title'],
                'content': page['body']['storage']['value'],
                'id': page['id'],
                'url': f"{CONFLUENCE_URL}/wiki/spaces/{SPACE_KEY}/pages/{page['id']}"
            }
            content.append(article)
        return content