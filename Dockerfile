# Sử dụng image Python chính thức
FROM python:3.9-slim

# Thiết lập working directory
WORKDIR /app

# Sao chép các file yêu cầu vào container
COPY requirements.txt .

# Cài đặt các thư viện từ requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Sao chép toàn bộ mã nguồn vào container
COPY . .

# Expose port
EXPOSE 8080

# Chạy ứng dụng Flask
CMD ["python", "app.py"]