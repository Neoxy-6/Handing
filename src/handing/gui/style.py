from handing.control.states import State

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

QTreeWidget {{ background: transparent; border: none; outline: none; }}
QTreeWidget::item {{ padding: 6px 2px; border-radius: 4px; }}
QTreeWidget::item:selected {{ background: #2f3a52; color: {TEXT}; }}
QHeaderView {{ background: transparent; border: none; }}
QHeaderView::section {{ background: transparent; color: {MUTED}; border: none; padding: 2px; font-size: 11px; }}

QComboBox, QSpinBox, QDoubleSpinBox, QLineEdit {{
    background: #2a2a30; border: 1px solid {BORDER}; border-radius: 5px; padding: 4px 6px;
}}
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
