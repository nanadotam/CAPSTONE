import os
import json
import cv2
import datetime

# ----------------------------
# CONFIG
# ----------------------------

GLOSSES = [
    "movie", "balance", "bracelet", "cereal", "your", "sorry",
    "fish", "dry", "convince", "arrive", "tea", "snow",
    "name", "talk", "meet"
]

JSON_PATH = "WLASL_v0.3.json"
RAW_DIR = "subset_raw"
OUT_DIR = "subset_clips"
FPS = 25
LOG_FILE = "segmentation.log"

# If True → reprocess clips even if they exist but are size = 0 (corrupted)
REPROCESS_ZERO_SIZE = True


# ----------------------------
# LOGGING UTILITIES
# ----------------------------

def log(msg):
    timestamp = datetime.datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    final = f"{timestamp} {msg}"
    print(final)
    with open(LOG_FILE, "a") as f:
        f.write(final + "\n")


# ----------------------------
# HELPER FUNCTIONS
# ----------------------------

def load_json():
    log("Loading WLASL JSON annotations...")
    with open(JSON_PATH, "r") as f:
        return json.load(f)

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)
        log(f"Created folder: {path}")


# -----------------------------------------------------
# DOUBLE-EXTENSION FIXER
# -----------------------------------------------------

def resolve_video_path(base_path):
    expected_exts = ["mp4", "mkv", "webm", "mov"]
    candidates = [f"{base_path}.{ext}" for ext in expected_exts]

    # Try normal extensions
    for c in candidates:
        if os.path.exists(c):
            return c

    # Try any file starting with base (handles mkv.mp4, webm.mp4, etc)
    prefix = os.path.basename(base_path)
    all_files = os.listdir(RAW_DIR)

    matches = [f for f in all_files if f.startswith(prefix)]
    if matches:
        return os.path.join(RAW_DIR, matches[0])

    return None


# ----------------------------
# EXTRACT CLIP
# ----------------------------

def extract_segment(raw_path, out_path, start_frame, end_frame):
    cap = cv2.VideoCapture(raw_path)
    if not cap.isOpened():
        log(f"ERROR: Cannot open video file → {raw_path}")
        return False

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # Bounds fix
    if end_frame < 0 or end_frame >= total_frames:
        end_frame = total_frames - 1
    if start_frame < 0:
        start_frame = 0

    writer = cv2.VideoWriter(out_path, cv2.VideoWriter_fourcc(*"mp4v"), FPS, (width, height))

    frame_idx = 0
    extracted_count = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if start_frame <= frame_idx <= end_frame:
            writer.write(frame)
            extracted_count += 1

        frame_idx += 1

    writer.release()
    cap.release()

    if extracted_count == 0:
        log(f"WARNING: No frames extracted for {out_path}")
        return False

    return True


# ----------------------------
# MAIN PROCESS
# ----------------------------

def main():
    open(LOG_FILE, "w").close()
    log("===== SEGMENTATION PROCESS STARTED =====")

    data = load_json()
    ensure_dir(OUT_DIR)

    total_attempts = 0
    total_success = 0
    total_skipped = 0
    total_missing = 0

    for entry in data:
        gloss = entry["gloss"]

        if gloss not in GLOSSES:
            continue

        gloss_dir = os.path.join(OUT_DIR, gloss)
        ensure_dir(gloss_dir)

        for inst in entry["instances"]:
            video_id = inst["video_id"]
            start = inst["frame_start"] - 1
            end = inst["frame_end"] - 1

            total_attempts += 1

            # Resolve raw video
            base = os.path.join(RAW_DIR, f"{gloss}_{video_id}")
            raw_path = resolve_video_path(base)

            if raw_path is None:
                total_missing += 1
                log(f"MISSING FILE: {gloss}_{video_id}")
                continue

            out_path = os.path.join(gloss_dir, f"{gloss}_{video_id}.mp4")

            # -------------------------------
            # NEW: Already processed check
            # -------------------------------
            if os.path.exists(out_path):
                size = os.path.getsize(out_path)

                if size > 1000:  # non-zero → SKIP
                    total_skipped += 1
                    log(f"SKIP: {out_path} (already processed)")
                    continue

                # Zero-size corrupted file → optionally reprocess
                elif size == 0 and REPROCESS_ZERO_SIZE:
                    log(f"REPROCESSING CORRUPTED FILE: {out_path}")
                else:
                    log(f"SKIPPED CORRUPTED BUT IGNORE FLAG OFF: {out_path}")
                    continue

            # --------------------------------------------
            # PROCESS
            # --------------------------------------------
            log(f"PROCESSING: {raw_path} → {out_path}  [frames {start} to {end}]")

            ok = extract_segment(raw_path, out_path, start, end)
            if ok:
                total_success += 1
                log(f"SUCCESS: {out_path}")
            else:
                total_missing += 1
                log(f"FAILED: {raw_path}")

    # ----------------------------
    # SUMMARY
    # ----------------------------
    log("===== SEGMENTATION PROCESS COMPLETED =====")
    log(f"Total attempts: {total_attempts}")
    log(f"Successfully segmented: {total_success}")
    log(f"Already processed / skipped: {total_skipped}")
    log(f"Missing or failed: {total_missing}")
    log(f"Output folder: {OUT_DIR}/")


if __name__ == "__main__":
    main()
