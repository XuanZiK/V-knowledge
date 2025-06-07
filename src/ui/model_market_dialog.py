from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTableWidget, QTableWidgetItem,
    QMessageBox, QProgressBar, QComboBox, QProgressDialog
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from src.core.model_manager import ModelManager
import requests
import json
from datetime import datetime
import time

class ModelDownloadWorker(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(bool, str)
    
    def __init__(self, model_manager, model_name, model_type):
        super().__init__()
        self.model_manager = model_manager
        self.model_name = model_name
        self.model_type = model_type
        
    def run(self):
        try:
            # Simulate download progress
            for i in range(101):
                self.progress.emit(i)
                time.sleep(0.1)
            
            # Actually download the model
            success = self.model_manager.download_model(self.model_name, self.model_type)
            if success:
                self.finished.emit(True, "Model downloaded successfully!")
            else:
                self.finished.emit(False, "Model download failed. Please check your network connection or try again.")
        except Exception as e:
                          self.finished.emit(False, f"Download error: {str(e)}")

class ModelMarketDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.model_manager = ModelManager()
        self.init_ui()
        self.load_model_list()

    def init_ui(self):
        self.setWindowTitle("Model Market")
        self.setMinimumSize(800, 600)
        layout = QVBoxLayout(self)

        # Model type selection
        type_layout = QHBoxLayout()
        type_label = QLabel("Model Type:")
        self.model_type = QComboBox()
        self.model_type.addItems(["Embedding Models", "Reranking Models"])
        self.model_type.currentIndexChanged.connect(self.load_model_list)
        type_layout.addWidget(type_label)
        type_layout.addWidget(self.model_type)
        type_layout.addStretch()
        layout.addLayout(type_layout)

        # Model list
        self.model_table = QTableWidget()
        self.model_table.setColumnCount(6)
        self.model_table.setHorizontalHeaderLabels(["Model Name", "Size", "Language", "Description", "Status", "Action"])
        self.model_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.model_table)

        # Download progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)

        # Buttons
        button_layout = QHBoxLayout()
        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.load_model_list)
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        button_layout.addWidget(refresh_button)
        button_layout.addWidget(close_button)
        layout.addLayout(button_layout)

    def load_model_list(self):
        """Load model list"""
        self.model_table.setRowCount(0)
        model_type = self.model_type.currentText()
        
        try:
            # Get online model list
            models = []
            if model_type == "Embedding Models":
                models = [
                    {
                        "name": "sentence-transformers/all-MiniLM-L6-v2",
                        "size": "90MB",
                        "language": "Multilingual",
                        "description": "Lightweight multilingual text embedding model"
                    },
                    {
                        "name": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
                        "size": "120MB",
                        "language": "Multilingual",
                        "description": "High-performance multilingual text embedding model"
                    }
                ]
            else:
                models = [
                    {
                        "name": "cross-encoder/ms-marco-MiniLM-L-6-v2",
                        "size": "80MB",
                        "language": "English",
                        "description": "Lightweight text reranking model"
                    },
                    {
                        "name": "cross-encoder/ms-marco-TinyBERT-L-2-v2",
                        "size": "40MB",
                        "language": "English",
                        "description": "Ultra-lightweight text reranking model"
                    }
                ]

            # 获取本地模型列表
            local_models = self.model_manager.get_local_models(model_type)
            local_model_names = [m["name"] for m in local_models]

            for model in models:
                row = self.model_table.rowCount()
                self.model_table.insertRow(row)
                self.model_table.setItem(row, 0, QTableWidgetItem(model["name"]))
                self.model_table.setItem(row, 1, QTableWidgetItem(model["size"]))
                self.model_table.setItem(row, 2, QTableWidgetItem(model["language"]))
                self.model_table.setItem(row, 3, QTableWidgetItem(model["description"]))
                
                # Set status
                if model["name"] in local_model_names:
                    status = "Downloaded"
                    button_text = "Delete"
                    button_callback = lambda checked, m=model["name"]: self.delete_model(m)
                else:
                    status = "Not Downloaded"
                    button_text = "Download"
                    button_callback = lambda checked, m=model["name"]: self.download_model(m)
                
                self.model_table.setItem(row, 4, QTableWidgetItem(status))
                button = QPushButton(button_text)
                button.clicked.connect(button_callback)
                self.model_table.setCellWidget(row, 5, button)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load model list: {str(e)}")

    def download_model(self, model_name):
        """Download model"""
        try:
            self.progress_bar.show()
            self.progress_bar.setValue(0)
            
            # Create progress dialog
            progress_dialog = QProgressDialog(f"Downloading model: {model_name}", "Cancel", 0, 100, self)
            progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
            progress_dialog.setAutoClose(True)
            progress_dialog.setAutoReset(True)
            
            # Create download thread
            self.download_worker = ModelDownloadWorker(
                self.model_manager,
                model_name,
                self.model_type.currentText()
            )
            
            # Connect signals
            self.download_worker.progress.connect(progress_dialog.setValue)
            self.download_worker.finished.connect(
                lambda success, msg: self.handle_download_finished(success, msg, progress_dialog)
            )
            
            # Start download
            self.download_worker.start()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to download model: {str(e)}")
            self.progress_bar.hide()

    def delete_model(self, model_name):
        """Delete model"""
        try:
            reply = QMessageBox.question(
                self, "Confirm Delete",
                f"Are you sure you want to delete model {model_name}?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                success = self.model_manager.delete_model(model_name)
                if success:
                    QMessageBox.information(self, "Success", "Model deleted successfully")
                    self.load_model_list()
                else:
                    QMessageBox.critical(self, "Error", "Failed to delete model")
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to delete model: {str(e)}")

    def handle_download_finished(self, success, message, progress_dialog):
        progress_dialog.close()
        if success:
            self.progress_bar.hide()
            QMessageBox.information(self, "Download Complete", message)
            self.load_model_list()
        else:
            self.progress_bar.hide()
            QMessageBox.warning(self, "Download Failed", message) 