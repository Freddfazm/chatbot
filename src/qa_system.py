import os
import openai
from chromadb.utils import embedding_functions
import chromadb

class QASystem:
    def __init__(self, excluded_labels=None, auto_rebuild=False):
        # Set default excluded labels if none provided
        self.excluded_labels = excluded_labels or ['internal', 'mls-team']
        print(f"Excluding content with labels: {self.excluded_labels}")
        
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
        
        # Get or create the collection with better error handling
        self.collection = self._get_or_create_collection()
        
        # Auto-rebuild knowledge base if requested
        if auto_rebuild:
            self.rebuild_knowledge_base_with_filter()

    def filter_content_by_labels(self, content_items):
        """
        Filter out content items that have any of the excluded labels
        
        Args:
            content_items (list): List of content items from Confluence
            
        Returns:
            list: Filtered list of content items
        """
        filtered_items = []
        excluded_count = 0
        
        for item in content_items:
            # Skip items with excluded labels
            if 'labels' in item:
                # Check if any excluded label is in the item's labels
                has_excluded_label = any(
                    excluded_label.lower() in [label.lower() for label in item['labels']] 
                    for excluded_label in self.excluded_labels
                )
                
                if has_excluded_label:
                    excluded_count += 1
                    print(f"Excluding item with title: {item.get('title', 'Unknown')} due to labels: {item.get('labels', [])}")
                    continue
            
            # If we get here, the item doesn't have excluded labels
            filtered_items.append(item)
        
        print(f"Filtered out {excluded_count} items with excluded labels")
        print(f"Kept {len(filtered_items)} items")
        
        return filtered_items
    
    def rebuild_knowledge_base_with_filter(self):
        """
        Rebuild the knowledge base by fetching content from Confluence,
        filtering out items with excluded labels, and adding the filtered content
        """
        try:
            print("Starting knowledge base rebuild with label filtering...")
            
            # Step 1: Delete the existing collection
            try:
                self.chroma_client.delete_collection(name="confluence_kb")
                print("Deleted existing collection")
            except Exception as e:
                print(f"Error deleting collection: {str(e)}")
            
            # Step 2: Create a new collection
            self.collection = self.chroma_client.create_collection(
                name="confluence_kb",
                embedding_function=self.openai_ef
            )
            print("Created new collection")
            
            # Step 3: Fetch content from Confluence
            from confluence_fetcher import ConfluenceFetcher
            fetcher = ConfluenceFetcher()
            pages = fetcher.get_all_pages()
            content = fetcher.extract_content(pages)
            print(f"Fetched {len(content)} items from Confluence")
            
            # Step 4: Filter content by labels
            filtered_content = self.filter_content_by_labels(content)
            
            # Step 5: Save to JSON file
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            json_path = os.path.join(base_dir, 'confluence_content.json')
            with open(json_path, 'w', encoding='utf-8') as f:
                import json
                json.dump(filtered_content, f, ensure_ascii=False, indent=4)
            
            # Step 6: Add filtered content to the vector database
            added_count = self.add_content_to_knowledge_base(filtered_content)
            
            print(f"Knowledge base rebuilt successfully. Added {added_count} documents.")
            return {
                "success": True,
                "message": f"Knowledge base rebuilt successfully. Added {added_count} documents."
            }
        except Exception as e:
            print(f"Error rebuilding knowledge base: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "message": f"Error rebuilding knowledge base: {str(e)}"
            }
    
    def add_content_to_knowledge_base(self, content_items):
        """
        Add content to the knowledge base
        
        Args:
            content_items (list): List of content items from Confluence
            
        Returns:
            int: Number of documents added
        """
        # Prepare documents for batch insertion
        documents = []
        metadatas = []
        ids = []
        
        # Process each content item
        count = 0
        for item in content_items:
            if 'title' in item and 'content' in item and 'url' in item:
                # Validate content is not None or empty
                if item['content'] is None or item['content'].strip() == '':
                    print(f"Skipping item with empty content: {item['title']}")
                    continue
                    
                # Create a document with title and content
                doc = f"Title: {item['title']}\n\n{item['content']}"
                
                # Validate document
                if doc and len(doc.strip()) > 10:  # Ensure document has meaningful content
                    # Add to batches
                    documents.append(doc)
                    metadata = {"url": item['url'], "title": item['title']}
                    
                    # Add labels to metadata if available
                    if 'labels' in item:
                        metadata['labels'] = ','.join(item['labels'])
                        
                    metadatas.append(metadata)
                    ids.append(f"doc_{count}")
                    
                    count += 1
                    print(f"Added document {count}: {item['title'][:50]}...")
                else:
                    print(f"Skipping document with insufficient content: {item['title']}")
        
        # Add documents to collection in batches
        if documents:
            try:
                print(f"Adding {len(documents)} documents to collection")
                self.collection.add(
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids
                )
                print("Documents added successfully")
            except Exception as e:
                print(f"Error adding documents to collection: {str(e)}")
                import traceback
                traceback.print_exc()
        else:
            print("No valid documents to add")
            
        return count

    def _get_or_create_collection(self):
        """Get or create the collection with better error handling"""
        try:
            # Try to get the collection
            collection = self.chroma_client.get_collection(
                name="confluence_kb",
                embedding_function=self.openai_ef
            )
            doc_count = collection.count()
            print(f"Found collection with {doc_count} documents")
            return collection
        except Exception as e:
            print(f"Error getting collection: {str(e)}")
            try:
                # Try to create the collection
                collection = self.chroma_client.create_collection(
                    name="confluence_kb",
                    embedding_function=self.openai_ef
                )
                print("Created new collection")
                return collection
            except Exception as create_error:
                print(f"Error creating collection: {str(create_error)}")
                # As a last resort, try to delete and recreate
                try:
                    print("Attempting to delete and recreate collection")
                    try:
                        self.chroma_client.delete_collection(name="confluence_kb")
                    except:
                        pass  # Ignore if it doesn't exist
                    
                    collection = self.chroma_client.create_collection(
                        name="confluence_kb",
                        embedding_function=self.openai_ef
                    )
                    print("Successfully recreated collection")
                    return collection
                except Exception as final_error:
                    print(f"Fatal error creating collection: {str(final_error)}")
                    raise
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
            
            # Print metadata for debugging
            if 'metadatas' in results and results['metadatas'] and results['metadatas'][0]:
                print(f"Metadata found: {len(results['metadatas'][0])}")
                for i, metadata in enumerate(results['metadatas'][0]):
                    print(f"Metadata {i}: {metadata}")
            else:
                print("No metadata found")
                
            # Print IDs for debugging
            if 'ids' in results and results['ids'] and results['ids'][0]:
                print(f"IDs found: {len(results['ids'][0])}")
                for i, id in enumerate(results['ids'][0]):
                    print(f"ID {i}: {id}")
            else:
                print("No IDs found")
        
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