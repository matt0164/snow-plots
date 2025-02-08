import subprocess

repo_path = "/Users/mattalevy/PycharmProjects/snow-plots"

# Navigate to the repository
subprocess.run(["cd", repo_path], shell=True)

# Ensure we are on the correct branch
subprocess.run(["git", "checkout", "web_deploy"], check=True)

# Add all files, including untracked ones
subprocess.run(["git", "add", "-A"], check=True)

# Check if there are staged changes before committing
status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)

if status.stdout.strip():  # If there's anything to commit
    commit_message = "Automated commit for web_deploy branch"
    subprocess.run(["git", "commit", "-m", commit_message], check=True)
    subprocess.run(["git", "push", "origin", "web_deploy"], check=True)
    print(f"✅ Successfully committed and pushed changes to web_deploy branch with message: '{commit_message}'")
else:
    print("✅ No changes to commit. Skipping commit and push.")