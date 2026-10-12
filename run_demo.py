"""
Runner script for FHIR Dual Coding Prototype
Launches the Streamlit Clinician Portal UI.
"""

import sys
import subprocess


def main():
    print("=" * 60)
    print("  FHIR-Based Dual Coding Microservice (NAMASTE & ICD-11)")
    print("  Smart India Hackathon 2025 Prototype")
    print("=" * 60)
    print("\nStarting Streamlit Clinician Portal...\n")

    cmd = [sys.executable, "-m", "streamlit", "run", "app.py", "--server.headless", "false"]
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\nApplication stopped.")


if __name__ == "__main__":
    main()
