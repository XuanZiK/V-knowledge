from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTableWidget, QTableWidgetItem,
    QMessageBox, QProgressBar, QComboBox,
    QFileDialog, QCheckBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from pathlib import Path
import os
from src.core.document_processor import DocumentProcessor

class BatchImportWorker(QThread):
    progress = pyqtSignal(int, str)  # Progress value, current processing file
    file_progress = pyqtSignal(int)  # Single file processing progress
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, files, collection_name, store):
        super().__init__()
        self.files = files
        self.collection_name = collection_name
        self.store = store
        self.is_cancelled = False
        self.processor = DocumentProcessor()

    def run(self):
        try:
            total = len(self.files)
            for i, file in enumerate(self.files, 1):
                if self.is_cancelled:
                    break
                
                # Update total progress and current file
                self.progress.emit(int(i * 100 / total), file)
                
                try:
                    # Process document
                    chunks = self.processor.process_document(
                        file,
                        progress_callback=self.file_progress.emit
                    )
                    
                    # Save chunks to vector database
                    for j, chunk in enumerate(chunks):
                        if self.is_cancelled:
                            break
                        # 只在处理第一个块时设置is_first_chunk为True
                        self.store.add_texts(self.collection_name, [chunk], is_first_chunk=(j == 0))
                    
                except Exception as e:
                    print(f"Failed to process file: {file}, error: {str(e)}")
                    continue
                
            if not self.is_cancelled:
                self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))

    def cancel(self):
        self.is_cancelled = True

class BatchImportDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.files = []
        self.worker = None
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Batch Import Documents")
        self.setMinimumSize(800, 600)
        layout = QVBoxLayout(self)

        # Select knowledge base
        kb_layout = QHBoxLayout()
        kb_label = QLabel("Target Knowledge Base:")
        self.kb_combo = QComboBox()
        self.kb_combo.addItems(["Default Knowledge Base", "Knowledge Base 1", "Knowledge Base 2"])  # This should get from actual knowledge base list
        kb_layout.addWidget(kb_label)
        kb_layout.addWidget(self.kb_combo)
        kb_layout.addStretch()
        layout.addLayout(kb_layout)

        # File list
        self.file_table = QTableWidget()
        self.file_table.setColumnCount(5)
        self.file_table.setHorizontalHeaderLabels(["Filename", "Size", "Type", "Status", "Progress"])
        self.file_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.file_table)

        # Options
        options_group = QHBoxLayout()
        self.recursive_check = QCheckBox("Include Subfolders")
        self.recursive_check.setChecked(True)
        options_group.addWidget(self.recursive_check)
        
        self.skip_exists_check = QCheckBox("Skip Existing Files")
        self.skip_exists_check.setChecked(True)
        options_group.addWidget(self.skip_exists_check)
        
        options_group.addStretch()
        layout.addLayout(options_group)

        # Total progress
        progress_layout = QHBoxLayout()
        progress_layout.addWidget(QLabel("Total Progress:"))
        self.total_progress = QProgressBar()
        self.total_progress.hide()
        progress_layout.addWidget(self.total_progress)
        layout.addLayout(progress_layout)

        # Current file progress
        file_progress_layout = QHBoxLayout()
        file_progress_layout.addWidget(QLabel("File Progress:"))
        self.file_progress = QProgressBar()
        self.file_progress.hide()
        file_progress_layout.addWidget(self.file_progress)
        layout.addLayout(file_progress_layout)

        # Current file label
        self.current_file_label = QLabel()
        self.current_file_label.hide()
        layout.addWidget(self.current_file_label)

        # Buttons
        button_layout = QHBoxLayout()
        
        add_button = QPushButton("Add Files")
        add_button.clicked.connect(self.add_files)
        button_layout.addWidget(add_button)
        
        add_folder_button = QPushButton("Add Folder")
        add_folder_button.clicked.connect(self.add_folder)
        button_layout.addWidget(add_folder_button)
        
        clear_button = QPushButton("Clear List")
        clear_button.clicked.connect(self.clear_files)
        button_layout.addWidget(clear_button)
        
        button_layout.addStretch()
        
        self.import_button = QPushButton("Start Import")
        self.import_button.clicked.connect(self.start_import)
        button_layout.addWidget(self.import_button)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)

    def add_files(self):
        """Add files"""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Files",
            "",
            "Document Files (*.txt *.pdf *.doc *.docx);;All Files (*.*)"
        )
        
        if files:
            self.add_files_to_list(files)

    def add_folder(self):
        """Add folder"""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Folder"
        )
        
        if folder:
            files = []
            if self.recursive_check.isChecked():
                # Recursively traverse folder
                for root, _, filenames in os.walk(folder):
                    for filename in filenames:
                        if filename.endswith(('.txt', '.pdf', '.doc', '.docx')):
                            files.append(os.path.join(root, filename))
            else:
                # Only traverse current folder
                for filename in os.listdir(folder):
                    if filename.endswith(('.txt', '.pdf', '.doc', '.docx')):
                        files.append(os.path.join(folder, filename))
            
            if files:
                self.add_files_to_list(files)
            else:
                QMessageBox.warning(self, "Warning", "No supported document files found in the selected folder")

    def add_files_to_list(self, files):
        """Add files to list"""
        for file in files:
            if file not in self.files:
                self.files.append(file)
                path = Path(file)
                row = self.file_table.rowCount()
                self.file_table.insertRow(row)
                
                # Filename
                self.file_table.setItem(row, 0, QTableWidgetItem(path.name))
                
                # File size
                size = path.stat().st_size
                size_str = self.format_size(size)
                self.file_table.setItem(row, 1, QTableWidgetItem(size_str))
                
                # File type
                self.file_table.setItem(row, 2, QTableWidgetItem(path.suffix[1:].upper()))
                
                # Status
                self.file_table.setItem(row, 3, QTableWidgetItem("Pending"))
                
                # Progress
                progress_bar = QProgressBar()
                progress_bar.setRange(0, 100)
                progress_bar.setValue(0)
                self.file_table.setCellWidget(row, 4, progress_bar)

    def clear_files(self):
        """Clear file list"""
        self.files.clear()
        self.file_table.setRowCount(0)

    def start_import(self):
        """Start importing"""
        if not self.files:
            QMessageBox.warning(self, "Warning", "Please add files to import")
            return

        self.import_button.setEnabled(False)
        self.cancel_button.setText("Cancel Import")
        self.total_progress.show()
        self.total_progress.setValue(0)
        self.file_progress.show()
        self.file_progress.setValue(0)
        self.current_file_label.show()
        
        # Update all file status to pending
        for row in range(self.file_table.rowCount()):
            self.file_table.setItem(row, 3, QTableWidgetItem("Pending"))
            progress_bar = self.file_table.cellWidget(row, 4)
            if progress_bar:
                progress_bar.setValue(0)

        self.worker = BatchImportWorker(self.files, self.kb_combo.currentText(), self.store)
        self.worker.progress.connect(self.update_progress)
        self.worker.file_progress.connect(self.update_file_progress)
        self.worker.finished.connect(self.import_finished)
        self.worker.error.connect(self.import_error)
        self.worker.start()

    def update_progress(self, progress: int, current_file: str):
        """Update total progress"""
        self.total_progress.setValue(progress)
        self.current_file_label.setText(f"Processing: {current_file}")
        
        # Update file status
        for row in range(self.file_table.rowCount()):
            file_name = self.file_table.item(row, 0).text()
            if Path(current_file).name == file_name:
                self.file_table.setItem(row, 3, QTableWidgetItem("Processing"))
            elif progress > (row + 1) * 100 / self.file_table.rowCount():
                self.file_table.setItem(row, 3, QTableWidgetItem("Completed"))
                progress_bar = self.file_table.cellWidget(row, 4)
                if progress_bar:
                    progress_bar.setValue(100)

    def update_file_progress(self, progress: int):
        """Update file progress"""
        self.file_progress.setValue(progress)
        
        # Update current file progress bar
        current_file = self.current_file_label.text().replace("Processing: ", "")
        for row in range(self.file_table.rowCount()):
            file_name = self.file_table.item(row, 0).text()
            if current_file.endswith(file_name):
                progress_bar = self.file_table.cellWidget(row, 4)
                if progress_bar:
                    progress_bar.setValue(progress)
                break

    def import_finished(self):
        """Import completed"""
        self.total_progress.setValue(100)
        self.file_progress.setValue(100)
        self.current_file_label.setText("Import completed")
        self.import_button.setEnabled(True)
        self.cancel_button.setText("Close")
        
        # Update all unfinished files to completed
        for row in range(self.file_table.rowCount()):
            status = self.file_table.item(row, 3).text()
            if status != "Completed":
                self.file_table.setItem(row, 3, QTableWidgetItem("Completed"))
                progress_bar = self.file_table.cellWidget(row, 4)
                if progress_bar:
                    progress_bar.setValue(100)
        
        QMessageBox.information(self, "Success", "Document import completed")

    def import_error(self, error_msg: str):
        """Import error"""
        self.import_button.setEnabled(True)
        self.cancel_button.setText("Close")
        QMessageBox.critical(self, "Error", f"Document import failed: {error_msg}")

    def reject(self):
        """Close dialog"""
        if self.worker and self.worker.isRunning():
            reply = QMessageBox.question(
                self,
                "Confirm Cancel",
                "Document import is in progress. Are you sure you want to cancel?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.worker.cancel()
                self.worker.wait()
                super().reject()
        else:
            super().reject()

    @staticmethod
    def format_size(size: int) -> str:
        """Format file size"""
        units = ['B', 'KB', 'MB', 'GB', 'TB']
        size_float = float(size)
        unit_index = 0
        while size_float >= 1024 and unit_index < len(units) - 1:
            size_float /= 1024
            unit_index += 1
        return f"{size_float:.2f} {units[unit_index]}" 