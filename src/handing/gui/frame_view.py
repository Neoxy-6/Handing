import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QLabel, QSizePolicy

class FrameView(QLabel):
    """shows bgr frames scaled to fit, keeping aspect"""

    def __init__(self):
        super().__init__("starting camera...")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumSize(320, 240)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setStyleSheet("background: #111; color: #888;")

    def show_frame(self, bgr: np.ndarray) -> None:
        rgb = np.ascontiguousarray(bgr[:, :, ::-1])
        h, w = rgb.shape[:2]
        image = QImage(rgb.data, w, h, 3 * w, QImage.Format.Format_RGB888).copy()

        pixmap = QPixmap.fromImage(image)
        self.setPixmap(pixmap.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
