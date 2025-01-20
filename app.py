from flask import Flask, request, jsonify, send_file, render_template
from io import StringIO
from contextlib import redirect_stdout, redirect_stderr
import threading
import ast
import uuid
import tempfile
import os
import builtins
import math  # Thư viện math
import random  # Thư viện random
import datetime  # Thư viện datetime
import json  # Thư viện json
import re  # Thư viện re
import collections  # Thư viện collections
import itertools  # Thư viện itertools
import functools  # Thư viện functools
import heapq  # Thư viện heapq
import bisect  # Thư viện bisect
import statistics  # Thư viện statistics
import array  # Thư viện array
import decimal  # Thư viện decimal
import fractions  # Thư viện fractions
import operator  # Thư viện operator

app = Flask(__name__)
app.secret_key = "2Mr4wbDS37QDLvDUQEsWbUTx"

# Giới hạn thời gian thực thi code (giây)
EXECUTION_TIMEOUT = 5

# Danh sách các thư viện tích hợp sẵn được phép import
ALLOWED_MODULES = {
    "math": math,  # Thư viện math
    "random": random,  # Thư viện random
    "datetime": datetime,  # Thư viện datetime
    "json": json,  # Thư viện json
    "re": re,  # Thư viện re
    "collections": collections,  # Thư viện collections
    "itertools": itertools,  # Thư viện itertools
    "functools": functools,  # Thư viện functools
    "heapq": heapq,  # Thư viện heapq
    "bisect": bisect,  # Thư viện bisect
    "statistics": statistics,  # Thư viện statistics
    "array": array,  # Thư viện array
    "decimal": decimal,  # Thư viện decimal
    "fractions": fractions,  
    "operator": operator,  
}


def is_safe_code(code):
    try:
        tree = ast.parse(code)
        for node in ast.walk(tree):
            # Cho phép import các thư viện trong ALLOWED_MODULES
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name not in ALLOWED_MODULES:
                        return False, f"Importing module '{alias.name}' is not allowed."
            # Cho phép import từ các thư viện trong ALLOWED_MODULES
            elif isinstance(node, ast.ImportFrom):
                if node.module not in ALLOWED_MODULES:
                    return (
                        False,
                        f"Importing from module '{node.module}' is not allowed.",
                    )
        return True, "Code is safe."
    except SyntaxError as e:
        return False, f"Syntax error: {str(e)}"


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

    # Kiểm tra code có an toàn không
    is_safe, message = is_safe_code(code)
    if not is_safe:
        return jsonify({"output": f"Error: {message}", "error": True})

    input_iterator = iter(input_values)

    def custom_input(prompt=""):
        print(prompt, end="", flush=True)
        try:
            value = next(input_iterator)
            print(value)
            return value
        except StopIteration:
            raise EOFError("No more input available")

    output_buffer = StringIO()
    error_buffer = StringIO()

    def execute_code():
        with redirect_stdout(output_buffer), redirect_stderr(error_buffer):
            try:

                def custom_print(*args, sep=" ", end=" ", **kwargs):
                    print(*args, sep=sep, end=end, file=output_buffer)

                # tạo môi trường thực thi với các thư viện được phép
                exec_globals = {
                    "__builtins__": builtins,
                    "print": custom_print,
                    "input": custom_input,
                    **ALLOWED_MODULES,  # thêm các thư viện được phép vào môi trường thực thi
                }

                exec(code, exec_globals)
            except Exception as e:
                print(f"Error: {type(e).__name__} - {str(e)}", file=error_buffer)

    thread = threading.Thread(target=execute_code)
    thread.start()
    thread.join(timeout=EXECUTION_TIMEOUT)

    if thread.is_alive():
        return jsonify({"output": "Error: Code execution timed out.", "error": True})

    output = output_buffer.getvalue()
    error = error_buffer.getvalue()

    if error:
        return jsonify({"output": f"Error during execution: {error}", "error": True})
    else:
        return jsonify({"output": output, "error": False})


@app.route("/share-code", methods=["POST"])
def share_code():
    data = request.json
    code = data.get("code", "")
    share_id = uuid.uuid4().hex

    # Lưu code vào thư mục tạm
    shared_code_dir = os.path.join(tempfile.gettempdir(), "shared_code")
    os.makedirs(shared_code_dir, exist_ok=True)

    with open(
        os.path.join(shared_code_dir, f"{share_id}.py"), "w", encoding="utf-8"
    ) as f:
        f.write(code)

    share_url = f"/view/{share_id}"
    return jsonify({"share_url": share_url})


@app.route("/view/<share_id>")
def view_shared_code(share_id):
    shared_code_path = os.path.join(
        tempfile.gettempdir(), "shared_code", f"{share_id}.py"
    )
    try:
        with open(shared_code_path, "r", encoding="utf-8") as f:
            code = f.read()
        return render_template("view_shared_code.html", code=code)
    except FileNotFoundError:
        # Trả về trang 404.html khi mã không tồn tại
        return render_template('404.html'), 404

@app.route("/install-library", methods=["POST"])
def install_library():
    return jsonify(
        {
            "success": False,
            "error": "Installing libraries dynamically is not supported for security reasons.",
        }
    )

@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404

if __name__ == "__main__":
    app.run(debug=True)
