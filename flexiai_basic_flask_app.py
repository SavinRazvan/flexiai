# flexiai_basic_flask_app.py
import os

def create_logs_folder(project_root):
    log_folder = os.path.join(project_root, 'logs')
    if not os.path.exists(log_folder):
        os.makedirs(log_folder)
        print(f"Created directory: {log_folder}")

def create_routes_folder(project_root):
    routes_folder = os.path.join(project_root, 'routes')
    if not os.path.exists(routes_folder):
        os.makedirs(routes_folder)
        print(f"Created directory: {routes_folder}")
    
    files_content = {
        'api.py': (
            "# routes/api.py\n"
            "from flask import Blueprint, request, jsonify, session as flask_session\n"
            "from flexiai import FlexiAI\n"
            "from flexiai.config.logging_config import setup_logging\n"
            "import uuid\n\n"
            "api_bp = Blueprint('api', __name__)\n"
            "flexiai = FlexiAI()\n\n"
            "# setup_logging() # Check logs -> app.log file after you activate this\n\n"
            "def message_to_dict(message):\n"
            "    \"\"\"\n"
            "    Convert a message object to a dictionary, including nested TextContentBlock objects.\n"
            "    \"\"\"\n"
            "    message_dict = {\n"
            "        'id': message.id,\n"
            "        'role': message.role,\n"
            "        'content': [block.text.value for block in message.content if hasattr(block, 'text') and hasattr(block.text, 'value')]\n"
            "    }\n"
            "    return message_dict\n\n"
            "@api_bp.route('/run', methods=['POST'])\n"
            "def run():\n"
            "    data = request.json\n"
            "    user_message = data['message']\n"
            "    assistant_id = 'asst_bxt62YG46C5wn4t5U1ESqJZf'  # Updated assistant ID\n"
            "    thread_id = data.get('thread_id')\n\n"
            "    session_id = flask_session.get('session_id')\n"
            "    if not session_id:\n"
            "        session_id = str(uuid.uuid4())  # Generate a new session ID\n"
            "        flask_session['session_id'] = session_id\n"
            "        flexiai.session_manager.create_session(session_id, {\"thread_id\": thread_id, \"seen_message_ids\": []})\n"
            "    else:\n"
            "        session_data = flexiai.session_manager.get_session(session_id)\n"
            "        thread_id = session_data.get(\"thread_id\", thread_id)\n\n"
            "    if not thread_id:\n"
            "        thread = flexiai.create_thread()\n"
            "        thread_id = thread.id\n"
            "        flexiai.session_manager.create_session(session_id, {\"thread_id\": thread_id, \"seen_message_ids\": []})\n\n"
            "    last_retrieved_id = None\n"
            "    flexiai.create_advanced_run(assistant_id, thread_id, user_message)\n"
            "    messages = flexiai.retrieve_messages_dynamically(thread_id, limit=20, retrieve_all=False, last_retrieved_id=last_retrieved_id)\n\n"
            "    session_data = flexiai.session_manager.get_session(session_id)\n"
            "    seen_message_ids = set(session_data.get(\"seen_message_ids\", []))\n\n"
            "    filtered_messages = []\n"
            "    new_seen_message_ids = list(seen_message_ids)\n\n"
            "    for msg in messages:\n"
            "        if msg.id not in seen_message_ids:\n"
            "            filtered_messages.append({\n"
            "                \"role\": \"You\" if msg.role == \"user\" else \"Assistant\",\n"
            "                \"message\": \" \".join([block.text.value for block in msg.content if hasattr(block, 'text') and hasattr(block.text, 'value')])\n"
            "            })\n"
            "            new_seen_message_ids.append(msg.id)\n\n"
            "    flexiai.session_manager.create_session(session_id, {\"thread_id\": thread_id, \"seen_message_ids\": new_seen_message_ids})\n\n"
            "    return jsonify(success=True, thread_id=thread_id, messages=filtered_messages)\n\n"
            "@api_bp.route('/thread/<thread_id>/messages', methods=['GET'])\n"
            "def get_thread_messages(thread_id):\n"
            "    session_id = flask_session.get('session_id')\n"
            "    if not session_id:\n"
            "        return jsonify(success=False, message=\"Session not found\"), 404\n\n"
            "    messages = flexiai.retrieve_messages(thread_id, limit=20)\n"
            "    formatted_messages = [\n"
            "        {\n"
            "            \"role\": \"You\" if msg.role == \"user\" else \"Assistant\",\n"
            "            \"message\": \" \".join([block.text.value for block in msg.content if hasattr(block, 'text') and hasattr(block.text, 'value')])\n"
            "        }\n"
            "        for msg in messages\n"
            "    ]\n"
            "    return jsonify(success=True, thread_id=thread_id, messages=formatted_messages)\n\n"
            "@api_bp.route('/session', methods=['POST'])\n"
            "def create_session():\n"
            "    data = request.json\n"
            "    session_id = data['session_id']\n"
            "    session_data = data['data']\n"
            "    session = flexiai.session_manager.create_session(session_id, session_data)\n"
            "    return jsonify(success=True, session=session)\n\n"
            "@api_bp.route('/session/<session_id>', methods=['GET'])\n"
            "def get_session(session_id):\n"
            "    try:\n"
            "        session_data = flexiai.session_manager.get_session(session_id)\n"
            "        return jsonify(success=True, session=session_data)\n"
            "    except KeyError:\n"
            "        return jsonify(success=False, message=\"Session not found\"), 404\n\n"
            "@api_bp.route('/session/<session_id>', methods=['DELETE'])\n"
            "def delete_session(session_id):\n"
            "    success = flexiai.session_manager.delete_session(session_id)\n"
            "    return jsonify(success=success)\n\n"
            "@api_bp.route('/sessions', methods=['GET'])\n"
            "def get_all_sessions():\n"
            "    sessions = flexiai.session_manager.get_all_sessions()\n"
            "    return jsonify(success=True, sessions=sessions)\n\n"
            "@api_bp.route('/sessions', methods=['DELETE'])\n"
            "def clear_all_sessions():\n"
            "    success = flexiai.session_manager.clear_all_sessions()\n"
            "    return jsonify(success=success)\n"
        )
    }
    
    for filename, content in files_content.items():
        file_path = os.path.join(routes_folder, filename)
        if not os.path.exists(file_path):
            with open(file_path, 'w') as f:
                f.write(content)
            print(f"Created file: {file_path}")

