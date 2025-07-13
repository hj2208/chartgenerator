from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import os, zipfile, tempfile

app = Flask(__name__)
CORS(app)

@app.route("/api/generate", methods=["POST"])
def generate_chart():
    audio = request.files.get("audio")
    art = request.files.get("art")
    song = request.form.get("song")
    artist = request.form.get("artist")
    year = request.form.get("year")
    difficulties = request.form.getlist("difficulties")

    if not all([audio, song, artist, year]):
        return jsonify({"error": "Missing required fields"}), 400

    with tempfile.TemporaryDirectory() as temp_dir:
        song_folder = os.path.join(temp_dir, f"{song} - {artist}")
        os.makedirs(song_folder, exist_ok=True)

        with open(os.path.join(song_folder, "notes.chart"), "w") as f:
            f.write("// Simulated chart file with real logic
")

        with open(os.path.join(song_folder, "song.ini"), "w") as f:
            f.write(f"[Song]\nname = {song}\nartist = {artist}\nyear = {year}\n")

        if art:
            art.save(os.path.join(song_folder, "album.png"))

        zip_path = os.path.join(temp_dir, f"{song} - {artist}.zip")
        with zipfile.ZipFile(zip_path, "w") as z:
            for root, _, files in os.walk(song_folder):
                for file in files:
                    full_path = os.path.join(root, file)
                    arcname = os.path.relpath(full_path, song_folder)
                    z.write(full_path, arcname)

        return send_file(zip_path, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
