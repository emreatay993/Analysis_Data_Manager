button_style = """
    QPushButton {
        background-color: #e7f0fd;
        border: 1px solid #5b9bd5;
        padding: 10px;
        border-radius: 5px;
    }
    QPushButton:hover {
        background-color: #cce4ff;
    }
"""

tab_style = """
    QTabBar::tab {
        background-color: #d6e4f5;  /* Pale blue background for inactive tabs */
        border: 1px solid #5b9bd5;   /* Default border for tabs */
        padding: 3px;
        border-top-left-radius: 5px;  /* Upper left corner rounded */
        border-top-right-radius: 5px; /* Upper right corner rounded */
        margin: 2px;
    }
    QTabBar::tab:hover {
        background-color: #cce4ff;  /* Background color when hovering over tabs */
    }
    QTabBar::tab:selected {
        background-color: #e7f0fd;  /* Active tab has your blue theme color */
        border: 2px solid #5b9bd5;  /* Thicker border for the active tab */
        color: #000000;  /* Active tab text color */
    }
    QTabBar::tab:!selected {
        background-color: #d6e4f5;  /* Paler blue for unselected tabs */
        color: #808080;  /* Gray text for inactive tabs */
        margin-top: 3px;  /* Make the unselected tabs slightly smaller */
    }
"""

menu_style = """
    QMenuBar {
        background-color: #e7f0fd;
        border-bottom: 1px solid #5b9bd5;
    }
    QMenuBar::item {
        background: transparent;
        padding: 5px 10px;
        margin: 0px 2px;
        border-radius: 4px;
        color: #000000;
    }
    QMenuBar::item:selected {
        background: #cce4ff;
        color: #000000;
    }
    QMenu {
        background-color: #f7fbff;
        border: 1px solid #5b9bd5;
        padding: 4px;
    }
    QMenu::item {
        padding: 6px 16px;
        border-radius: 4px;
        color: #000000;
    }
    QMenu::item:selected {
        background-color: #cce4ff;
        color: #000000;
    }
"""

combobox_style = """
    QComboBox {
        background-color: #e7f0fd;
        border: 1px solid #5b9bd5;
        padding: 6px 28px 6px 8px;  /* room for arrow */
        border-radius: 5px;
        color: #000000;
    }
    QComboBox:hover {
        background-color: #cce4ff;
    }
    QComboBox:focus {
        border: 2px solid #5b9bd5;
        background-color: #e7f0fd;
    }
    QComboBox::drop-down {
        subcontrol-origin: padding;
        subcontrol-position: top right;
        width: 22px;
        border-left: 1px solid #5b9bd5;
        border-top-right-radius: 5px;
        border-bottom-right-radius: 5px;
        background: #e7f0fd;
    }
    QComboBox::down-arrow {
        width: 0; height: 0;
        border-left: 5px solid transparent;
        border-right: 5px solid transparent;
        border-top: 7px solid #5b9bd5;
        margin-right: 6px;
    }
    QComboBox QAbstractItemView {
        background: #ffffff;
        border: 1px solid #5b9bd5;
        selection-background-color: #cce4ff;
        selection-color: #000000;
        outline: none;
    }
"""

inputs_style = """
    QLineEdit, QTextEdit, QPlainTextEdit {
        background: #ffffff;
        border: 1px solid #5b9bd5;
        border-radius: 5px;
        padding: 6px 8px;
        color: #000000;
        selection-background-color: #cce4ff;
        selection-color: #000000;
    }
    QLineEdit:hover, QTextEdit:hover, QPlainTextEdit:hover {
        background: #f7fbff;
    }
    QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
        border: 2px solid #5b9bd5;
        background: #ffffff;
    }
    QTextEdit, QPlainTextEdit {
        padding: 8px;  /* slightly larger for multi-line */
    }
"""

splitter_style = """
    QSplitter::handle {
        background-color: #cce4ff;
        border: 1px solid #5b9bd5;
        margin: 2px;
    }
    QSplitter::handle:hover {
        background-color: #abd9e9;
    }
    QSplitter::handle:horizontal {
        width: 6px;
    }
    QSplitter::handle:vertical {
        height: 6px;
    }
"""

main_window_separator_style = """
    QMainWindow::separator {
        background-color: #cce4ff;
        border: 1px solid #5b9bd5;
        width: 6px;   /* thickness for vertical separators */
        height: 6px;  /* thickness for horizontal separators */
        margin: 0px;
    }
    QMainWindow::separator:hover {
        background-color: #abd9e9;
    }
"""

app_stylesheet = "\n".join([
    button_style,
    tab_style,
    menu_style,
    combobox_style,
    inputs_style,
    splitter_style,
    main_window_separator_style,
])


