import http.server
import socketserver
import os
import socket
from urllib.parse import parse_qs
import email
from email import policy
from email.parser import BytesParser

PORT = 8081

html_form = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>File Upload</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
            background-color: #f4f4f9;
        }
        .container {
            text-align: center;
            background-color: #ffffff;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        }
        h1 {
            color: #333;
        }
        form {
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        input[type="file"] {
            margin-bottom: 10px;
        }
        input[type="submit"] {
            padding: 10px 20px;
            border: none;
            border-radius: 4px;
            background-color: #007bff;
            color: #ffffff;
            cursor: pointer;
            font-size: 16px;
        }
        input[type="submit"]:hover {
            background-color: #0056b3;
        }
        .message {
            margin-top: 20px;
            font-size: 18px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Upload a File</h1>
        <form enctype="multipart/form-data" method="post" action="/">
            <input type="file" name="file" required>
            <input type="submit" value="Upload">
        </form>
        <div class="message"></div>
    </div>
</body>
</html>
'''


class SimpleHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # Serve the HTML form for file upload
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(html_form.encode('utf-8'))

    def do_POST(self):
        # Handle file upload
        content_length = int(self.headers['Content-Length'])
        content_type = self.headers['Content-Type']
        boundary = content_type.split("=")[1].encode()

        data = self.rfile.read(content_length)
        body = data.split(b'--' + boundary + b'\r\n')[1]
        headers, file_data = body.split(b'\r\n\r\n', 1)
        file_data = file_data.rsplit(b'\r\n--' + boundary + b'--', 1)[0]

        headers = email.message_from_bytes(headers, policy=policy.default)
        file_name = headers.get_param('filename', header='Content-Disposition')

        if not file_name:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Failed to upload file: no filename provided")
            return

        file_name = self.get_unique_file_name(file_name)

        try:
            with open(file_name, "wb") as f:
                f.write(file_data)

            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"File uploaded successfully")
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(b"Failed to upload file")
            print(f"Error during file upload: {e}")

    def get_unique_file_name(self, file_name):
        # Generate a unique file name if the file already exists
        base, extension = os.path.splitext(file_name)
        counter = 1
        new_file_name = file_name
        while os.path.exists(new_file_name):
            new_file_name = f"{base}_{counter}{extension}"
            counter += 1
        return new_file_name


def get_local_ip():
    # Retrieve the local IP address
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # This doesn't have to be reachable
        s.connect(('10.254.254.254', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip


if __name__ == "__main__":
    Handler = SimpleHTTPRequestHandler
    local_ip = get_local_ip()

    with socketserver.TCPServer((local_ip, PORT), Handler) as httpd:
        print(f"Serving at http://{local_ip}:{PORT}")
        httpd.serve_forever()
