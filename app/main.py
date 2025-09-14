import sys
from PyQt5 import QtWidgets
from app.ui.main_window import MainWindow
from app.utils.logging import get_logger


def main():
    logger = get_logger("app")
    logger.info("Application starting")
    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow()
    w.show()
    rc = app.exec_()
    logger.info("Application exiting with code %s", rc)
    sys.exit(rc)


if __name__ == "__main__":
    main()
