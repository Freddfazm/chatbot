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
        
        # Set the model to use
        self.model = "gpt-4-turbo"  # Using latest model
        print(f"Using model: {self.model}")  # Debug print
        
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

    def get_answer(self, question, n_results=5):  # Increased from 3 to 5 results
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
        
        # DEBUG: Print first 500 chars of context
        print(f"Context preview: {context[:500]}...")
        
        # Create prompt for GPT - modified to be more flexible
        prompt = f"""Answer the following question based on the provided context information. 
        Try to be helpful even if the information is not completely explicit in the context.
        If the context provides ANY relevant information that might help answer the question, use it.
        If you truly don't have ANY information related to the question, say "I don't have specific information about that topic."
        
        Context:
        {context}
        
        Question: {question}"""

        # Get response from GPT using the new API format with the latest model
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that answers questions based on the provided context. Extract as much relevant information as possible from the context to provide detailed, accurate answers."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3  # Lower temperature for more focused answers
        )

        return {
            'answer': response.choices[0].message.content,
            'sources': [m['url'] for m in results['metadatas'][0]]
        }
        
    def clear_knowledge_base(self):
        """
        Completely clear all documents from the knowledge base.
        """
        try:
            # Delete all documents from the collection
            self.collection.delete(where={})
            doc_count = self.collection.count()
            return {
                "success": True,
                "message": f"Knowledge base cleared. Collection now has {doc_count} documents."
            }
        except Exception as e:
            print(f"Error clearing knowledge base: {str(e)}")
            return {
                "success": False,
                "message": f"Error clearing knowledge base: {str(e)}"
            }