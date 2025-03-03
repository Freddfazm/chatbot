from dotenv import load_dotenv
import os

load_dotenv()

CONFLUENCE_URL = os.getenv('CONFLUENCE_URL')
CONFLUENCE_USERNAME = os.getenv('CONFLUENCE_USERNAME')
CONFLUENCE_API_TOKEN = os.getenv('CONFLUENCE_API_TOKEN')
SPACE_KEY = os.getenv('SPACE_KEY')
