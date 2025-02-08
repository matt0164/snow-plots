import subprocess

repo_path = "/Users/mattalevy/PycharmProjects/snow-plots"

# Navigate to the repository
subprocess.run(["cd", repo_path], shell=True)

# Ensure we are on the correct branch
subprocess.run(["git", "checkout", "web_deploy"], check=True)

# Add all changes to the staging area
subprocess.run(["git", "add", "."], check=True)

# Commit the changes (you can modify the commit message)
commit_message = "Automated commit for web_deploy branch"
subprocess.run(["git", "commit", "-m", commit_message], check=True)

# Push the changes to the remote `web_deploy` branch
subprocess.run(["git", "push", "origin", "web_deploy"], check=True)

print(f"Successfully committed and pushed changes to web_deploy branch with message: '{commit_message}'")