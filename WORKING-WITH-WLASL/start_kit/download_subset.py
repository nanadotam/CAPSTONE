import json
import os
import subprocess

# original subset glosses
GLOSSES = ["movie", "balance", "bracelet", "cereal", "your", "sorry", "fish", "dry", "convince", "arrive", "tea", "snow", "name", "talk", "meet"]

# code broke and i had to restart
# GLOSSES = ["dry", "convince", "arrive", "tea", "snow", "name", "talk", "meet"]


with open("WLASL_v0.3.json", "r") as f:
    data = json.load(f)

os.makedirs("subset_raw", exist_ok=True)

for entry in data:
    gloss = entry["gloss"]
    if gloss not in GLOSSES:
        continue

    for instance in entry["instances"]:
        url = instance["url"]
        video_id = instance["video_id"]

        output_path = f"subset_raw/{gloss}_{video_id}.mp4"

        print(f"Downloading {gloss} from {url}")

        cmd = [
            "yt-dlp",
            "--quiet",
            "--no-warnings",
            "-o", output_path,
            url
        ]

        subprocess.run(cmd)
