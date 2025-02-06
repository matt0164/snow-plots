from flask import Flask, send_from_directory, redirect
import os

app = Flask(__name__)

# Set the heatmap directory
heatmap_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../images"))


@app.route("/")
def home():
    # Get the latest heatmap file
    heatmap_files = sorted(os.listdir(heatmap_dir))
    if not heatmap_files:
        return "No heatmap available."
    latest_heatmap = heatmap_files[-1]

    # Redirect to the latest heatmap
    return redirect(f"/heatmap/{latest_heatmap}")


@app.route("/heatmap/<filename>")
def heatmap(filename):
    return send_from_directory(heatmap_dir, filename)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)