def create_static_folder(project_root):
    static_folder = os.path.join(project_root, 'static')
    if not os.path.exists(static_folder):
        os.makedirs(static_folder)
        print(f"Created directory: {static_folder}")
    
    subfolders = ['css', 'images', 'js']
    files_content = {
        'css/styles.css': (
            "/* static/css/styles.css */\n\n"
            "/* Import Open Sans Font */\n"
            "@import url('https://fonts.googleapis.com/css2?family=Open+Sans:wght@400;600&display=swap');\n\n"
            "/* Base Styles */\n"
            "body {\n"
            "    font-family: 'Open Sans', sans-serif;\n"
            "    margin: 0;\n"
            "    padding: 0;\n"
            "    background-color: #535353;\n"
            "    display: flex;\n"
            "    justify-content: center;\n"
            "    align-items: flex-start;\n"
            "    height: 100vh;\n"
            "}\n\n"
            "/* Chat Container */\n"
            "#chat-container {\n"
            "    width: 100%;\n"
            "    max-width: 400px;\n"
            "    height: calc(100vh - 2rem);\n"
            "    display: flex;\n"
            "    flex-direction: column;\n"
            "    background-color: #ffffff;\n"
            "    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);\n"
            "    border-radius: 8px;\n"
            "    margin: 1rem 0;\n"
            "    overflow: hidden;\n"
            "}\n\n"
            "/* Links */\n"
            "a {\n"
            "    color: #89e600;\n"
            "}\n\n"
            "/* Messages List */\n"
            "#messages {\n"
            "    list-style-type: none;\n"
            "    padding: 1rem;\n"
            "    flex: 1;\n"
            "    overflow-y: auto;\n"
            "    margin: 0;\n"
            "    color: #e1e1e6;\n"
            "}\n\n"
            "/* Message Item */\n"
            "#messages li {\n"
            "    padding: 0.5rem 0;\n"
            "    margin: 0.5rem 0;\n"
            "    border-radius: 4px;\n"
            "    word-wrap: break-word;\n"
            "    display: flex;\n"
            "    align-items: flex-start;\n"
            "    animation: fadeIn 0.5s ease-in-out;\n"
            "}\n\n"
            "/* Animation for messages */\n"
            "@keyframes fadeIn {\n"
            "    from { opacity: 0; transform: translateY(10px); }\n"
            "    to { opacity: 1; transform: translateY(0); }\n"
            "}\n\n"
            "/* Message Container */\n"
            ".message-container {\n"
            "    display: flex;\n"
            "    align-items: flex-start;\n"
            "    width: 100%;\n"
            "}\n\n"
            "/* Avatar */\n"
            ".avatar {\n"
            "    width: 45px;\n"
            "    height: 45px;\n"
            "    border-radius: 50%;\n"
            "    background-color: #25272a;\n"
            "    display: flex;\n"
            "    justify-content: center;\n"
            "    align-items: center;\n"
            "    margin-right: 10px;\n"
            "    font-size: 1.2em;\n"
            "    color: #ffffff;\n"
            "    border: 1px solid #c6c6c6;\n"
            "    overflow: hidden;\n"
            "}\n\n"
            "/* Avatar Images */\n"
            ".avatar img {\n"
            "    width: 100%;\n"
            "    height: 100%;\n"
            "    border-radius: 50%;\n"
            "}\n\n"
            "/* Message Content */\n"
            ".message-content {\n"
            "    flex: 1;\n"
            "    padding: 0.75rem 1rem;\n"
            "    border-radius: 4px;\n"
            "    font-size: 0.9em;\n"
            "    background-color: #3a3f4b;\n"
            "    color: #e1e1e6;\n"
            "    position: relative;\n"
            "}\n\n"
            "/* User Message */\n"
            ".user .message-content {\n"
            "    background-color: #3a3a3a;\n"
            "    text-align: left;\n"
            "    color: #e1e1e6;\n"
            "}\n\n"
            "/* Assistant Message */\n"
            ".assistant .message-content {\n"
            "    background-color: #404a63;\n"
            "    text-align: left;\n"
            "}\n\n"
            "/* Error Message */\n"
            "#error {\n"
            "    background-color: #ff4c4c;\n"
            "    text-align: center;\n"
            "    color: #fff;\n"
            "}\n"
            "#error-message {\n"
            "    color: #fff;\n"
            "}\n\n"
            "/* Input Container */\n"
            "#input-container {\n"
            "    display: flex;\n"
            "    align-items: center;\n"
            "    padding: 0.75rem 1rem;\n"
            "    border-top: 1px solid #353940;\n"
            "    background-color: #ffffff;\n"
            "}\n\n"
            "/* Message Input */\n"
            "#message-input {\n"
            "    flex: 1;\n"
            "    padding: 0.75rem;\n"
            "    border: 1px solid #484e5c;\n"
            "    border-radius: 20px;\n"
            "    margin-right: 0.5rem;\n"
            "    box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.2);\n"
            "    transition: border-color 0.3s;\n"
            "    background-color: #3a3a3a;\n"
            "    color: #e1e1e6;\n"
            "    width: 100%;\n"
            "    box-sizing: border-box;\n"
            "}\n"
            "#message-input:focus {\n"
            "    border-color: #5a5a5a;\n"
            "    outline: none;\n"
            "}\n\n"
            "/* Send Button */\n"
            "#send-button {\n"
            "    padding: 0.75rem 1rem;\n"
            "    border: none;\n"
            "    border-radius: 20px;\n"
            "    background-color: #404a63;\n"
            "    color: white;\n"
            "    cursor: pointer;\n"
            "    transition: background-color 0.3s, transform 0.1s;\n"
            "    flex-shrink: 0;\n"
            "}\n"
            "#send-button:hover {\n"
            "    background-color: #2a3552;\n"
            "}\n"
            "#send-button:active {\n"
            "    transform: scale(0.95);\n"
            "}\n\n"
            "/* Markdown Content */\n"
            ".markdown-content {\n"
            "    font-size: 0.9em;\n"
            "    line-height: 1.4em;\n"
            "    margin: 0;\n"
            "}\n\n"
            ".markdown-content h1, .markdown-content h2, .markdown-content h3 {\n"
            "    border-bottom: 1px solid #444;\n"
            "    padding-bottom: 0.3em;\n"
            "    margin-top: 0.5em;\n"
            "    font-size: 1.1em;\n"
            "}\n\n"
            ".markdown-content p {\n"
            "    margin: 0.5em 0;\n"
            "}\n\n"
            ".markdown-content code {\n"
            "    background-color: #2e2e2e;\n"
            "    border-radius: 3px;\n"
            "    padding: 0.2em 0.4em;\n"
            "    color: #e1e1e6;\n"
            "}\n\n"
            ".markdown-content pre {\n"
            "    background-color: #2e2e2e;\n"
            "    padding: 1em;\n"
            "    border-radius: 3px;\n"
            "    overflow-x: auto;\n"
            "    font-size: 0.85em;\n"
            "    color: #e1e1e6;\n"
            "}\n\n"
            ".markdown-content ol, .markdown-content ul {\n"
            "    margin-left: -1em;\n"
            "    padding-left: 1.5em;\n"
            "}\n\n"
            "/* Responsive Design */\n"
            "@media (max-width: 600px) {\n"
            "    #chat-container {\n"
            "        height: calc(100vh - 2rem);\n"
            "    }\n"
            "    #message-input {\n"
            "        padding: 0.75rem;\n"
            "    }\n"
            "    #send-button {\n"
            "        padding: 0.75rem 1rem;\n"
            "    }\n"
            "    .avatar {\n"
            "        width: 30px;\n"
            "        height: 30px;\n"
            "        font-size: 1em;\n"
            "    }\n"
            "    .message-content {\n"
            "        font-size: 0.85em;\n"
            "        padding: 0.75rem 1rem;\n"
            "    }\n"
            "    .markdown-content {\n"
            "        font-size: 0.85em;\n"
            "    }\n"
            "}\n"
        ),
        'js/scripts.js': (
            "// static/js/scripts.js\n\n"
            "let threadId = null;\n\n"
            "document.getElementById('send-button').addEventListener('click', sendMessage);\n"
            "document.getElementById('message-input').addEventListener('keypress', function(event) {\n"
            "    if (event.key === 'Enter') {\n"
            "        sendMessage();\n"
            "    }\n"
            "});\n\n"
            "function sendMessage() {\n"
            "    const messageInput = document.getElementById('message-input');\n"
            "    const message = messageInput.value.trim();\n"
            "    if (message === '') return;\n\n"
            "    console.log('Sending message:', message);\n\n"
            "    // Add user message to chat directly without retrieval\n"
            "    addMessage('You', message, 'user');\n\n"
            "    // Send message to server\n"
            "    fetch('/api/run', {\n"
            "        method: 'POST',\n"
            "        headers: { 'Content-Type': 'application/json' },\n"
            "        body: JSON.stringify({ message: message, thread_id: threadId })\n"
            "    })\n"
            "    .then(response => response.json())\n"
            "    .then(data => {\n"
            "        console.log('Received response:', data); // Log the response to debug\n"
            "        if (data.success) {\n"
            "            threadId = data.thread_id;\n"
            "            updateChat(data.messages);\n"
            "        } else {\n"
            "            addMessage('Error', 'Failed to get response from assistant.', 'error');\n"
            "        }\n"
            "    })\n"
            "    .catch(error => {\n"
            "        console.error('Fetch error:', error);\n"
            "        addMessage('Error', 'An error occurred: ' + error.message, 'error');\n"
            "    });\n\n"
            "    // Clear input\n"
            "    messageInput.value = '';\n"
            "}\n\n"
            "function addMessage(role, text, className) {\n"
            "    console.log('Adding message:', role, text);\n\n"
            "    const messageElement = document.createElement('li');\n"
            "    messageElement.className = className;\n\n"
            "    // Determine avatar based on role\n"
            "    const avatar = role === 'You' ? '/static/images/user.png' : '/static/images/assistant.png';\n\n"
            "    // Convert markdown to HTML\n"
            "    try {\n"
            "        const htmlContent = window.marked.parse(text);\n"
            "        console.log('HTML Content:', htmlContent); // Log the HTML content to debug\n"
            "        messageElement.innerHTML = `\n"
            "            <div class=\"message-container\">\n"
            "                <div class=\"avatar\"><img src=\"${avatar}\" alt=\"${role}\" /></div>\n"
            "                <div class=\"message-content\">\n"
            "                    <div class=\"markdown-content\">${htmlContent}</div>\n"
            "                </div>\n"
            "            </div>`;\n"
            "    } catch (error) {\n"
            "        console.error('Markdown conversion error:', error);\n"
            "        messageElement.innerHTML = `\n"
            "            <div class=\"message-container\">\n"
            "                <div class=\"avatar\"><img src=\"${avatar}\" alt=\"${role}\" /></div>\n"
            "                <div class=\"message-content\">\n"
            "                    <div class=\"markdown-content\">${text}</div>\n"
            "                </div>\n"
            "            </div>`;\n"
            "    }\n\n"
            "    const messagesContainer = document.getElementById('messages');\n"
            "    messagesContainer.appendChild(messageElement);\n"
            "    messagesContainer.scrollTop = messagesContainer.scrollHeight;\n"
            "}\n\n"
            "function updateChat(messages) {\n"
            "    messages.forEach(msg => {\n"
            "        if (msg.role === 'Assistant') {\n"
            "            addMessage('Assistant', msg.message, 'assistant');\n"
            "        }\n"
            "    });\n"
            "}\n\n"
            "// Test if marked is available\n"
            "if (typeof window.marked !== 'undefined') {\n"
            "    console.log('Marked library is loaded');\n"
            "} else {\n"
            "    console.error('Marked library is not loaded');\n"
            "}\n"
        ),
    }
    
    for subfolder in subfolders:
        subfolder_path = os.path.join(static_folder, subfolder)
        if not os.path.exists(subfolder_path):
            os.makedirs(subfolder_path)
            print(f"Created directory: {subfolder_path}")

    for filename, content in files_content.items():
        file_path = os.path.join(static_folder, filename)
        if not os.path.exists(file_path):
            with open(file_path, 'w') as f:
                f.write(content)
            print(f"Created file: {file_path}")

