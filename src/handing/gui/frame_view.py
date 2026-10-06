import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QLabel, QSizePolicy

class FrameView(QLabel):
    """shows bgr frames filling the widget, keeping aspect and cropping the overflow"""

    def __init__(self):
        super().__init__("starting camera...")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumSize(320, 240)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setStyleSheet("color: #888;")

    def show_frame(self, bgr: np.ndarray) -> None:
        rgb = np.ascontiguousarray(bgr[:, :, ::-1])
        h, w = rgb.shape[:2]
        image = QImage(rgb.data, w, h, 3 * w, QImage.Format.Format_RGB888).copy()

        size = self.size()
        scaled = QPixmap.fromImage(image).scaled(size, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)

        x = (scaled.width() - size.width()) // 2
        y = (scaled.height() - size.height()) // 2
        self.setPixmap(scaled.copy(x, y, size.width(), size.height()))
