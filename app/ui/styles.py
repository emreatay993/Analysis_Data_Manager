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

app_stylesheet = button_style + "\n" + tab_style