def create_templates_folder(project_root):
    templates_folder = os.path.join(project_root, 'templates')
    if not os.path.exists(templates_folder):
        os.makedirs(templates_folder)
        print(f"Created directory: {templates_folder}")
    
    files_content = {
        'index.html': (
            "<!-- templates/index.html -->\n"
            "<!DOCTYPE html>\n"
            "<html lang=\"en\">\n"
            "<head>\n"
            "    <meta charset=\"UTF-8\">\n"
            "    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n"
            "    <title>FlexiAI Chat Application</title>\n"
            "    <link rel=\"stylesheet\" href=\"{{ url_for('static', filename='css/styles.css') }}\">\n"
            "    <link rel=\"icon\" href=\"{{ url_for('static', filename='favicon.ico') }}\" type=\"image/x-icon\">\n"
            "</head>\n"
            "<body>\n"
            "    <div id=\"chat-container\">\n"
            "        <ul id=\"messages\"></ul>\n"
            "        <div id=\"input-container\">\n"
            "            <input type=\"text\" id=\"message-input\" placeholder=\"Type your message here...\">\n"
            "            <button id=\"send-button\">Send</button>\n"
            "        </div>\n"
            "    </div>\n\n"
            "    <!-- Include the Marked.js library -->\n"
            "    <script src=\"https://cdn.jsdelivr.net/npm/marked/marked.min.js\"></script>\n"
            "    <!-- Custom JavaScript file -->\n"
            "    <script src=\"{{ url_for('static', filename='js/scripts.js') }}\"></script>\n"
            "</body>\n"
            "</html>\n"
        )
    }
    
    for filename, content in files_content.items():
        file_path = os.path.join(templates_folder, filename)
        if not os.path.exists(file_path):
            with open(file_path, 'w') as f:
                f.write(content)
            print(f"Created file: {file_path}")

