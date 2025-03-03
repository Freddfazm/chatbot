import os
import openai
from chromadb.utils import embedding_functions
import chromadb
class QASystem:
    def __init__(self):
        self.chroma_client = chromadb.Client()
        self.openai_ef = embedding_functions.OpenAIEmbeddingFunction(
            api_key=os.getenv('OPENAI_API_KEY'),
            model_name="text-embedding-ada-002"
        )
        self.collection = self.chroma_client.get_or_create_collection(
            name="confluence_kb",
            embedding_function=self.openai_ef
        )
    def get_answer(self, question, n_results=3):
        # Query the vector database
        results = self.collection.query(
            query_texts=[question],
            n_results=n_results
        )

        # Prepare context from relevant chunks
        context = "\n".join(results['documents'][0])
        
        # Create prompt for GPT
        prompt = f"""Based on the following context, answer the question. 
        If the answer cannot be found in the context, say "I don't have enough information to answer that."
        
        Context:
        {context}
        
        Question: {question}"""

        # Get response from GPT
        response = openai.ChatCompletion.create(
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
