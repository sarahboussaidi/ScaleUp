#!/usr/bin/env python
"""
Quick launcher for Screenshot Engagement Evaluator Web Interface
Run this directly: python run_server.py
"""

import sys
import os

print("""
============================================================
  Screenshot Engagement Evaluator - Web Interface
============================================================
""")

# Check if engagement_pipeline exists
if not os.path.exists('engagement_pipeline.py'):
    print("[ERROR] engagement_pipeline.py not found")
    print("Please run this from the project root folder")
    sys.exit(1)

# Import and start Flask
try:
    from app import app
    print("[OK] Flask app imported successfully")
    print("[OK] Starting server on http://localhost:5000")
    print("\n" + "="*60)
    print("WEB INTERFACE READY!")
    print("="*60)
    print("\nOpen your browser: http://localhost:5000")
    print("\nTo stop: Press Ctrl+C\n")
    print("="*60 + "\n")
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=False,
        threaded=True,
        use_reloader=False
    )
except Exception as e:
    print(f"[ERROR] Failed to start: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
