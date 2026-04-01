import argparse
import subprocess
import time
import os

def run(cmd):
    """Helper to run shell commands with the current directory in PYTHONPATH."""
    print(f"Executing: {cmd}")
    env = os.environ.copy()
    env["PYTHONPATH"] = os.getcwd() + os.pathsep + env.get("PYTHONPATH", "")
    return subprocess.run(cmd, shell=True, env=env)

def kill_port_8000():
    """Smartly kill only the process on port 8000 on Windows."""
    try:
        # Find PID on 8000
        output = subprocess.check_output('netstat -ano | findstr :8000', shell=True).decode()
        for line in output.splitlines():
            if "LISTENING" in line:
                pid = line.strip().split()[-1]
                print(f"Stopping existing process {pid} on port 8000...")
                subprocess.run(f"taskkill /F /PID {pid}", shell=True, capture_output=True)
                time.sleep(1)
    except Exception:
        pass

def start_server():
    """Start the backend server in a separate process."""
    kill_port_8000()
    print("Starting Backend Server...")
    env = os.environ.copy()
    env["PYTHONPATH"] = os.getcwd() + os.pathsep + env.get("PYTHONPATH", "")
    return subprocess.Popen("python -m src.main", shell=True, env=env)

def main():
    parser = argparse.ArgumentParser(description="LLM Infra Platform Management CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    subparsers.add_parser("setup", help="Install dependencies and initialize database")
    subparsers.add_parser("run", help="Start the LLM Gateway server")
    subparsers.add_parser("dashboard", help="Launch the Streamlit analytics dashboard")
    subparsers.add_parser("simulate", help="Run a contextual V4.1 simulation (auto-starts server)")
    subparsers.add_parser("dev", help="Full Stack Mode: Run Server + Dashboard + Simulation")

    args = parser.parse_args()

    if args.command == "setup":
        run("pip install -r requirements.txt")
        run("python scripts/setup_db.py")
        run("python scripts/seed_data.py")

    elif args.command == "run":
        run("python -m src.main")

    elif args.command == "dashboard":
        run("streamlit run src/dashboard/app.py")

    elif args.command == "simulate":
        server = start_server()
        time.sleep(5)  # wait for server to boot
        try:
            run("python scripts/simulate.py --mode v4.1 --user test_user")
        finally:
            print("Shutting down server...")
            server.terminate()

    elif args.command == "dev":
        print("Starting Elite Demo Mode...")
        server = start_server()
        time.sleep(5)  # wait for server to boot and bind port 8000
        
        try:
            print("🚀 Phase 1: Running Elite Simulation...")
            run("python scripts/simulate.py --mode v4.1 --user dev_user")
            
            print("📊 Phase 2: Launching Analytics Dashboard...")
            run("streamlit run src/dashboard/app.py")
        except KeyboardInterrupt:
            print("\nStopping Demo Mode...")
        finally:
            server.terminate()

    else:
        parser.print_help()

if __name__ == "__main__":
    main()
