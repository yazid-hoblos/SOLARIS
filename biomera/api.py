from flask import Flask, request, jsonify, send_from_directory
from main import Main
import subprocess
import shlex
import sys

app = Flask(__name__, static_folder="public", static_url_path="/")

@app.route('/')
def index():
    return send_from_directory("public", "index.html")

@app.route('/<path:path>')
def static_file(path):
    return send_from_directory("public", path)

biomera = Main()

@app.route('/ask', methods=['POST'])
def message():
    content = request.get_json()
    if not content or 'message' not in content:
        return jsonify({'error': 'No JSON entry'}), 400
    
    if len(content["message"]) < 2:
        return jsonify({'error': 'Message too short'}), 400
    
    if len(content["message"]) > 1000:
        return jsonify({'error': 'Message too long'}), 400

    msg = content["message"].strip()

    # If message is intended for solaris, forward to the chat_solaris handler
    if msg.lower().startswith("solaris:"):
        # strip the prefix and forward
        solaris_cmd = msg.split(":", 1)[1].strip()
        # construct a fake request body like /chat_solaris expects
        return chat_solaris_internal(solaris_cmd)

    response = biomera.query("user", content["message"])

    return jsonify({
        "input": content["message"],
        "response": response,
    }), 201

@app.route('/files', methods=["GET"])
def files():
    files = biomera.executor.list_files()
    return jsonify(files), 200


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
    app.run(debug=True)