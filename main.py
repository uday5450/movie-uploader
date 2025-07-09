import os
import random
import subprocess
import gdown
from flask import Flask, request, render_template_string
from instagrapi import Client

app = Flask(__name__)
OUTPUT_DIR = "reels_parts"
INPUT_VIDEO = "video.mp4"

# ========== HTML Template ==========
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>Upload Instagram Reel</title>
  <style>
    body { font-family: Arial; background: #111; color: #fff; padding: 20px; }
    input, textarea { width: 100%; margin: 10px 0; padding: 10px; font-size: 16px; }
    button { padding: 12px 20px; background: #00c853; border: none; color: white; cursor: pointer; }
    button:hover { background: #00b248; }
  </style>
</head>
<body>
  <h2>🎥 Upload Reels from Google Drive</h2>
  <form method="POST" action="/upload">
    <label>Google Drive URL:</label>
    <input type="text" name="drive_url" required>

    <label>Instagram Username:</label>
    <input type="text" name="username" required>

    <label>Instagram Password:</label>
    <input type="password" name="password" required>

    <label>Caption:</label>
    <textarea name="caption" rows="3">My Reel Caption ✨</textarea>

    <button type="submit">🚀 Start Upload</button>
  </form>
</body>
</html>
"""

# ========== FFmpeg Helpers ==========
def get_video_duration(path):
    result = subprocess.run([
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        path
    ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return int(float(result.stdout.decode().strip()))

def create_video_part_ffmpeg(input_path, start, end, output_path, part_number):
    text = f"Part {part_number}"
    command = [
        "ffmpeg", "-y",
        "-ss", str(start),
        "-t", str(end - start),
        "-i", input_path,
        "-vf", f"drawtext=text='{text}':x=(w-text_w)/2:y=20:fontsize=40:fontcolor=white:shadowcolor=black:shadowx=2:shadowy=2",
        "-c:v", "libx264", "-c:a", "aac",
        output_path
    ]
    subprocess.run(command, check=True)
    print(f"🎬 Created: {output_path}")

# ========== Upload Logic ==========
def download_video_from_drive(url, output_path=INPUT_VIDEO):
    print(f"⬇️ Downloading from Google Drive...")
    gdown.download(url, output_path, quiet=False, fuzzy=True)
    return output_path

def process_and_upload(input_file, output_folder, username, password, caption):
    os.makedirs(output_folder, exist_ok=True)
    duration = get_video_duration(input_file)

    print("🔐 Logging into Instagram...")
    cl = Client()
    cl.login(username, password)

    start = 0
    part_number = 1

    while start < duration:
        segment_duration = random.randint(25, 35)
        end = min(start + segment_duration, duration)
        part_path = os.path.join(output_folder, f"part_{part_number}.mp4")

        create_video_part_ffmpeg(input_file, start, end, part_path, part_number)

        print(f"📤 Uploading part {part_number}...")
        cl.clip_upload(part_path, caption=f"{caption} (Part {part_number})")
        print(f"✅ Uploaded part {part_number}")

        start = end
        part_number += 1

# ========== Routes ==========
@app.route("/", methods=["GET"])
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route("/upload", methods=["POST"])
def upload():
    try:
        drive_url = request.form.get("drive_url")
        username = request.form.get("username")
        password = request.form.get("password")
        caption = request.form.get("caption", "Your Reel Caption ✨")

        download_video_from_drive(drive_url)
        process_and_upload(INPUT_VIDEO, OUTPUT_DIR, username, password, caption)
        return "✅ All parts uploaded successfully!"

    except Exception as e:
        return f"❌ Error: {str(e)}", 500

# ========== Main ==========
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
