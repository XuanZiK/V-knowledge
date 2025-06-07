from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTextEdit, QLabel, QComboBox,
    QTableWidget, QTableWidgetItem, QMessageBox,
    QTabWidget, QFileDialog, QSpinBox, QGroupBox,
    QFormLayout, QLineEdit, QProgressBar, QSplitter,
    QInputDialog, QDialog, QHeaderView, QProgressDialog
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QAction, QIcon
import os
from datetime import datetime
from src.core.vector_store import VectorStore
from src.core.document_processor import DocumentProcessor
from src.ui.model_settings_dialog import ModelSettingsDialog
from src.core.logger import Logger
from .style_manager import StyleManager
import json

class ImportWorker(QThread):
    progress = pyqtSignal(int)
    error = pyqtSignal(str)
    finished = pyqtSignal()
    
    def __init__(self, processor, store, file_path, collection_name):
        super().__init__()
        self.processor = processor
        self.store = store
        self.file_path = file_path
        self.collection_name = collection_name
        self._is_running = True
        
    def stop(self):
        self._is_running = False
        
    def run(self):
        try:
            # Process document
            chunks = self.processor.process_document(self.file_path)
            
            # Import to vector storage
            total = len(chunks)
            for i, chunk in enumerate(chunks):
                if not self._is_running:
                    break
                # Only set is_first_chunk to True when processing the first chunk
                self.store.add_texts(self.collection_name, [chunk], is_first_chunk=(i == 0))
                self.progress.emit(int((i + 1) / total * 100))
                
            if self._is_running:
                self.finished.emit()
                
        except Exception as e:
            self.error.emit(str(e))
        finally:
            self._is_running = False

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.logger = Logger.get_logger()
        self.logger.info("初始化主窗口")
        
        try:
            # 初始化向量存储，不重置数据目录
            self.store = VectorStore(reset=False)
            self.processor = DocumentProcessor()
            self.init_ui()
            self.init_menu()
            self.load_style()
            
            # 如果没有集合，创建一个默认集合
            collections = self.store.get_collections()
            if not collections:
                default_collection = "默认知识库"
                if self.store.create_collection(default_collection):
                    self.store.current_collection = default_collection
                    self.refresh_kb_list()
                    self.logger.info(f"已创建默认集合: {default_collection}")
                else:
                    self.logger.error("创建默认集合失败")
                    QMessageBox.warning(self, "警告", "创建默认集合失败，请手动创建知识库")
            
        except ConnectionError as e:
            self.logger.error(f"连接错误: {str(e)}")
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.setWindowTitle("连接错误")
            msg.setText("无法连接到Qdrant服务器")
            msg.setInformativeText(str(e))
            msg.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg.exec()
            self.close()
        except Exception as e:
            self.logger.error(f"初始化错误: {str(e)}")
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.setWindowTitle("错误")
            msg.setText("应用程序初始化失败")
            msg.setInformativeText(str(e))
            msg.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg.exec()
            self.close()

    def load_style(self):
        """加载样式"""
        StyleManager.apply_theme(self, "dark")

    def init_menu(self):
        """初始化菜单"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu('file')
        
        # 创建知识库
        create_kb_action = QAction('creatingAKnowledgeBase', self)
        create_kb_action.triggered.connect(self.create_knowledge_base)
        file_menu.addAction(create_kb_action)
        
        # 导入文档
        import_doc_action = QAction('importingDocuments', self)
        import_doc_action.triggered.connect(self.import_document)
        file_menu.addAction(import_doc_action)
        
        # 设置菜单
        settings_menu = menubar.addMenu('settings')
        
        # 模型设置
        model_settings_action = QAction('modelSetup', self)
        model_settings_action.triggered.connect(self.show_model_settings)
        settings_menu.addAction(model_settings_action)
        
        # Qdrant 服务器设置
        qdrant_settings_action = QAction('Qdrant ServerSetup', self)
        qdrant_settings_action.triggered.connect(self.show_qdrant_settings)
        settings_menu.addAction(qdrant_settings_action)

    def init_ui(self):
        self.setWindowTitle("V-knowledge")
        self.setMinimumSize(800, 600)

        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # 创建选项卡
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)

        # 添加各个功能选项卡
        self.tab_widget.addTab(self.create_knowledge_base_tab(), "knowledgeBaseManagement")
        self.tab_widget.addTab(self.create_search_tab(), "searching")
        self.tab_widget.addTab(self.create_test_tab(), "retrievalTest")

    def create_knowledge_base_tab(self):
        """Create knowledge base management tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Knowledge base operations area
        kb_group = QGroupBox("Knowledge Base Operations")
        kb_layout = QVBoxLayout(kb_group)

        # Knowledge base list
        self.kb_table = QTableWidget()
        self.kb_table.setColumnCount(4)
        self.kb_table.setHorizontalHeaderLabels(["Knowledge Base Name", "Document Count", "Created At", "Action"])
        self.kb_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        kb_layout.addWidget(self.kb_table)

        # Operation buttons
        btn_layout = QHBoxLayout()
        create_btn = QPushButton(QIcon(":/icons/add.png"), "Create Knowledge Base")
        create_btn.clicked.connect(self.create_knowledge_base)
        import_btn = QPushButton(QIcon(":/icons/import.png"), "Import Document")
        import_btn.clicked.connect(self.import_document)
        refresh_btn = QPushButton(QIcon(":/icons/refresh.png"), "Refresh")
        refresh_btn.clicked.connect(self.refresh_kb_list)
        btn_layout.addWidget(create_btn)
        btn_layout.addWidget(import_btn)
        btn_layout.addWidget(refresh_btn)
        kb_layout.addLayout(btn_layout)

        layout.addWidget(kb_group)
        return widget

    def create_search_tab(self):
        """Create search tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Search configuration area
        search_config = QGroupBox("Search Configuration")
        config_layout = QFormLayout(search_config)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter search keywords")
        config_layout.addRow("Keywords:", self.search_input)
        
        self.kb_select = QComboBox()
        self.kb_select.addItems(self.store.get_collections())
        config_layout.addRow("Knowledge Base:", self.kb_select)

        search_btn = QPushButton(QIcon(":/icons/search.png"), "Search")
        search_btn.clicked.connect(self.search)
        config_layout.addRow("", search_btn)

        layout.addWidget(search_config)

        # Search results area
        search_results = QGroupBox("Search Results")
        results_layout = QVBoxLayout(search_results)
        
        self.result_table = QTableWidget()
        self.result_table.setColumnCount(3)
        self.result_table.setHorizontalHeaderLabels(["Similarity", "Document", "Content"])
        self.result_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        results_layout.addWidget(self.result_table)
        
        layout.addWidget(search_results)

        # Export button
        export_btn = QPushButton(QIcon(":/icons/export.png"), "Export Results")
        export_btn.clicked.connect(self.export_results)
        results_layout.addWidget(export_btn)

        return widget

    def create_test_tab(self):
        """Create search test tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Test configuration
        test_config = QGroupBox("Test Configuration")
        config_layout = QFormLayout(test_config)
        
        self.test_model_combo = QComboBox()
        self.test_model_combo.addItems([
            "sentence-transformers/all-MiniLM-L6-v2",
            "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        ])
        config_layout.addRow("Test Model:", self.test_model_combo)
        
        layout.addWidget(test_config)

        # Test input
        test_input = QGroupBox("Test Input")
        input_layout = QVBoxLayout(test_input)
        
        self.test_input = QTextEdit()
        self.test_input.setPlaceholderText("Enter test text...")
        input_layout.addWidget(self.test_input)
        
        test_btn = QPushButton("Start Test")
        test_btn.clicked.connect(self.run_test)
        input_layout.addWidget(test_btn)
        
        layout.addWidget(test_input)

        # Test results
        test_results = QGroupBox("Test Results")
        results_layout = QVBoxLayout(test_results)
        
        self.test_result_table = QTableWidget()
        self.test_result_table.setColumnCount(4)
        self.test_result_table.setHorizontalHeaderLabels(["Text", "Similarity", "Time", "Metadata"])
        results_layout.addWidget(self.test_result_table)
        
        layout.addWidget(test_results)
        return widget

    def create_knowledge_base(self):
        """Create new knowledge base"""
        name, ok = QInputDialog.getText(self, "Create Knowledge Base", "Enter knowledge base name:")
        if ok and name:
            try:
                self.logger.info(f"Creating knowledge base: {name}")
                self.store.create_collection(name)
                self.refresh_kb_list()
                QMessageBox.information(self, "Success", f"Knowledge base {name} created successfully!")
            except Exception as e:
                self.logger.error(f"Failed to create knowledge base: {str(e)}")
                QMessageBox.critical(self, "Error", f"Failed to create knowledge base: {str(e)}")

    def import_document(self):
        """Import document"""
        try:
            # Get selected knowledge base
            current_row = self.kb_table.currentRow()
            if current_row < 0:
                QMessageBox.warning(self, "Warning", "Please select a knowledge base first")
                return
                
            collection_name = self.kb_table.item(current_row, 0).text()
            
            # Select file
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Select Document",
                "",
                "Document Files (*.txt *.pdf *.docx)"
            )
            
            if file_path:
                self.logger.info(f"Importing document: {file_path} to knowledge base: {collection_name}")
                
                # Create progress dialog
                progress = QProgressDialog("Importing document...", "Cancel", 0, 100, self)
                progress.setWindowModality(Qt.WindowModality.WindowModal)
                progress.setAutoClose(True)
                progress.setAutoReset(True)
                progress.canceled.connect(self.cancel_import)
                
                # Create import worker thread
                self.import_worker = ImportWorker(self.processor, self.store, file_path, collection_name)
                self.import_worker.progress.connect(progress.setValue)
                self.import_worker.finished.connect(self.import_finished)
                self.import_worker.error.connect(lambda msg: QMessageBox.critical(self, "Error", msg))
                
                self.import_worker.start()
                
        except Exception as e:
            self.logger.error(f"Failed to import document: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to import document: {str(e)}")
            
    def cancel_import(self):
        """Cancel import"""
        if hasattr(self, 'import_worker') and self.import_worker.isRunning():
            self.import_worker.stop()
            self.import_worker.wait()
            
    def import_finished(self):
        """Import completed"""
        self.refresh_kb_list()
        QMessageBox.information(self, "Success", "Document import completed!")

    def refresh_kb_list(self):
        """刷新知识库列表"""
        try:
            self.logger.info("刷新知识库列表")
            collections = self.store.get_collections()
            
            self.kb_table.setRowCount(len(collections))
            for i, collection_name in enumerate(collections):
                # 获取集合信息
                info = self.store.get_collection_info(collection_name)
                
                # 设置知识库名称
                self.kb_table.setItem(i, 0, QTableWidgetItem(collection_name))
                
                # 设置文档数量
                self.kb_table.setItem(i, 1, QTableWidgetItem(str(info["points_count"])))
                
                # 设置创建时间
                created_at = info["created_at"]
                if isinstance(created_at, datetime):
                    created_at = created_at.strftime("%Y-%m-%d %H:%M:%S")
                self.kb_table.setItem(i, 2, QTableWidgetItem(str(created_at)))
                
                # 添加删除按钮
                delete_btn = QPushButton("Delete")
                delete_btn.clicked.connect(lambda checked, name=collection_name: self.delete_kb(name))
                self.kb_table.setCellWidget(i, 3, delete_btn)
            
            # **刷新搜索模块**
            self.refresh_search_module()
                
        except Exception as e:
            self.logger.error(f"刷新知识库列表失败: {str(e)}")
            QMessageBox.critical(self, "错误", f"刷新知识库列表失败: {str(e)}")

    def refresh_search_module(self):
        """刷新搜索模块"""
        try:
            # 更新知识库选择下拉框
            self.kb_select.clear()
            self.kb_select.addItems(self.store.get_collections())
            
            # 如果搜索框中有查询内容，重新执行搜索
            current_query = self.search_input.text()
            if current_query:
                self.search()
        except Exception as e:
            self.logger.error(f"刷新搜索模块失败: {str(e)}")
        

    def delete_kb(self, name):
        """删除知识库"""
        try:
            reply = QMessageBox.question(
                self,
                "确认删除",
                f"确定要删除知识库 {name} 吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.logger.info(f"删除知识库: {name}")
                self.store.delete_collection(name)
                self.refresh_kb_list()
                
        except Exception as e:
            self.logger.error(f"删除知识库失败: {str(e)}")
            QMessageBox.critical(self, "错误", f"删除知识库失败: {str(e)}")

    def show_model_settings(self):
        """显示模型设置对话框"""
        dialog = ModelSettingsDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            settings = dialog.get_settings()
            # TODO: 应用模型设置
            QMessageBox.information(self, "成功", "模型设置已更新！")

    def run_test(self):
        """Run retrieval test"""
        try:
            query = self.test_input.toPlainText().strip()
            if not query:
                QMessageBox.warning(self, "Warning", "Please enter test text")
                return

            # Set model
            model_name = self.test_model_combo.currentText()
            self.store.set_embedding_model(model_name)

            # Run test
            import time
            start_time = time.time()
            results = self.store.search(query, limit=5)
            end_time = time.time()

            # Show results
            self.test_result_table.setRowCount(len(results))
            for i, (score, source, text) in enumerate(results):
                self.test_result_table.setItem(i, 0, QTableWidgetItem(text[:100]))  # Show first 100 characters
                self.test_result_table.setItem(i, 1, QTableWidgetItem(f"{score:.4f}"))
                self.test_result_table.setItem(i, 2, QTableWidgetItem(f"{(end_time - start_time)*1000:.2f}ms"))
                self.test_result_table.setItem(i, 3, QTableWidgetItem(source))

        except Exception as e:
            self.logger.error(f"Test failed: {str(e)}")
            QMessageBox.critical(self, "Error", f"Test failed: {str(e)}")

    def search(self):
        """Search documents"""
        query = self.search_input.text()
        collection = self.kb_select.currentText()
        
        if not query:
            QMessageBox.warning(self, "Warning", "Please enter search keywords!")
            return
        
        try:
            results = self.store.search(query, collection)
            
            # Show results
            self.result_table.setRowCount(len(results))
            for i, (score, doc, content) in enumerate(results):
                self.result_table.setItem(i, 0, QTableWidgetItem(f"{score:.4f}"))
                self.result_table.setItem(i, 1, QTableWidgetItem(doc))
                self.result_table.setItem(i, 2, QTableWidgetItem(content))
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Search failed: {str(e)}")

    def export_results(self):
        """Export search results"""
        if self.result_table.rowCount() == 0:
            QMessageBox.warning(self, "Warning", "No search results to export!")
            return
            
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Results",
            "",
            "CSV files (*.csv);;Text files (*.txt)"
        )
        
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    if file_path.endswith(".csv"):
                        # Export CSV
                        f.write("Similarity,Document,Content\n")
                        for i in range(self.result_table.rowCount()):
                            score = self.result_table.item(i, 0).text()
                            doc = self.result_table.item(i, 1).text()
                            content = self.result_table.item(i, 2).text()
                            f.write(f"{score},{doc},{content}\n")
                    else:
                        # Export text
                        for i in range(self.result_table.rowCount()):
                            score = self.result_table.item(i, 0).text()
                            doc = self.result_table.item(i, 1).text()
                            content = self.result_table.item(i, 2).text()
                            f.write(f"Similarity: {score}\n")
                            f.write(f"Document: {doc}\n")
                            f.write(f"Content: {content}\n")
                            f.write("-" * 50 + "\n")
                
                QMessageBox.information(self, "Success", "Search results exported!")
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Export failed: {str(e)}")

    def show_qdrant_settings(self):
        """显示 Qdrant 服务器设置对话框"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Qdrant serverSetup")
        dialog.setMinimumWidth(400)
        
        layout = QFormLayout()
        
        # 连接模式：本地存储或服务器
        mode_combo = QComboBox()
        mode_combo.addItems(["localStorageMode", "serverMode"])
        layout.addRow("connectionMode:", mode_combo)
        
        # 服务器地址
        host_input = QLineEdit("localhost")
        layout.addRow("serverAddress:", host_input)
        
        # 服务器端口
        port_input = QSpinBox()
        port_input.setRange(1, 65535)
        port_input.setValue(6333)
        layout.addRow("serverPort:", port_input)
        
        # 按钮
        button_box = QHBoxLayout()
        save_button = QPushButton("save")
        cancel_button = QPushButton("cancel")
        
        button_box.addWidget(save_button)
        button_box.addWidget(cancel_button)
        
        # 主布局
        main_layout = QVBoxLayout()
        main_layout.addLayout(layout)
        main_layout.addLayout(button_box)
        
        dialog.setLayout(main_layout)
        
        # 连接信号
        save_button.clicked.connect(lambda: self.save_qdrant_settings(
            mode_combo.currentText(),
            host_input.text(),
            port_input.value(),
            dialog
        ))
        cancel_button.clicked.connect(dialog.close)
        
        # 初始化根据当前设置
        settings_path = os.path.join(os.getcwd(), "data", "settings.json")
        if os.path.exists(settings_path):
            try:
                with open(settings_path, "r", encoding="utf-8") as f:
                    settings = json.load(f)
                    if "qdrant" in settings:
                        qdrant_settings = settings["qdrant"]
                        mode_index = 0 if qdrant_settings.get("mode") == "local" else 1
                        mode_combo.setCurrentIndex(mode_index)
                        host_input.setText(qdrant_settings.get("host", "localhost"))
                        port_input.setValue(qdrant_settings.get("port", 6333))
            except Exception as e:
                self.logger.error(f"failedToLoadSettings: {str(e)}")
        
        dialog.exec()
    
    def save_qdrant_settings(self, mode, host, port, dialog):
        """保存 Qdrant 服务器设置"""
        try:
            # 创建设置目录
            settings_dir = os.path.join(os.getcwd(), "data")
            os.makedirs(settings_dir, exist_ok=True)
            
            # 保存设置到文件
            settings_path = os.path.join(settings_dir, "settings.json")
            
            # 读取现有设置（如果有）
            settings = {}
            if os.path.exists(settings_path):
                try:
                    with open(settings_path, "r", encoding="utf-8") as f:
                        settings = json.load(f)
                except Exception as e:
                    self.logger.error(f"failedToReadSettings: {str(e)}")
            
            # 更新设置
            settings["qdrant"] = {
                "mode": "local" if mode == "localStorageMode" else "server",
                "host": host,
                "port": port
            }
            
            # 保存设置
            with open(settings_path, "w", encoding="utf-8") as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
            
            QMessageBox.information(self, "success", "The Settings are saved and will take effect after restarting the application.")
            dialog.close()
            
        except Exception as e:
            QMessageBox.critical(self, "error", f"failedToSaveSettings: {str(e)}")
            self.logger.error(f"failedToSaveSettings: {str(e)}")