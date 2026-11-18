#!/usr/bin/env python3
"""
Lightweight Dashboard HTTP Server
Launches a local web server to view the Interactive WSN Dashboard in your browser.
"""

import http.server
import socketserver
import os
import sys
import webbrowser

PORT = 8080

def start_server():
    # Set root directory to repository root so relative SVG links work seamlessly
    dashboard_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(dashboard_dir)
    os.chdir(repo_root)

    Handler = http.server.SimpleHTTPRequestHandler
    Handler.extensions_map.update({
        '.svg': 'image/svg+xml',
        '.css': 'text/css',
        '.js': 'application/javascript',
        '.json': 'application/json'
    })

    try:
        with socketserver.TCPServer(("", PORT), Handler) as httpd:
            url = f"http://localhost:{PORT}/dashboard/index.html"
            print("=================================================================")
            print("  SMART ENVIRONMENTAL MONITORING & WSN DASHBOARD                 ")
            print("=================================================================")
            print(f"  [+] Local Server running at : {url}")
            print(f"  [+] Press Ctrl+C to stop the server")
            print("=================================================================\n")
            
            try:
                webbrowser.open(url)
            except Exception:
                pass
                
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[*] Server stopped.")
    except Exception as e:
        print(f"[!] Server error: {e}")

if __name__ == "__main__":
    start_server()
