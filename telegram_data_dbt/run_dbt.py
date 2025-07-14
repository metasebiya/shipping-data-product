# run_dbt.py
import os
from dotenv import load_dotenv
import subprocess
import sys

# Load environment variables from .env file in the current directory
load_dotenv()

# Get dbt arguments passed to this script (e.g., "debug", "run", "--select marts")
dbt_args = sys.argv[1:]

# Execute dbt command with the loaded environment variables
# os.environ contains all current environment variables, including those loaded by load_dotenv()
try:
    print(f"Running dbt with command: dbt {' '.join(dbt_args)}")
    subprocess.run(["dbt"] + dbt_args, env=os.environ, check=True)
except subprocess.CalledProcessError as e:
    print(f"dbt command failed with error: {e}")
    sys.exit(e.returncode)
except FileNotFoundError:
    print("Error: dbt command not found. Make sure dbt is installed and in your PATH.")
    print("You might need to activate your virtual environment: source venv/bin/activate")
    sys.exit(1)