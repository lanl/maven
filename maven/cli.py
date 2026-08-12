import os
import subprocess
import socket
import getpass
import sys

PORT = 8505
APP = os.path.join(os.path.dirname(__file__), "app.py")


def main():
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"

    if os.name != "nt":
        subprocess.run(f"lsof -t -i:{PORT} | xargs -r kill -9", shell=True, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        from colorama import Fore, Style, init
        init(autoreset=True)
        subprocess.run(f'for /f "tokens=5" %a in (\'netstat -ano ^| findstr :{PORT}\') do taskkill /F /PID %a >nul 2>&1',
                       shell=True, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    is_remote = any(os.environ.get(x) for x in ["SSH_CONNECTION", "SSH_CLIENT", "SSH_TTY"])
    if is_remote:
        remote_user = getpass.getuser()
        remote_host = socket.getfqdn() or socket.gethostname()

        print("Open a new terminal window on your local machine and run:")
        if os.name != "nt":
            print(f" \033[1mssh -L {PORT}:localhost:{PORT} {remote_user}@{remote_host}\033[0m")
        else:
            print(f" {Style.BRIGHT}ssh -L {PORT}:localhost:{PORT} {remote_user}@{remote_host}{Style.RESET_ALL}")
        print(" (Leave the new terminal running while using the app)")

    if os.name != "nt":
        print(f"\nCopy \033[1;34mhttp://localhost:{PORT}\033[0m in a browser to launch Maven")
    else:
        print(f"\nCopy {Fore.BLUE}{Style.BRIGHT}http://localhost:{PORT}{Style.RESET_ALL} in a browser to launch MAVEN")

    print("To exit, enter [Ctrl+C] here")

    cmd = [sys.executable, "-m", "streamlit", "run", APP, f"--server.port={PORT}", "--server.headless=true",
           "--browser.gatherUsageStats=false"]
    proc = subprocess.Popen(cmd, env=env, stdin=None, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=1)
    try:
        for line in proc.stdout:
            line = line.rstrip("\n")
            if (
                "You can now view your Streamlit app" in line
                or "Local URL:" in line
                or "Network URL:" in line
                or "External URL:" in line
                or "For better performance" in line
                or "$ xcode-select" in line
                or "$ pip install watchdog" in line
                or "Uvicorn server started" in line
                or "Could not bind IPv6 wildcard address" in line
                or line == ""
            ):
                continue
            print(line, flush=True)
        proc.wait()
    except KeyboardInterrupt:
        print("\n Closing the Maven App.\n")
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
