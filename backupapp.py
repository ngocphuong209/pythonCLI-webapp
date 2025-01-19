from flask import Flask, request, jsonify, send_file, render_template
import subprocess
import sys
import os
import uuid
import tempfile
import unicodedata
import re
import io 

app = Flask(__name__)
app.secret_key = "2Mr4wbDS37QDLvDUQEsWbUTx"

def remove_accents(input_str):
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    only_ascii = nfkd_form.encode('ASCII', 'ignore')
    return only_ascii.decode('ASCII')

@app.route("/")
def homepage():
    return send_file("index.html")

@app.route("/clipython")
def clipython():
    return render_template("clipython.html")

@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({"error": "File is too large! The limit is 100MB."}), 413

@app.route("/run-python", methods=["POST"])
def run_python_code():
    data = request.json
    code = data.get("code", "")
    input_values = data.get("input_values", [])

    # Remove accents from code and input values
    code = remove_accents(code)
    input_values = [remove_accents(value) for value in input_values]

    with tempfile.NamedTemporaryFile(mode="w+", suffix=".py", delete=False, encoding="utf-8") as temp_file:
        temp_file.write(code)
        temp_file_path = temp_file.name

    try:
        # Create a custom input function to capture prompts
        input_iterator = iter(input_values)
        def custom_input(prompt=''):
            print(prompt, end='')  # Print the prompt
            try:
                value = next(input_iterator)
                print(value)  # Print the input value
                return value
            except StopIteration:
                raise EOFError("No more input available")

        # Redirect stdout to capture all output
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()

        # Execute the code with the custom input function
        exec(code, {'input': custom_input})

        # Get the captured output
        output = sys.stdout.getvalue()

        # Restore the original stdout
        sys.stdout = old_stdout

        return jsonify({"output": output, "error": False})
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

    shared_code_dir = os.path.join(tempfile.gettempdir(), "shared_code")
    os.makedirs(shared_code_dir, exist_ok=True)

    with open(os.path.join(shared_code_dir, f"{share_id}.py"), "w", encoding="utf-8") as f:
        f.write(code)

    share_url = f"/view/{share_id}"
    return jsonify({"share_url": share_url})

@app.route("/view/<share_id>")
def view_shared_code(share_id):
    shared_code_path = os.path.join(tempfile.gettempdir(), "shared_code", f"{share_id}.py")
    try:
        with open(shared_code_path, "r", encoding="utf-8") as f:
            code = f.read()
        return render_template("view_shared_code.html", code=code)
    except FileNotFoundError:
        return "Code does not exist or has expired", 404

@app.route("/install-library", methods=["POST"])
def install_library():
    return jsonify(
        {
            "success": False,
            "error": "Installing libraries dynamically is not supported for security reasons.",
        }
    )

if __name__ == "__main__":
    app.run(debug=True)21