# -*- coding: utf-8 -*-
"""
app.py: WSGI development server entrypoint using the `app` callable from index.py.
"""
from wsgiref.simple_server import make_server
from index import app

if __name__ == "__main__":
    with make_server("0.0.0.0", 8080, app) as httpd:
        print("Serving qiskit-neat-fold demo at http://localhost:8080")
        httpd.serve_forever()
