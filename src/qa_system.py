import os
import openai
from chromadb.utils import embedding_functions
import chromadb

class QASystem:
    def __init__(self):
        # Use absolute path for persistent storage
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        db_path = os.path.join(base_dir, "chroma_db")
        print(f"Looking for ChromaDB at: {db_path}")  # Debug print
        
        # Create the directory if it doesn't exist
        os.makedirs(db_path, exist_ok=True)
        
        # Use persistent client with absolute path
        self.chroma_client = chromadb.PersistentClient(path=db_path)
        
        # Initialize OpenAI client
        self.client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.openai_ef = embedding_functions.OpenAIEmbeddingFunction(
            api_key=os.getenv('OPENAI_API_KEY'),
            model_name="text-embedding-ada-002"
        )
        
        # Get the collection
        try:
            self.collection = self.chroma_client.get_collection(
                name="confluence_kb",
                embedding_function=self.openai_ef
            )
            doc_count = self.collection.count()
            print(f"Found collection with {doc_count} documents")  # Debug print
        except Exception as e:
            print(f"Error getting collection: {str(e)}")
            # Create the collection if it doesn't exist
            self.collection = self.chroma_client.create_collection(
                name="confluence_kb",
                embedding_function=self.openai_ef
            )
            print("Created new collection")

    def get_answer(self, question, n_results=3):
        # Check if collection has any documents
        doc_count = self.collection.count()
        print(f"Collection has {doc_count} documents")  # Debug print
        
        if not doc_count:
            return {
                'answer': "I don't have any information yet. Please add documents to the knowledge base first.",
                'sources': []
            }
            
        # Query the vector database
        results = self.collection.query(
            query_texts=[question],
            n_results=n_results
        )

        # Debug print
        print(f"Query results: Found {len(results['documents'][0]) if results['documents'] and results['documents'][0] else 0} documents")

        # Handle empty results
        if not results['documents'] or not results['documents'][0]:
            return {
                'answer': "I couldn't find any relevant information to answer your question.",
                'sources': []
            }

        # Prepare context from relevant chunks
        context = "\n".join(results['documents'][0])
        
        # Create prompt for GPT
        prompt = f"""Based on the following context, answer the question. 
        If the answer cannot be found in the context, say "I don't have enough information to answer that."
        
        Context:
        {context}
        
        Question: {question}"""

        # Get response from GPT using the new API format
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that answers questions based on the provided context."},
                {"role": "user", "content": prompt}
            ]
        )

        return {
            'answer': response.choices[0].message.content,
            'sources': [m['url'] for m in results['metadatas'][0]]
        }