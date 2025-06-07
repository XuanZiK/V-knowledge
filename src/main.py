import sys
import os
import logging
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QSettings, Qt
from src.core.logger import Logger
 
# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 导入应用程序主窗口
from src.ui.main_window import MainWindow

def main():
    """主函数"""
    try:
        # 设置应用程序
        app = QApplication(sys.argv)
        
        # 设置日志
        logger = Logger.get_logger()
        logger.info("启动应用程序")
        
        # 创建主窗口
        window = MainWindow()
        window.show()
        
        # 运行应用程序
        sys.exit(app.exec())
        
    except Exception as e:
        logger = Logger.get_logger()
        logger.error(f"应用程序运行失败: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    sys.exit(main())
