#!/usr/bin/env python
"""Setup script for stock simulator."""
import subprocess
import sys
import os

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    print("Installing dependencies...")
    req_file = os.path.join(os.path.dirname(script_dir), "requirements.txt")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", req_file])
    
    print("\nStarting stock simulator...")
    os.chdir(script_dir)
    subprocess.call([sys.executable, "app.py"])

if __name__ == "__main__":
    main()
