import subprocess
import threading
from flask import Flask

# Run main.py in a separate thread
def run_main():
    subprocess.Popen(["python", "bot.py"])

# Start the thread
threading.Thread(target=run_main).start()

# Set up a minimal Flask app
app = Flask(__name__)

@app.route("/GET", methods=["GET"])
def alive():
    return "Bot is alive", 200

# Run the Flask server
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
