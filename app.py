from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import os, zipfile, tempfile
from spleeter.separator import Separator

app = Flask(__name__)
CORS(app)

def separate_audio(input_path, output_folder):
    separator = Separator('spleeter:4stems')
    separator.separate_to_file(input_path, output_folder)

    stems_subdir = os.path.join(output_folder, os.listdir(output_folder)[0])  # Get actual stem folder
    other_path = os.path.join(stems_subdir, "other.wav")
    guitar_path = os.path.join(stems_subdir, "guitar.wav")

    if os.path.exists(other_path):
        os.rename(other_path, guitar_path)

    return stems_subdir  # Return path to separated files

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

    if not difficulties:
        difficulties = ["Expert"]

    with tempfile.TemporaryDirectory() as temp_dir:
        song_folder = os.path.join(temp_dir, f"{song} - {artist}")
        os.makedirs(song_folder, exist_ok=True)

        audio_path = os.path.join(song_folder, "song.ogg")
        audio.save(audio_path)

        # Separate audio
        stems_dir = os.path.join(song_folder, "stems")
        os.makedirs(stems_dir, exist_ok=True)
        separated_path = separate_audio(audio_path, stems_dir)

        # Save art
        if art:
            art.save(os.path.join(song_folder, "album.png"))

        # song.ini
        with open(os.path.join(song_folder, "song.ini"), "w") as f:
            f.write(f"[Song]\nname = {song}\nartist = {artist}\nyear = {year}\n")

        # notes.chart
        chart_path = os.path.join(song_folder, "notes.chart")
        with open(chart_path, "w") as f_chart:
            f_chart.write(f"[Song]\n{{\n  name = \"{song}\"\n  artist = \"{artist}\"\n  year = \"{year}\"\n}}\n\n")
            f_chart.write("[SyncTrack]\n{\n  0 = TS 4\n  1920 = B 120000\n}\n\n")
            f_chart.write("[Events]\n{\n  0 = E \"section Intro\"\n}\n\n")

            section_names = {
                "Easy": "EasySingle",
                "Medium": "MediumSingle",
                "Hard": "HardSingle",
                "Expert": "ExpertSingle"
            }

            for diff in difficulties:
                section = section_names.get(diff)
                if section:
                    f_chart.write(f"[{section}]\n{{\n")
                    for i in range(3):
                        f_chart.write(f"  {i*480} = N {i} 0\n")
                    f_chart.write("}\n\n")

        # zip packaging
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
