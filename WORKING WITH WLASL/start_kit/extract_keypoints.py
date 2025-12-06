import os
import cv2
import numpy as np
import mediapipe as mp

INPUT_DIR = "subset_clips"
OUTPUT_DIR = "keypoints_dataset"
SEQUENCE_LENGTH = 50

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

def extract_keypoints(frame):
    """Extract up to 2-hand keypoints and ALWAYS return length 126."""
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(frame_rgb)

    keypoints = []

    if results.multi_hand_landmarks:
        for hand in results.multi_hand_landmarks[:2]:
            for lm in hand.landmark:
                keypoints.extend([lm.x, lm.y, lm.z])

        # If only 1 hand detected → pad remaining 63 values
        if len(results.multi_hand_landmarks) == 1:
            keypoints.extend([0.0] * 63)

    # If no hands detected → fill with zeros
    else:
        keypoints = [0.0] * 126

    # Safety: force EXACT size
    if len(keypoints) > 126:
        keypoints = keypoints[:126]
    elif len(keypoints) < 126:
        keypoints.extend([0.0] * (126 - len(keypoints)))

    return keypoints


def process_video(path):
    """Turn video into a fixed 50×126 matrix."""
    cap = cv2.VideoCapture(path)
    sequence = []

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        try:
            keypoints = extract_keypoints(frame)
        except Exception as e:
            print(f"[WARN] Frame processing failed in {path}: {e}")
            keypoints = [0.0] * 126  # safe fallback

        sequence.append(keypoints)

    cap.release()

    # Fix sequence length (pad or trim)
    if len(sequence) < SEQUENCE_LENGTH:
        while len(sequence) < SEQUENCE_LENGTH:
            sequence.append([0.0] * 126)
    else:
        sequence = sequence[:SEQUENCE_LENGTH]

    return np.array(sequence, dtype=np.float32)


def main():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    for gloss in os.listdir(INPUT_DIR):
        gloss_path = os.path.join(INPUT_DIR, gloss)
        if not os.path.isdir(gloss_path):
            continue

        out_gloss_dir = os.path.join(OUTPUT_DIR, gloss)
        os.makedirs(out_gloss_dir, exist_ok=True)

        for file in os.listdir(gloss_path):
            if not file.endswith(".mp4"):
                continue

            video_path = os.path.join(gloss_path, file)
            npy_path = os.path.join(out_gloss_dir, file.replace(".mp4", ".npy"))

            # Skip already completed files
            if os.path.exists(npy_path):
                print(f"[SKIP] Already processed: {npy_path}")
                continue

            print(f"[PROCESS] {video_path}")

            try:
                sequence = process_video(video_path)
                np.save(npy_path, sequence)
            except Exception as e:
                print(f"[ERROR] Could not process {video_path}: {e}")

    print("DONE ✔ All keypoints extracted safely.")


if __name__ == "__main__":
    main()
