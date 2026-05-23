"""
Startup script — boots both FastAPI backend and React frontend dev server.
Run from the project root: python run.py
"""

import subprocess
import sys
import os
import signal
import time

ROOT = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(ROOT, "backend")
FRONTEND_DIR = os.path.join(ROOT, "frontend")


def main():
    print("\n" + "=" * 60)
    print("  🚀  CauseIQ — AI Incident Root Cause Analyzer")
    print("=" * 60)
    print()

    # Check for .env
    env_file = os.path.join(BACKEND_DIR, ".env")
    if not os.path.exists(env_file):
        print("  ⚠️  No backend/.env file found!")
        print("  → Copy backend/.env.example to backend/.env")
        print("  → Set your GOOGLE_API_KEY in backend/.env")
        print()

    procs = []

    try:
        # Start FastAPI backend
        print("  [1/2] Starting FastAPI backend on http://localhost:8000")
        backend = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"],
            cwd=BACKEND_DIR,
        )
        procs.append(backend)
        time.sleep(1)

        # Start React frontend
        print("  [2/2] Starting React frontend on http://localhost:5173")
        frontend = subprocess.Popen(
            ["npm", "run", "dev"],
            cwd=FRONTEND_DIR,
            shell=True,
        )
        procs.append(frontend)

        print()
        print("  ✅  Dashboard ready at: http://localhost:5173")
        print("  ✅  API docs at:        http://localhost:8000/docs")
        print()
        print("  Press Ctrl+C to stop both servers.")
        print("=" * 60 + "\n")

        # Wait for either process to exit
        for p in procs:
            p.wait()

    except KeyboardInterrupt:
        print("\n\n  🛑  Shutting down...")
        for p in procs:
            p.terminate()
        for p in procs:
            try:
                p.wait(timeout=5)
            except subprocess.TimeoutExpired:
                p.kill()
        print("  ✅  All servers stopped.\n")


if __name__ == "__main__":
    main()
