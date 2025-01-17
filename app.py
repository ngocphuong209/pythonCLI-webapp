from flask import Flask, render_template, request, jsonify, flash, redirect, send_file
import subprocess
import sys
import os
import uuid

app = Flask(__name__)
app.secret_key = '2Mr4wbDS37QDLvDUQEsWbUTx'

@app.route('/')
def homepage():
    return send_file('index.html')

@app.route("/clipython")
def clipython():
    return render_template("clipython.html")

# Error handler for file size limit
@app.errorhandler(413)
def request_entity_too_large(error):
    flash("File is too large! The limit is 100MB.")
    return redirect(request.url), 413

@app.route("/run-python", methods=["POST"])
def run_python_code():
    data = request.json
    code = data.get("code", "")
    input_values = data.get("input_values", [])

    # Create a temporary file to store the Python code
    temp_file = f"/tmp/temp_{uuid.uuid4().hex}.py"
    with open(temp_file, "w") as f:
        f.write(code)

    try:
        # Run the Python code with the provided input
        process = subprocess.Popen(
            [sys.executable, temp_file],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        stdout, stderr = process.communicate(input="\n".join(input_values))

        if stderr:
            return jsonify({"output": stderr, "error": True})
        else:
            return jsonify({"output": stdout, "error": False})
    except Exception as e:
        return jsonify({"output": str(e), "error": True})
    finally:
        # Remove the temporary file
        if os.path.exists(temp_file):
            os.remove(temp_file)

@app.route("/share-code", methods=["POST"])
def share_code():
    data = request.json
    code = data.get("code", "")

    # Create a unique ID for the shared code
    share_id = uuid.uuid4().hex

    # Save the code to a file (in a real application, you'd use a database)
    with open(f"/tmp/shared_code_{share_id}.py", "w") as f:
        f.write(code)

    # Create the share URL
    share_url = f"/view/{share_id}"

    return jsonify({"share_url": share_url})

@app.route("/view/<share_id>")
def view_shared_code(share_id):
    # Read the code from the file (in a real application, you'd use a database)
    try:
        with open(f"/tmp/shared_code_{share_id}.py", "r") as f:
            code = f.read()
        return render_template("view_shared_code.html", code=code)
    except FileNotFoundError:
        return "Code does not exist or has expired", 404

@app.route("/install-library", methods=["POST"])
def install_library():
    # Note: Installing libraries on-the-fly is not recommended in a production environment
    # This is just for demonstration purposes
    data = request.json
    library = data.get("library", "")

    if not library:
        return jsonify({"success": False, "error": "Library name cannot be empty"})

    try:
        # Install the library using pip
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", library],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            return jsonify({"success": True})
        else:
            return jsonify({"success": False, "error": result.stderr})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

if __name__ == '__main__':
    app.run(debug=True)