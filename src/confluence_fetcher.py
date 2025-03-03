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
                expand='body.storage'
            )
            
            if not results:
                break
                
            pages.extend(results)
            start += limit
            
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
