from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QFormLayout, QComboBox,
    QSpinBox, QCheckBox, QGroupBox, QTabWidget,
    QDoubleSpinBox, QTextEdit, QTableWidget, QTableWidgetItem,
    QMessageBox, QWidget
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from src.core.model_tester import ModelTester
from src.core.model_manager import ModelManager
from src.ui.model_market_dialog import ModelMarketDialog

class ModelTestWorker(QThread):
    progress = pyqtSignal(dict)
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, model_tester, model_name, device):
        super().__init__()
        self.model_tester = model_tester
        self.model_name = model_name
        self.device = device

    def run(self):
        try:
            result = self.model_tester.test_model(self.model_name, self.device)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))

class ModelSettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.model_tester = ModelTester()
        self.model_manager = ModelManager()
        self.init_ui()
        self.refresh_model_list()

    def refresh_model_list(self):
        """Refresh model list"""
        # Refresh Embedding model list
        self.embedding_model.clear()
        embedding_models = self.model_manager.get_local_models("Embedding Models")
        if embedding_models:
            self.embedding_model.addItems([m["name"] for m in embedding_models])
        else:
            self.embedding_model.addItems([
                "sentence-transformers/all-MiniLM-L6-v2",
                "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
            ])

        # Refresh reranking model list
        self.rerank_model.clear()
        rerank_models = self.model_manager.get_local_models("Reranking Models")
        if rerank_models:
            self.rerank_model.addItems([m["name"] for m in rerank_models])
        else:
            self.rerank_model.addItems([
                "cross-encoder/ms-marco-MiniLM-L-6-v2",
                "cross-encoder/ms-marco-TinyBERT-L-2-v2"
            ])

    def init_ui(self):
        self.setWindowTitle("Model Configuration")
        self.setMinimumWidth(600)
        layout = QVBoxLayout(self)

        # Create tab widget
        tab_widget = QTabWidget()
        layout.addWidget(tab_widget)

        # Add each configuration tab
        tab_widget.addTab(self.create_embedding_tab(), "Embedding Model")
        tab_widget.addTab(self.create_rerank_tab(), "Reranking Model")
        tab_widget.addTab(self.create_advanced_tab(), "Advanced Configuration")
        tab_widget.addTab(self.create_test_tab(), "Performance Test")

        # Buttons
        button_layout = QHBoxLayout()
        save_button = QPushButton("Save")
        save_button.clicked.connect(self.accept)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

    def create_embedding_tab(self):
        """Create Embedding model configuration tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Model selection
        model_group = QGroupBox("Model Selection")
        model_layout = QFormLayout(model_group)

        model_select_layout = QHBoxLayout()
        self.embedding_model = QComboBox()
        model_select_layout.addWidget(self.embedding_model)
        
        market_button = QPushButton("Browse Model Market")
        market_button.clicked.connect(lambda: self.open_model_market("embedding"))
        model_select_layout.addWidget(market_button)
        
        model_layout.addRow("Model Selection:", model_select_layout)

        self.embedding_device = QComboBox()
        self.embedding_device.addItems(["cpu", "cuda"])
        model_layout.addRow("Running Device:", self.embedding_device)

        layout.addWidget(model_group)

        # Model parameters
        param_group = QGroupBox("Model Parameters")
        param_layout = QFormLayout(param_group)

        self.embedding_batch_size = QSpinBox()
        self.embedding_batch_size.setRange(1, 128)
        self.embedding_batch_size.setValue(32)
        param_layout.addRow("Batch Size:", self.embedding_batch_size)

        self.embedding_max_length = QSpinBox()
        self.embedding_max_length.setRange(32, 512)
        self.embedding_max_length.setValue(128)
        param_layout.addRow("Max Sequence Length:", self.embedding_max_length)

        self.embedding_pooling = QComboBox()
        self.embedding_pooling.addItems(["mean", "max", "cls"])
        param_layout.addRow("Pooling Method:", self.embedding_pooling)

        layout.addWidget(param_group)

        return widget

    def create_rerank_tab(self):
        """Create reranking model configuration tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Model selection
        model_group = QGroupBox("Model Selection")
        model_layout = QFormLayout(model_group)

        model_select_layout = QHBoxLayout()
        self.rerank_model = QComboBox()
        model_select_layout.addWidget(self.rerank_model)
        
        market_button = QPushButton("Browse Model Market")
        market_button.clicked.connect(lambda: self.open_model_market("rerank"))
        model_select_layout.addWidget(market_button)
        
        model_layout.addRow("Model Selection:", model_select_layout)

        self.rerank_device = QComboBox()
        self.rerank_device.addItems(["cpu", "cuda"])
        model_layout.addRow("Running Device:", self.rerank_device)

        layout.addWidget(model_group)

        # Model parameters
        param_group = QGroupBox("Model Parameters")
        param_layout = QFormLayout(param_group)

        self.rerank_batch_size = QSpinBox()
        self.rerank_batch_size.setRange(1, 128)
        self.rerank_batch_size.setValue(32)
        param_layout.addRow("Batch Size:", self.rerank_batch_size)

        self.rerank_max_length = QSpinBox()
        self.rerank_max_length.setRange(32, 512)
        self.rerank_max_length.setValue(128)
        param_layout.addRow("Max Sequence Length:", self.rerank_max_length)

        self.rerank_threshold = QDoubleSpinBox()
        self.rerank_threshold.setRange(0, 1)
        self.rerank_threshold.setValue(0.5)
        self.rerank_threshold.setSingleStep(0.1)
        param_layout.addRow("Similarity Threshold:", self.rerank_threshold)

        layout.addWidget(param_group)

        return widget

    def create_advanced_tab(self):
        """Create advanced configuration tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Cache configuration
        cache_group = QGroupBox("Cache Configuration")
        cache_layout = QFormLayout(cache_group)

        self.use_cache = QCheckBox("Enable Model Cache")
        self.use_cache.setChecked(True)
        cache_layout.addRow("", self.use_cache)

        self.cache_dir = QLineEdit()
        self.cache_dir.setPlaceholderText("Model Cache Directory")
        cache_layout.addRow("Cache Directory:", self.cache_dir)

        layout.addWidget(cache_group)

        # Performance configuration
        perf_group = QGroupBox("Performance Configuration")
        perf_layout = QFormLayout(perf_group)

        self.num_threads = QSpinBox()
        self.num_threads.setRange(1, 16)
        self.num_threads.setValue(4)
        perf_layout.addRow("Number of Threads:", self.num_threads)

        self.use_fp16 = QCheckBox("Use FP16 Acceleration")
        self.use_fp16.setChecked(False)
        perf_layout.addRow("", self.use_fp16)

        layout.addWidget(perf_group)

        return widget

    def create_test_tab(self):
        """Create performance test tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Test configuration
        test_group = QGroupBox("Test Configuration")
        test_layout = QFormLayout(test_group)

        self.test_model = QComboBox()
        self.test_model.addItems([
            "sentence-transformers/all-MiniLM-L6-v2",
            "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
            "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
        ])
        test_layout.addRow("Test Model:", self.test_model)

        self.test_device = QComboBox()
        self.test_device.addItems(["cpu", "cuda"])
        test_layout.addRow("Test Device:", self.test_device)

        layout.addWidget(test_group)

        # Test button
        test_btn = QPushButton("Start Test")
        test_btn.clicked.connect(self.run_test)
        layout.addWidget(test_btn)

        # Test results
        result_group = QGroupBox("Test Results")
        result_layout = QVBoxLayout(result_group)

        self.result_table = QTableWidget()
        self.result_table.setColumnCount(2)
        self.result_table.setHorizontalHeaderLabels(["Metric", "Value"])
        result_layout.addWidget(self.result_table)

        layout.addWidget(result_group)

        return widget

    def run_test(self):
        """Run performance test"""
        try:
            model_name = self.test_model.currentText()
            device = self.test_device.currentText()

            # Create test thread
            worker = ModelTestWorker(self.model_tester, model_name, device)
            worker.finished.connect(self.show_test_results)
            worker.error.connect(lambda msg: QMessageBox.critical(self, "Error", f"Test failed: {msg}"))
            worker.start()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Test failed: {str(e)}")

    def show_test_results(self, results: dict):
        """Show test results"""
        self.result_table.setRowCount(len(results))
        for i, (key, value) in enumerate(results.items()):
            self.result_table.setItem(i, 0, QTableWidgetItem(key))
            self.result_table.setItem(i, 1, QTableWidgetItem(str(value)))

    def open_model_market(self, model_type):
        """Open model market"""
        dialog = ModelMarketDialog(self)
        if model_type == "embedding":
            dialog.model_type.setCurrentText("Embedding Model")
        else:
            dialog.model_type.setCurrentText("Reranking Model")
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh_model_list()

    def get_settings(self):
        """Get settings"""
        return {
            "embedding": {
                "model": self.embedding_model.currentText(),
                "device": self.embedding_device.currentText(),
                "batch_size": self.embedding_batch_size.value(),
                "max_length": self.embedding_max_length.value(),
                "pooling": self.embedding_pooling.currentText()
            },
            "rerank": {
                "model": self.rerank_model.currentText(),
                "device": self.rerank_device.currentText(),
                "batch_size": self.rerank_batch_size.value(),
                "max_length": self.rerank_max_length.value(),
                "threshold": self.rerank_threshold.value()
            },
            "advanced": {
                "use_cache": self.use_cache.isChecked(),
                "cache_dir": self.cache_dir.text(),
                "num_threads": self.num_threads.value(),
                "use_fp16": self.use_fp16.isChecked()
            }
        } 