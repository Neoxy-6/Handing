from pathlib import Path

from handing.control.states import State

ICONS = (Path(__file__).parent / "icons").as_posix()

BG = "#18181b"
SURFACE = "#232327"
BORDER = "#34343a"
TEXT = "#e7e7ea"
MUTED = "#9a9aa3"
ACCENT = "#3b82f6"
DANGER = "#ef4444"

STATE_COLORS = {
    State.STANDBY: "#71717a",
    State.LOCKED: "#71717a",
    State.IDLE: ACCENT,
    State.ACTIVE: "#22c55e",
}

# buttons pick a look with setProperty("role", "primary" | "danger")
SHEET = f"""
QWidget {{ background: {BG}; color: {TEXT}; font-size: 13px; }}
QLabel {{ background: transparent; }}
QLabel[role="muted"] {{ color: {MUTED}; font-size: 12px; }}
QLabel[role="title"] {{ color: {MUTED}; font-size: 11px; font-weight: 600; letter-spacing: 1px; }}
QFrame#card {{ background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 10px; }}

QPushButton {{
    background: #2e2e34; border: 1px solid {BORDER}; border-radius: 6px; padding: 6px 12px;
}}
QPushButton:hover {{ background: #38383f; }}
QPushButton:pressed {{ background: #27272c; }}
QPushButton[role="primary"] {{ background: {ACCENT}; border-color: {ACCENT}; color: white; }}
QPushButton[role="primary"]:hover {{ background: #5592f7; }}
QPushButton[role="danger"] {{ background: {DANGER}; border-color: {DANGER}; color: white; font-weight: 600; }}

QTreeWidget {{ background: transparent; border: none; outline: none; show-decoration-selected: 1; }}
QTreeWidget::item {{ padding: 6px 2px; border: none; }}
QTreeWidget::item:hover {{ background: #2a2a30; }}
QTreeWidget::item:selected {{ background: #2f3a52; color: {TEXT}; }}
QHeaderView {{ background: transparent; border: none; }}
QScrollBar:vertical {{ background: transparent; width: 8px; margin: 0; }}
QScrollBar::handle:vertical {{ background: #45454d; border-radius: 4px; min-height: 24px; }}
QScrollBar::handle:vertical:hover {{ background: #55555e; }}
QScrollBar::add-line, QScrollBar::sub-line, QScrollBar::add-page, QScrollBar::sub-page {{ height: 0; background: none; }}
QHeaderView::section {{ background: transparent; color: {MUTED}; border: none; padding: 2px; font-size: 11px; }}

QComboBox, QSpinBox, QDoubleSpinBox, QLineEdit {{
    background: #2a2a30; border: 1px solid {BORDER}; border-radius: 5px; padding: 4px 6px;
}}
QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus, QLineEdit:focus {{ border-color: {ACCENT}; }}
QComboBox {{ padding-right: 24px; }}
QComboBox::drop-down {{ border: none; width: 22px; }}
QComboBox::down-arrow {{ image: url({ICONS}/down.svg); width: 10px; height: 10px; }}
QComboBox QAbstractItemView {{
    background: {SURFACE}; border: 1px solid {BORDER}; outline: none; selection-background-color: #2f3a52;
}}
QSpinBox, QDoubleSpinBox {{ padding-right: 22px; }}
QSpinBox::up-button, QDoubleSpinBox::up-button, QSpinBox::down-button, QDoubleSpinBox::down-button {{
    subcontrol-origin: border; width: 20px; border: none; background: transparent;
}}
QSpinBox::up-button, QDoubleSpinBox::up-button {{ subcontrol-position: top right; }}
QSpinBox::down-button, QDoubleSpinBox::down-button {{ subcontrol-position: bottom right; }}
QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {{ image: url({ICONS}/up.svg); width: 9px; height: 9px; }}
QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {{ image: url({ICONS}/down.svg); width: 9px; height: 9px; }}

QCheckBox {{ spacing: 8px; background: transparent; }}
QCheckBox::indicator {{ width: 16px; height: 16px; border: 1px solid #5a5a63; border-radius: 4px; background: #2a2a30; }}
QCheckBox::indicator:hover {{ border-color: {ACCENT}; }}
QCheckBox::indicator:checked {{ background: {ACCENT}; border-color: {ACCENT}; image: url({ICONS}/check.svg); }}
QTabWidget::pane {{ border: 1px solid {BORDER}; border-radius: 6px; }}
QTabBar::tab {{ background: transparent; color: {MUTED}; padding: 6px 12px; }}
QTabBar::tab:selected {{ color: {TEXT}; border-bottom: 2px solid {ACCENT}; }}
QProgressBar {{ background: #2a2a30; border: none; border-radius: 4px; height: 8px; text-align: center; }}
QProgressBar::chunk {{ background: {ACCENT}; border-radius: 4px; }}
"""

def set_role(widget, role: str) -> None:
    """switch a styled role at runtime, qss needs a re-polish to notice"""
    widget.setProperty("role", role)
    widget.style().unpolish(widget)
    widget.style().polish(widget)
