CantioDAW_DARK = {
    "bg_primary": "#0d1117",
    "bg_secondary": "#161b22",
    "bg_tertiary": "#1c2333",
    "bg_card": "#21262d",
    "bg_hover": "#30363d",
    "accent": "#e94560",
    "accent_dim": "#b83350",
    "accent_glow": "rgba(233, 69, 96, 0.25)",
    "text_primary": "#e6edf3",
    "text_secondary": "#8b949e",
    "text_muted": "#484f58",
    "border": "#30363d",
    "success": "#2ea043",
    "warning": "#d29922",
    "error": "#f85149",
    "info": "#58a6ff",
    "track_colors": ["#e94560", "#58a6ff", "#2ea043", "#d29922", "#bc8cff", "#f0883e"],
    "font_family": "Segoe UI, system-ui, sans-serif",
    "mono_font": "JetBrains Mono, Consolas, monospace",
    "font_size_small": 11,
    "font_size_normal": 13,
    "font_size_large": 16,
    "spacing": 4,
    "corner_radius": 6,
}

STYLESHEET = f"""
QMainWindow, QDialog {{
    background-color: {CantioDAW_DARK["bg_primary"]};
    color: {CantioDAW_DARK["text_primary"]};
}}
QMenuBar {{
    background-color: {CantioDAW_DARK["bg_secondary"]};
    color: {CantioDAW_DARK["text_primary"]};
    border-bottom: 1px solid {CantioDAW_DARK["border"]};
    padding: 2px;
    font-size: 13px;
}}
QMenuBar::item:selected {{
    background-color: {CantioDAW_DARK["bg_hover"]};
}}
QMenu {{
    background-color: {CantioDAW_DARK["bg_secondary"]};
    color: {CantioDAW_DARK["text_primary"]};
    border: 1px solid {CantioDAW_DARK["border"]};
    padding: 4px;
}}
QMenu::item {{
    padding: 6px 24px;
    border-radius: 4px;
}}
QMenu::item:selected {{
    background-color: {CantioDAW_DARK["accent"]};
}}
QToolBar {{
    background-color: {CantioDAW_DARK["bg_secondary"]};
    border-bottom: 1px solid {CantioDAW_DARK["border"]};
    spacing: 4px;
    padding: 4px 8px;
}}
QPushButton {{
    background-color: {CantioDAW_DARK["bg_card"]};
    color: {CantioDAW_DARK["text_primary"]};
    border: 1px solid {CantioDAW_DARK["border"]};
    border-radius: {CantioDAW_DARK["corner_radius"]}px;
    padding: 6px 14px;
    font-size: 12px;
}}
QPushButton:hover {{
    background-color: {CantioDAW_DARK["bg_hover"]};
    border-color: {CantioDAW_DARK["accent"]};
}}
QPushButton:pressed {{
    background-color: {CantioDAW_DARK["accent_dim"]};
}}
QPushButton#accent {{
    background-color: {CantioDAW_DARK["accent"]};
    border-color: {CantioDAW_DARK["accent"]};
    color: white;
    font-weight: 600;
}}
QPushButton#accent:hover {{
    background-color: {CantioDAW_DARK["accent_dim"]};
}}
QPushButton#transport {{
    background-color: {CantioDAW_DARK["bg_card"]};
    border-radius: 16px;
    min-width: 36px;
    min-height: 36px;
    max-width: 36px;
    max-height: 36px;
    font-size: 16px;
    padding: 0;
}}
QPushButton#transport:hover {{
    background-color: {CantioDAW_DARK["accent"]};
}}
QPushButton#record {{
    background-color: #c0392b;
}}
QPushButton#record:hover {{
    background-color: #e74c3c;
}}
QLabel {{
    color: {CantioDAW_DARK["text_primary"]};
    background: transparent;
}}
QSlider::groove:horizontal {{
    background: {CantioDAW_DARK["bg_card"]};
    height: 4px;
    border-radius: 2px;
}}
QSlider::handle:horizontal {{
    background: {CantioDAW_DARK["accent"]};
    width: 12px;
    height: 12px;
    margin: -4px 0;
    border-radius: 6px;
}}
QSlider::sub-page:horizontal {{
    background: {CantioDAW_DARK["accent"]};
    border-radius: 2px;
}}
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
    background-color: {CantioDAW_DARK["bg_primary"]};
    color: {CantioDAW_DARK["text_primary"]};
    border: 1px solid {CantioDAW_DARK["border"]};
    border-radius: 4px;
    padding: 6px 8px;
    font-size: 12px;
}}
QLineEdit:focus, QSpinBox:focus, QComboBox:focus {{
    border-color: {CantioDAW_DARK["accent"]};
}}
QComboBox::drop-down {{
    background-color: {CantioDAW_DARK["bg_card"]};
    border: none;
    width: 20px;
}}
QComboBox::down-arrow {{
    image: none;
    border: none;
}}
QListView, QTreeView, QListWidget {{
    background-color: {CantioDAW_DARK["bg_primary"]};
    color: {CantioDAW_DARK["text_primary"]};
    border: 1px solid {CantioDAW_DARK["border"]};
    border-radius: 4px;
}}
QListView::item:selected, QTreeView::item:selected {{
    background-color: {CantioDAW_DARK["accent"]};
}}
QListView::item:hover, QTreeView::item:hover {{
    background-color: {CantioDAW_DARK["bg_hover"]};
}}
QScrollBar:vertical {{
    background: {CantioDAW_DARK["bg_primary"]};
    width: 6px;
    border: none;
}}
QScrollBar::handle:vertical {{
    background: {CantioDAW_DARK["bg_card"]};
    min-height: 30px;
    border-radius: 3px;
}}
QScrollBar::handle:vertical:hover {{
    background: {CantioDAW_DARK["accent"]};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}
QScrollBar:horizontal {{
    background: {CantioDAW_DARK["bg_primary"]};
    height: 6px;
    border: none;
}}
QScrollBar::handle:horizontal {{
    background: {CantioDAW_DARK["bg_card"]};
    min-width: 30px;
    border-radius: 3px;
}}
QScrollBar::handle:horizontal:hover {{
    background: {CantioDAW_DARK["accent"]};
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0px;
}}
QStatusBar {{
    background-color: {CantioDAW_DARK["bg_secondary"]};
    color: {CantioDAW_DARK["text_muted"]};
    border-top: 1px solid {CantioDAW_DARK["border"]};
    font-size: 11px;
}}
QGroupBox {{
    border: 1px solid {CantioDAW_DARK["border"]};
    border-radius: 4px;
    margin-top: 8px;
    padding: 16px 8px 8px;
    color: {CantioDAW_DARK["text_secondary"]};
    font-size: 11px;
    font-weight: 600;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 6px;
}}
QTabWidget::pane {{
    background-color: {CantioDAW_DARK["bg_primary"]};
    border: 1px solid {CantioDAW_DARK["border"]};
    border-radius: 4px;
}}
QTabBar::tab {{
    background-color: {CantioDAW_DARK["bg_tertiary"]};
    color: {CantioDAW_DARK["text_secondary"]};
    padding: 8px 16px;
    border: none;
    margin-right: 2px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    font-size: 12px;
}}
QTabBar::tab:selected {{
    background-color: {CantioDAW_DARK["bg_primary"]};
    color: {CantioDAW_DARK["text_primary"]};
    border-bottom: 2px solid {CantioDAW_DARK["accent"]};
}}
QTabBar::tab:hover {{
    background-color: {CantioDAW_DARK["bg_hover"]};
}}
QProgressBar {{
    background-color: {CantioDAW_DARK["bg_card"]};
    border: none;
    border-radius: 3px;
    height: 4px;
    text-align: center;
    font-size: 11px;
    color: transparent;
}}
QProgressBar::chunk {{
    background-color: {CantioDAW_DARK["accent"]};
    border-radius: 3px;
}}
QCheckBox {{
    color: {CantioDAW_DARK["text_primary"]};
    spacing: 6px;
    font-size: 12px;
}}
QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border-radius: 3px;
    border: 1px solid {CantioDAW_DARK["border"]};
    background: {CantioDAW_DARK["bg_primary"]};
}}
QCheckBox::indicator:checked {{
    background: {CantioDAW_DARK["accent"]};
    border-color: {CantioDAW_DARK["accent"]};
}}
QDockWidget {{
    titlebar-close-icon: url(none);
    color: {CantioDAW_DARK["text_secondary"]};
    font-size: 12px;
}}
QDockWidget::title {{
    background-color: {CantioDAW_DARK["bg_secondary"]};
    padding: 6px;
    border-bottom: 1px solid {CantioDAW_DARK["border"]};
}}
"""
