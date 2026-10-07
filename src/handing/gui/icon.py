from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QIcon, QImage, QPainter, QPixmap

# (x, y, w, h) in px, measured from the original drawing assets/icon/icon.png
HAND = [
    (0, 43, 10, 22),  # thumb
    (14, 5, 9, 37),
    (25, 0, 9, 42),
    (36, 0, 9, 42),
    (47, 12, 9, 30),
    (14, 45, 42, 31),  # palm
]
HAND_SIZE = (56, 76)
APP_COLOR = "#00a2e8"
MARGIN = 0.08  # share of the icon left empty on each side

def paint(painter: QPainter, size: int, color: str, badge: str | None = None) -> None:
    """the hand scaled to fit and centered; badge puts a dot bottom right"""
    w, h = HAND_SIZE
    scale = size * (1 - 2 * MARGIN) / max(w, h)
    ox, oy = (size - w * scale) / 2, (size - h * scale) / 2

    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor(color))
    for x, y, rw, rh in HAND:
        painter.drawRect(QRectF(ox + x * scale, oy + y * scale, rw * scale, rh * scale))

    if badge:
        d = size * 0.38
        painter.setBrush(QColor(badge))
        painter.drawEllipse(QRectF(size - d, size - d, d, d))

def render(size: int, color: str = APP_COLOR, badge: str | None = None) -> QImage:
    image = QImage(size, size, QImage.Format.Format_ARGB32)
    image.fill(Qt.GlobalColor.transparent)

    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    paint(painter, size, color, badge)
    painter.end()

    return image

def state_icon(color: str, badge: str | None) -> QIcon:
    """tray icon: the same hand in the state color"""
    icon = QIcon()
    for size in (16, 24, 32, 48, 64):
        icon.addPixmap(QPixmap.fromImage(render(size, color, badge)))

    return icon
