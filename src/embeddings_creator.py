import json
import openai
import chromadb
from chromadb.utils import embedding_functions
import tiktoken
import os
from dotenv import load_dotenv

load_dotenv()

openai.api_key = os.getenv('OPENAI_API_KEY')

class ContentProcessor:
    def __init__(self):
        self.chroma_client = chromadb.Client()
        self.openai_ef = embedding_functions.OpenAIEmbeddingFunction(
            api_key=os.getenv('OPENAI_API_KEY'),
            model_name="text-embedding-ada-002"
        )
        self.collection = self.chroma_client.create_collection(
            name="confluence_kb",
            embedding_function=self.openai_ef
        )

    def chunk_text(self, text, chunk_size=500):
        enc = tiktoken.encoding_for_model("gpt-3.5-turbo")
        tokens = enc.encode(text)
        chunks = []
        
        for i in range(0, len(tokens), chunk_size):
            chunk = enc.decode(tokens[i:i + chunk_size])
            chunks.append(chunk)
        return chunks

    def process_content(self, json_file='confluence_content.json'):
        with open(json_file, 'r', encoding='utf-8') as f:
            content = json.load(f)

        for article in content:
            chunks = self.chunk_text(article['content'])
            
            for i, chunk in enumerate(chunks):
                self.collection.add(
                    documents=[chunk],
                    metadatas=[{
                        "title": article['title'],
                        "url": article['url'],
                        "chunk_id": i
                    }],
                    ids=[f"{article['id']}-{i}"]
                )
