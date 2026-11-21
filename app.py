# -*- coding: utf-8 -*-
"""
app.py: Application entrypoint alias for Vercel Python runtime.
Directly points to handler from index.py.
"""
from index import handler, app

if __name__ == "__main__":
    from http.server import HTTPServer
    server = HTTPServer(("0.0.0.0", 8080), handler)
    print("Serving qiskit-neat-fold demo at http://localhost:8080")
    server.serve_forever()
