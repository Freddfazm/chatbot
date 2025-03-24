from confluence_fetcher import ConfluenceFetcher
import json
import os
from flask import Flask, jsonify, render_template, send_from_directory

app = Flask(__name__)

# Get content from Confluence and store it
def fetch_confluence_content():
    fetcher = ConfluenceFetcher()
    
    # Get all pages
    pages = fetcher.get_all_pages()
    
    # Extract content
    content = fetcher.extract_content(pages)
    
    # Save to JSON file
    with open('confluence_content.json', 'w', encoding='utf-8') as f:
        json.dump(content, f, ensure_ascii=False, indent=4)
    
    return content

# Route for home page
@app.route('/')
def home():
    return jsonify({
        "status": "online",
        "message": "Confluence chatbot is running"
    })

# Route for widget
@app.route('/widget')
def widget():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Chatbot Widget</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 20px;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                background-color: #f5f5f5;
            }
            .chat-container {
                width: 400px;
                height: 600px;
                border: 1px solid #ddd;
                border-radius: 10px;
                overflow: hidden;
                display: flex;
                flex-direction: column;
                background-color: white;
                box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            }
            .chat-header {
                background-color: #075e54;
                color: white;
                padding: 15px;
                text-align: center;
                font-weight: bold;
            }
            .chat-messages {
                flex: 1;
                padding: 15px;
                overflow-y: auto;
            }
            .message {
                margin-bottom: 10px;
                padding: 10px;
                border-radius: 5px;
                max-width: 70%;
                word-wrap: break-word;
            }
            .user-message {
                background-color: #dcf8c6;
                margin-left: auto;
            }
            .bot-message {
                background-color: #f0f0f0;
            }
            .chat-input {
                display: flex;
                padding: 10px;
                border-top: 1px solid #ddd;
            }
            .chat-input input {
                flex: 1;
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 20px;
                margin-right: 10px;
            }
            .chat-input button {
                padding: 10px 20px;
                background-color: #075e54;
                color: white;
                border: none;
                border-radius: 20px;
                cursor: pointer;
            }
            .chat-input button:hover {
                background-color: #054c44;
            }
        </style>
    </head>
    <body>
        <div class="chat-container">
            <div class="chat-header">Confluence Chatbot</div>
            <div class="chat-messages" id="chat-messages">
                <div class="message bot-message">Hello! I'm your Confluence assistant. How can I help you today?</div>
            </div>
            <div class="chat-input">
                <input type="text" id="user-input" placeholder="Type your question..." />
                <button onclick="sendMessage()">Send</button>
            </div>
        </div>

        <script>
            function sendMessage() {
                const userInput = document.getElementById('user-input');
                const messagesContainer = document.getElementById('chat-messages');
                
                if (userInput.value.trim() === '') return;
                
                // Add user message
                const userMessage = document.createElement('div');
                userMessage.className = 'message user-message';
                userMessage.textContent = userInput.value;
                messagesContainer.appendChild(userMessage);
                
                // Clear input
                const userQuestion = userInput.value;
                userInput.value = '';
                
                // Scroll to bottom
                messagesContainer.scrollTop = messagesContainer.scrollHeight;
                
                // Simulate bot response (replace with actual API call)
                setTimeout(() => {
                    const botMessage = document.createElement('div');
                    botMessage.className = 'message bot-message';
                    botMessage.textContent = "I'm processing your question about: " + userQuestion;
                    messagesContainer.appendChild(botMessage);
                    
                    // Scroll to bottom again
                    messagesContainer.scrollTop = messagesContainer.scrollHeight;
                }, 1000);
            }
            
            // Allow sending message with Enter key
            document.getElementById('user-input').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    sendMessage();
                }
            });
        </script>
    </body>
    </html>
    """

# Route to fetch content
@app.route('/fetch-content')
def get_content():
    try:
        content = fetch_confluence_content()
        return jsonify({
            "status": "success",
            "message": "Content fetched successfully",
            "count": len(content)
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

if __name__ == "__main__":
    # Get port from environment variable (Heroku sets this)
    port = int(os.environ.get("PORT", 5000))
    # Run the app
    app.run(host='0.0.0.0', port=port)