import argparse

from handing.core import paths
from handing.core.clock import now_ms
from handing.detection.landmarker import Landmarker
from handing.input import preprocess
from handing.input.camera import Camera
from handing.recognition.classifier import Classifier
from handing.recognition.samples import SampleSet

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(prog = "handing", description = "print recognized gestures in the terminal")
    p.add_argument("--camera", type = int, default = 0)
    p.add_argument("--hands", type = int, default = 1, choices = (1, 2))
    p.add_argument("--max-distance", type = float, default = 2.0)

    return p.parse_args()

def main() -> None:
    args = parse_args()
    classifier = Classifier(SampleSet.load(paths.default_gestures()), max_distance = args.max_distance)

    print("ctrl+c to quit")

    with Camera(args.camera) as cam, Landmarker(paths.model_path(), num_hands = args.hands) as landmarker:
        try:
            while True:
                frame = cam.read()
                if frame is None:
                    continue

                rgb = preprocess.to_rgb(preprocess.fit_width(frame, 640))
                result = landmarker.detect(rgb, now_ms())

                parts = []
                for hand in result.hands:
                    pred = classifier.predict(hand, result.width, result.height)
                    parts.append(f"{hand.handedness:5} {pred.name:8} conf {pred.confidence:.2f}  dist {pred.distance:.2f}")

                line = "  |  ".join(parts) or "no hand"
                print(f"\r{line:<100}", end = "", flush = True)
        except KeyboardInterrupt:
            print()
