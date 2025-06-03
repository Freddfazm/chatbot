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

    def get_answer(self, question, n_results=5):
        # Check if collection has any documents
        doc_count = self.collection.count()
        print(f"Collection has {doc_count} documents")  # Debug print
    
        if not doc_count:
            print("No documents in collection")
            return {
                'answer': "I don't have any information yet. Please add documents to the knowledge base first.",
                'sources': []
            }
        
        # Query the vector database
        try:
            results = self.collection.query(
                query_texts=[question],
                n_results=n_results
            )
        
            # Debug print query results structure
            print(f"Query results structure: {type(results)}")
            print(f"Query results keys: {results.keys()}")
        
            # Check if documents exist in results
            if 'documents' not in results or not results['documents']:
                print("No 'documents' in query results or empty documents list")
                return {
                    'answer': "I couldn't find any relevant information to answer your question.",
                    'sources': []
                }
            
            # Check if documents[0] exists and has content
            if not results['documents'][0]:
                print("Empty documents[0] list")
                return {
                    'answer': "I couldn't find any relevant information to answer your question.",
                    'sources': []
                }
            
            # Print the actual documents for debugging
            print(f"Documents found: {len(results['documents'][0])}")
            for i, doc in enumerate(results['documents'][0]):
                print(f"Document {i}: Type={type(doc)}, Value={doc[:100] if doc else 'None'}")
        
            # Filter out None values and prepare context from relevant chunks
            documents = [doc for doc in results['documents'][0] if doc is not None]
            print(f"After filtering None values: {len(documents)} documents remain")
        
            # If all documents were None, handle that case
            if not documents:
                print("All documents were None")
                return {
                    'answer': "I couldn't find any relevant information to answer your question.",
                    'sources': []
                }
        
            # Join documents into context
            try:
                context = "\n".join(documents)
                print(f"Successfully joined {len(documents)} documents into context")
            except Exception as e:
                print(f"Error joining documents: {str(e)}")
                # Try to identify problematic documents
                for i, doc in enumerate(documents):
                    print(f"Document {i} type: {type(doc)}")
                return {
                    'answer': "I encountered an error processing your request.",
                    'sources': []
                }
        
            # DEBUG: Print first 500 chars of context
            print(f"Context preview: {context[:500]}...")
        
            # Check if context is empty or too short
            if not context or len(context.strip()) < 10:
                print("Context is empty or too short")
                return {
                    'answer': "I couldn't find any relevant information to answer your question.",
                    'sources': []
                }
        
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
            print("Sending request to OpenAI API")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that answers questions based ONLY on the provided context. Your job is to extract and present information from the context, not to use your general knowledge."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2  # Lower temperature for more focused answers
            )
            print("Received response from OpenAI API")

            # Process sources
            sources = []
            if 'metadatas' in results and results['metadatas'] and results['metadatas'][0]:
                print(f"Processing {len(results['metadatas'][0])} metadata items")
                for i, metadata in enumerate(results['metadatas'][0]):
                    print(f"Metadata {i}: {metadata}")
                    if metadata and 'url' in metadata and metadata['url'] is not None:
                        sources.append(metadata['url'])
        
            print(f"Final sources count: {len(sources)}")
            print(f"Answer: {response.choices[0].message.content[:100]}...")

            return {
                'answer': response.choices[0].message.content,
                'sources': sources
            }
        except Exception as e:
            print(f"Error in get_answer: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                'answer': "I encountered an error processing your request.",
                'sources': []
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