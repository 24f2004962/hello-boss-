import os
import subprocess
from datetime import datetime

def run_cmd(cmd):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error running {' '.join(cmd) if isinstance(cmd, list) else cmd}")
        print(f"Stdout: {result.stdout}")
        print(f"Stderr: {result.stderr}")
        return False
    return True

def main():
    now = datetime.now()
    timestamp_str = now.strftime("%Y%m%d_%H%M%S")
    filename = f"file_{timestamp_str}.txt"
    content = f"Automated file insertion at {now.isoformat()}\n"
    
    # Create the file
    with open(filename, "w") as f:
        f.write(content)
    print(f"Created file: {filename}")
    
    # Git operations
    if not run_cmd(f"git add {filename}"):
        return
    if not run_cmd(f'git commit -m "chore(auto): deploy automated sync file {filename} [skip ci]"'):
        return
    if not run_cmd("git push origin main"):
        return
    print("Successfully pushed to remote.")

if __name__ == "__main__":
    main()
