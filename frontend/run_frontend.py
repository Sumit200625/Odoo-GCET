# frontend/run_frontend.py
import http.server
import socketserver
import os
import sys

PORT = 3000
FRONTEND_DIR = os.path.dirname(os.path.abspath(__file__))

class DecoupledFrontendHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=FRONTEND_DIR, **kwargs)

    def log_message(self, format, *args):
        # Clean logging format
        sys.stdout.write("[Frontend Server] %s\n" % (format % args))

if __name__ == '__main__':
    os.chdir(FRONTEND_DIR)
    with socketserver.TCPServer(("127.0.0.1", PORT), DecoupledFrontendHTTPRequestHandler) as httpd:
        print("\n" + "="*70)
        print("StockSense Decoupled SPA Frontend Server Running!")
        print(f"URL: http://127.0.0.1:{PORT}")
        print("Communicating with Backend REST API at: http://127.0.0.1:5000/api/v1")
        print("="*70 + "\n")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down Frontend Server...")
            httpd.server_close()
