from flask import Flask, render_template, request, jsonify, flash, redirect, send_file
import subprocess
import sys
import os
import uuid
import tempfile

app = Flask(__name__)
app.secret_key = '2Mr4wbDS37QDLvDUQEsWbUTx'

@app.route('/')
def homepage():
    return send_file('index.html')

@app.route("/clipython")
def clipython():
    return render_template("clipython.html")

@app.errorhandler(413)
def request_entity_too_large(error):
    flash("File is too large! The limit is 100MB.")
    return redirect(request.url), 413

@app.route("/run-python", methods=["POST"])
def run_python_code():
    data = request.json
    code = data.get("code", "")
    input_values = data.get("input_values", [])

    with tempfile.NamedTemporaryFile(mode='w+', suffix='.py', delete=False, encoding='utf-8') as temp_file:
        temp_file.write(code)
        temp_file_path = temp_file.name

    try:
        process = subprocess.Popen(
            [sys.executable, temp_file_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8'
        )
        stdout, stderr = process.communicate(input="\n".join(input_values))

        if stderr:
            return jsonify({"output": stderr, "error": True})
        else:
            return jsonify({"output": stdout, "error": False})
    except Exception as e:
        return jsonify({"output": str(e), "error": True})
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

@app.route("/share-code", methods=["POST"])
def share_code():
    data = request.json
    code = data.get("code", "")
    share_id = uuid.uuid4().hex

    shared_code_dir = os.path.join(tempfile.gettempdir(), 'shared_code')
    os.makedirs(shared_code_dir, exist_ok=True)
    
    with open(os.path.join(shared_code_dir, f"{share_id}.py"), "w", encoding='utf-8') as f:
        f.write(code)

    share_url = f"/view/{share_id}"
    return jsonify({"share_url": share_url})

@app.route("/view/<share_id>")
def view_shared_code(share_id):
    shared_code_path = os.path.join(tempfile.gettempdir(), 'shared_code', f"{share_id}.py")
    try:
        with open(shared_code_path, "r", encoding='utf-8') as f:
            code = f.read()
        return render_template("view_shared_code.html", code=code)
    except FileNotFoundError:
        return "Code does not exist or has expired", 404

@app.route("/install-library", methods=["POST"])
def install_library():
    return jsonify({"success": False, "error": "Installing libraries dynamically is not supported for security reasons."})

if __name__ == '__main__':
    app.run(debug=True)