def create_main_files(project_root):
    main_files_content = {
        'app.py': (
            "# app.py\n"
            "import os\n"
            "from flask import Flask, session, render_template\n"
            "from datetime import timedelta\n"
            "from routes.api import api_bp\n"
            "from flexiai import FlexiAI\n\n"
            "app = Flask(__name__, static_folder='static', template_folder='templates')\n"
            "app.secret_key = os.urandom(24)  # Secure the session with a secret key\n"
            "app.register_blueprint(api_bp, url_prefix='/api')\n\n"
            "flexiai = FlexiAI()\n\n"
            "@app.before_request\n"
            "def before_request():\n"
            "    session.permanent = True\n"
            "    app.permanent_session_lifetime = timedelta(minutes=30)  # Set session lifetime\n\n"
            "@app.route('/')\n"
            "def index():\n"
            "    return render_template('index.html')\n\n"
            "if __name__ == '__main__':\n"
            "    app.run(host='0.0.0.0', port=5000, debug=False)\n"
        ),
        'run.py': (
            "# run.py\n"
            "import os\n"
            "from dotenv import load_dotenv\n"
            "from app import app\n\n"
            "# Load environment variables from .env file\n"
            "load_dotenv()\n\n"
            "# Set Flask-related environment variables programmatically\n"
            "os.environ['FLASK_APP'] = 'run.py'\n"
            "os.environ['FLASK_ENV'] = 'development'\n"
            "os.environ['FLASK_DEBUG'] = '1'\n\n"
            "if __name__ == '__main__':\n"
            "    app.run(host='0.0.0.0', port=5000, debug=False)\n"
        )
    }
    
    for filename, content in main_files_content.items():
        file_path = os.path.join(project_root, filename)
        if not os.path.exists(file_path):
            with open(file_path, 'w') as f:
                f.write(content)
            print(f"Created file: {file_path}")

if __name__ == '__main__':
    project_root = os.getcwd()

    try:
        create_logs_folder(project_root)
        create_routes_folder(project_root)
        create_static_folder(project_root)
        create_templates_folder(project_root)
        create_main_files(project_root)
    except Exception as e:
        print(f"Post-installation step failed: {e}")
