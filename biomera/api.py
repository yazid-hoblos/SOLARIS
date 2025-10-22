from flask import Flask, request, jsonify, send_from_directory
from main import Main
import subprocess
import shlex
import sys

app = Flask(__name__, static_folder="public", static_url_path="/")

# Add CORS headers to all responses
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

@app.route('/')
def index():
    return send_from_directory("public", "chat.html")

@app.route('/health')
def health():
    return jsonify({"status": "ok", "message": "SOLARIS Chatbot API is running"}), 200

# Handle OPTIONS requests for CORS preflight
@app.route('/ask', methods=['OPTIONS'])
@app.route('/chat_solaris', methods=['OPTIONS'])
@app.route('/reset', methods=['OPTIONS'])
@app.route('/files', methods=['OPTIONS'])
def options():
    return '', 204

@app.route('/<path:path>')
def static_file(path):
    return send_from_directory("public", path)

# Initialize biomera instance
biomera = None

def get_biomera():
    global biomera
    if biomera is None:
        biomera = Main()
    return biomera

@app.route('/ask', methods=['POST'])
def message():
    try:
        print(f"[/ask] Received request")
        content = request.get_json()
        print(f"[/ask] Content: {content}")
        
        if not content or 'message' not in content:
            return jsonify({'error': 'No JSON entry'}), 400
        
        if len(content["message"]) < 2:
            return jsonify({'error': 'Message too short'}), 400
        
        if len(content["message"]) > 1000:
            return jsonify({'error': 'Message too long'}), 400

        msg = content["message"].strip()
        print(f"[/ask] Processing message: {msg}")

        # If message is intended for solaris, forward to the chat_solaris handler
        if msg.lower().startswith("solaris:"):
            print(f"[/ask] Forwarding to solaris handler")
            # strip the prefix and forward
            solaris_cmd = msg.split(":", 1)[1].strip()
            # construct a fake request body like /chat_solaris expects
            return chat_solaris_internal(solaris_cmd)

        print(f"[/ask] Getting biomera instance...")
        biomera_instance = get_biomera()
        print(f"[/ask] Querying biomera...")
        response = biomera_instance.query("user", content["message"])
        print(f"[/ask] Got response: {response}")

        return jsonify({
            "input": content["message"],
            "response": response,
        }), 200
    
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"[/ask] ERROR: {error_details}")
        return jsonify({
            "error": str(e),
            "details": error_details
        }), 500

@app.route('/files', methods=["GET"])
def files():
    try:
        files = get_biomera().executor.list_files()
        return jsonify(files), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def chat_solaris_internal(command_text: str):
    """Internal helper to execute a solaris command and return Flask response tuple."""
    # Parse command into args safely (no shell)
    if not command_text:
        return jsonify({"error": "No solaris command provided."}), 400

    # Assume the user provides arguments as they would on the CLI, e.g. "pathway_profiler --input x"
    try:
        args = shlex.split(command_text)
    except ValueError as e:
        return jsonify({"error": f"Failed to parse command: {str(e)}"}), 400

    # Build the invocation: use the current Python executable to run solaris as a module
    cmd = [sys.executable, "-m", "solaris"] + args

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    except subprocess.TimeoutExpired:
        return jsonify({"error": "Solaris command timed out."}), 504
    except Exception as e:
        return jsonify({"error": f"Failed to run Solaris: {str(e)}"}), 500

    result = {
        "command": " ".join(shlex.quote(p) for p in cmd),
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
    }

    status = 200 if proc.returncode == 0 else 400
    return jsonify(result), status


@app.route('/chat_solaris', methods=['POST'])
def chat_solaris():
    """Public endpoint to run a Solaris subcommand.

    Expected JSON: { "message": "pathway_profiler --input file.fasta ..." }
    """
    content = request.get_json()
    if not content or 'message' not in content:
        return jsonify({'error': 'No JSON entry'}), 400

    return chat_solaris_internal(content['message'].strip())

@app.route('/reset', methods=["POST"])
def reset():
    global biomera
    try:
        biomera = Main()
        return jsonify({
            "message": "BIOMERA has been reset.",
        }), 200
    except Exception as e:
        return jsonify({
            "error": str(e),
        }), 500

if __name__ == '__main__':
    print("Starting SOLARIS Chatbot API...")
    print("Initializing BIOMERA (this may take a moment)...")
    try:
        get_biomera()  # Pre-initialize to avoid timeout on first request
        print("✅ BIOMERA initialized successfully!")
    except Exception as e:
        print(f"⚠️ Warning: Failed to pre-initialize BIOMERA: {e}")
        print("Will initialize on first request instead.")
    
    print("Open http://localhost:5000 in your browser")
    app.run(debug=True, host='0.0.0.0', port=5000)