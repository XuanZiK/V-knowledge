from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTableWidget, QTableWidgetItem,
    QMessageBox, QProgressBar, QComboBox,
    QTextEdit, QSplitter, QWidget, QFrame
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QColor, QPalette
from typing import List, Dict
import json

class SearchResultDialog(QDialog):
    def __init__(self, query: str, results: List[Dict], parent=None):
        super().__init__(parent)
        self.query = query
        self.results = results
        self.init_ui()
        self.load_results()

    def init_ui(self):
        self.setWindowTitle("Search Results")
        self.setMinimumSize(1000, 700)
        layout = QVBoxLayout(self)

        # Query information
        query_layout = QHBoxLayout()
        query_label = QLabel("Search Query:")
        query_layout.addWidget(query_label)
        query_text = QLabel(self.query)
        query_text.setStyleSheet("font-weight: bold;")
        query_layout.addWidget(query_text)
        query_layout.addStretch()
        layout.addLayout(query_layout)

        # Create splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)

        # Left side result list
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # Results statistics
        stats_layout = QHBoxLayout()
        self.stats_label = QLabel(f"Found {len(self.results)} results")
        stats_layout.addWidget(self.stats_label)
        
        # Sort method
        sort_label = QLabel("Sort by:")
        stats_layout.addWidget(sort_label)
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["Relevance", "Time"])
        self.sort_combo.currentIndexChanged.connect(self.sort_results)
        stats_layout.addWidget(self.sort_combo)
        
        stats_layout.addStretch()
        left_layout.addLayout(stats_layout)

        # Result list
        self.result_table = QTableWidget()
        self.result_table.setColumnCount(4)
        self.result_table.setHorizontalHeaderLabels(["Relevance", "Source", "Type", "Time"])
        self.result_table.horizontalHeader().setStretchLastSection(True)
        self.result_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.result_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.result_table.itemSelectionChanged.connect(self.show_content)
        left_layout.addWidget(self.result_table)
        
        splitter.addWidget(left_widget)

        # Right side content preview
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        preview_label = QLabel("Content Preview")
        preview_label.setStyleSheet("font-weight: bold;")
        right_layout.addWidget(preview_label)
        
        self.content_edit = QTextEdit()
        self.content_edit.setReadOnly(True)
        right_layout.addWidget(self.content_edit)
        
        # Metadata display
        self.metadata_label = QLabel()
        self.metadata_label.setWordWrap(True)
        self.metadata_label.setStyleSheet("color: gray;")
        right_layout.addWidget(self.metadata_label)
        
        splitter.addWidget(right_widget)

        # Set splitter ratio
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)

        # Buttons
        button_layout = QHBoxLayout()
        
        export_button = QPushButton("Export Results")
        export_button.clicked.connect(self.export_results)
        button_layout.addWidget(export_button)
        
        button_layout.addStretch()
        
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)

    def load_results(self):
        """Load search results"""
        self.result_table.setRowCount(len(self.results))
        for i, result in enumerate(self.results):
            # Relevance
            score = result.get("score", 0)
            score_item = QTableWidgetItem(f"{score:.2f}")
            score_item.setData(Qt.ItemDataRole.UserRole, score)
            self.result_table.setItem(i, 0, score_item)
            
            # Set background color based on relevance
            color = self.get_score_color(score)
            score_item.setBackground(color)
            
            # Source
            source = result.get("source", "").split("/")[-1]
            self.result_table.setItem(i, 1, QTableWidgetItem(source))
            
            # Type
            self.result_table.setItem(i, 2, QTableWidgetItem(result.get("file_type", "")))
            
            # Time
            self.result_table.setItem(i, 3, QTableWidgetItem(result.get("created_at", "")[:19]))
        
        # Auto-select first row
        if self.result_table.rowCount() > 0:
            self.result_table.selectRow(0)

    def show_content(self):
        """Show selected result content"""
        selected_rows = self.result_table.selectedItems()
        if not selected_rows:
            return
        
        row = selected_rows[0].row()
        result = self.results[row]
        
        # Show content
        content = result.get("content", "")
        self.content_edit.setText(content)
        
        # Highlight query terms
        self.highlight_query()
        
        # Show metadata
        metadata = {
            "Filename": result.get("filename", ""),
            "File Type": result.get("file_type", ""),
            "Created At": result.get("created_at", "")[:19],
            "Relevance": f"{result.get('score', 0):.2f}",
            "Chunk Type": result.get("chunk_type", ""),
            "Chunk Index": result.get("chunk_index", "")
        }
        
        metadata_text = " | ".join([f"{k}: {v}" for k, v in metadata.items() if v])
        self.metadata_label.setText(metadata_text)

    def highlight_query(self):
        """Highlight query terms"""
        cursor = self.content_edit.textCursor()
        format = cursor.charFormat()
        format.setBackground(QColor(255, 255, 0, 100))
        
        # Simple word matching, can be improved for smarter matching
        words = self.query.lower().split()
        for word in words:
            cursor = self.content_edit.document().find(word, 0, 
                QTextEdit.FindFlag.FindCaseSensitively)
            while not cursor.isNull():
                cursor.mergeCharFormat(format)
                cursor = self.content_edit.document().find(word, cursor, 
                    QTextEdit.FindFlag.FindCaseSensitively)

    def sort_results(self, index):
        """Sort results"""
        if index == 0:  # Sort by relevance
            self.results.sort(key=lambda x: x.get("score", 0), reverse=True)
        else:  # Sort by time
            self.results.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        
        self.load_results()

    def export_results(self):
        """Export search results"""
        try:
            data = {
                "query": self.query,
                "results": self.results
            }
            
            filename = f"search_results_{self.query[:30]}.json"
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            QMessageBox.information(self, "Success", f"Results exported to file: {filename}")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export results: {str(e)}")

    @staticmethod
    def get_score_color(score: float) -> QColor:
        """Get background color based on relevance score"""
        if score >= 0.8:
            return QColor(144, 238, 144, 100)  # Light green
        elif score >= 0.6:
            return QColor(255, 255, 224, 100)  # Light yellow
        elif score >= 0.4:
            return QColor(255, 228, 196, 100)  # Light orange
        else:
            return QColor(255, 192, 192, 100)  # Light red 