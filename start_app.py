#!/usr/bin/env python3
"""
Startup script to launch both the FastAPI backend and frontend server.
"""

import subprocess
import time
import signal
import sys
from pathlib import Path

# Get the directory of this script
SCRIPT_DIR = Path(__file__).parent

def start_backend():
    """Start the FastAPI backend server"""
    print("🚀 Starting FastAPI backend server...")
    backend_cmd = [
        "uvicorn",
        "api:app",
        "--host",
        "0.0.0.0",
        "--port",
        "8000"
    ]
    return subprocess.Popen(backend_cmd)

def start_frontend():
    """Start the frontend server"""
    print("🌐 Starting frontend server...")
    frontend_cmd = [
        "python",
        str(SCRIPT_DIR / "serve_frontend.py")
    ]
    return subprocess.Popen(frontend_cmd)

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print("\n🛑 Shutting down servers...")
    backend_process.terminate()
    frontend_process.terminate()
    sys.exit(0)

if __name__ == "__main__":
    # Set up signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    
    print("📋 Starting Checkbox Detection Application...")
    print("=" * 50)
    
    # Start backend server
    backend_process = start_backend()
    
    # Wait a moment for backend to start
    time.sleep(3)
    
    # Start frontend server
    frontend_process = start_frontend()
    
    # Wait a moment for frontend to start
    time.sleep(2)
    
    print("\n Both servers are running!")
    print("Frontend: http://localhost:3000/frontend.html")
    print("Backend API: http://localhost:8000")
    print("API Docs: http://localhost:8000/docs")
    print("\nPress Ctrl+C to stop both servers")
    
    # Try to open the frontend in browser
    try:
        webbrowser.open('http://localhost:3000/frontend.html')
    except:
        pass
    
    # Wait for processes to complete
    try:
        backend_process.wait()
        frontend_process.wait()
    except KeyboardInterrupt:
        signal_handler(signal.SIGINT, None)
