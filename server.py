
from http.server import SimpleHTTPRequestHandler, HTTPServer
import json

class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/api/news":
            data = [
                {
                    "title": "Alghimistry News API Berhasil Berjalan",
                    "source": "Alghimistry",
                    "category": "US Economy",
                    "description": "Server berita berhasil terhubung."
                }
            ]

            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(data).encode("utf-8"))
        else:
            super().do_GET()

HTTPServer(("0.0.0.0", 8001), Handler).serve_forever()
