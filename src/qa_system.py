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

        # Filter out None values and prepare context from relevant chunks
        documents = [doc for doc in results['documents'][0] if doc is not None]
        
        # If all documents were None, handle that case
        if not documents:
            return {
                'answer': "I couldn't find any relevant information to answer your question.",
                'sources': []
            }
        
        context = "\n".join(documents)
        
        # DEBUG: Print first 500 chars of context
        print(f"Context preview: {context[:500]}...")
        
        # IMPROVED PROMPT: More directive and explicit
        prompt = f"""Answer the following question based ONLY on the provided context information.
        
        Context:
        {context}
        
        Question: {question}
        
        Important instructions:
        1. If the context contains ANY information related to the question, use it to provide a detailed answer.
        2. If the context contains step-by-step instructions related to the question, include those steps in your answer.
        3. If the context contains partial information, provide what you can based on that partial information.
        4. ONLY say "I don't have specific information about that topic" if the context contains ABSOLUTELY NOTHING related to the question.
        5. DO NOT make up information that isn't in the context.
        6. Format your answer clearly, using bullet points or numbered lists if appropriate.
        """

        # Get response from GPT using the new API format with the latest model
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that answers questions based ONLY on the provided context. Your job is to extract and present information from the context, not to use your general knowledge."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2  # Lower temperature for more focused answers
        )

        # Filter out None values from metadatas URLs as well
        sources = []
        if results['metadatas'] and results['metadatas'][0]:
            for metadata in results['metadatas'][0]:
                if metadata and 'url' in metadata and metadata['url'] is not None:
                    sources.append(metadata['url'])

        return {
            'answer': response.choices[0].message.content,
            'sources': sources
        }    
    def clear_knowledge_base(self):
        """
        Completely clear all documents from the knowledge base.
        """
        try:
            # Get current document count
            before_count = self.collection.count()
            
            # Get all document IDs
            result = self.collection.get()
            if result and 'ids' in result and result['ids']:
                # Delete all documents by their IDs
                self.collection.delete(ids=result['ids'])
                
                # Verify deletion
                after_count = self.collection.count()
                
                return {
                    "success": True,
                    "message": f"Knowledge base cleared. Removed {before_count - after_count} documents."
                }
            else:
                return {
                    "success": True,
                    "message": "Knowledge base is already empty."
                }
        except Exception as e:
            print(f"Error clearing knowledge base: {str(e)}")
            return {
                "success": False,
                "message": f"Error clearing knowledge base: {str(e)}"
            }            