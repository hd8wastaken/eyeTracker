import os
import sys
import subprocess

base_dir = os.path.dirname(os.path.abspath(__file__))
main_path = os.path.join(base_dir, "src", "logic.py")

if not os.path.isfile(main_path):
    print(f"FAIL: could not find {main_path}")
    sys.exit(1)

result = subprocess.run([sys.executable, main_path])
sys.exit(result.returncode)