from PyQt6.QtGui import QPalette, QColor
from PyQt6.QtCore import Qt

class StyleManager:
    @staticmethod
    def get_dark_theme():
        """Get dark theme style"""
        return """
            QMainWindow {
                background-color: #2b2b2b;
            }
            QWidget {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QPushButton {
                background-color: #3b3b3b;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 5px 15px;
                color: #ffffff;
            }
            QPushButton:hover {
                background-color: #4b4b4b;
            }
            QPushButton:pressed {
                background-color: #2b2b2b;
            }
            QLineEdit, QTextEdit, QComboBox {
                background-color: #3b3b3b;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 5px;
                color: #ffffff;
            }
            QTableWidget {
                background-color: #2b2b2b;
                border: 1px solid #555555;
                gridline-color: #555555;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QTableWidget::item:selected {
                background-color: #4b4b4b;
            }
            QHeaderView::section {
                background-color: #3b3b3b;
                padding: 5px;
                border: 1px solid #555555;
            }
            QProgressBar {
                border: 1px solid #555555;
                border-radius: 4px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #4b4b4b;
            }
            QMessageBox {
                background-color: #2b2b2b;
            }
            QMessageBox QPushButton {
                min-width: 80px;
            }
        """

    @staticmethod
    def get_light_theme():
        """Get light theme style"""
        return """
            QMainWindow {
                background-color: #f0f0f0;
            }
            QWidget {
                background-color: #f0f0f0;
                color: #000000;
            }
            QPushButton {
                background-color: #e0e0e0;
                border: 1px solid #cccccc;
                border-radius: 4px;
                padding: 5px 15px;
                color: #000000;
            }
            QPushButton:hover {
                background-color: #d0d0d0;
            }
            QPushButton:pressed {
                background-color: #c0c0c0;
            }
            QLineEdit, QTextEdit, QComboBox {
                background-color: #ffffff;
                border: 1px solid #cccccc;
                border-radius: 4px;
                padding: 5px;
                color: #000000;
            }
            QTableWidget {
                background-color: #ffffff;
                border: 1px solid #cccccc;
                gridline-color: #cccccc;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QTableWidget::item:selected {
                background-color: #e0e0e0;
            }
            QHeaderView::section {
                background-color: #f0f0f0;
                padding: 5px;
                border: 1px solid #cccccc;
            }
            QProgressBar {
                border: 1px solid #cccccc;
                border-radius: 4px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #e0e0e0;
            }
            QMessageBox {
                background-color: #f0f0f0;
            }
            QMessageBox QPushButton {
                min-width: 80px;
            }
        """

    @staticmethod
    def apply_theme(app, theme="dark"):
        """应用主题到应用程序"""
        if theme == "dark":
            app.setStyleSheet(StyleManager.get_dark_theme())
        else:
            app.setStyleSheet(StyleManager.get_light_theme()) 