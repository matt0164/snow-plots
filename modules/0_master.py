#!/usr/bin/env python
import subprocess
import sys


def run_script(script_name):
    print(f"Running {script_name}...")
    result = subprocess.run(
        ["python", script_name],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    # Print the output from the script
    print(result.stdout)
    # Check for errors
    if result.returncode != 0:
        print(f"Error running {script_name}:")
        print(result.stderr)
        sys.exit(result.returncode)
    else:
        print(f"Finished {script_name} successfully.\n")


if __name__ == "__main__":
    scripts = [
        "1_scraper.py",
        "2_parser.py",
        "3_combine_stations.py",
        "4_combine_date.py"
    ]
    for script in scripts:
        run_script(script)

    print("All scripts executed successfully!")