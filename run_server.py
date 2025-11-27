#!/usr/bin/env python
"""
Simple script to run the Flask server.
Usage: python run_server.py
"""

if __name__ == '__main__':
    from src.flask.app import app
    import os

    port = int(os.environ.get('PORT', 5001))
    print(f"Starting Warframe Damage Calculator API on port {port}...")
    print(f"Access the web interface at: http://localhost:{port}")
    print(f"API documentation: http://localhost:{port}/api/health")
    app.run(debug=True, host='0.0.0.0', port=port)
