import logging
import os
from datetime import datetime
from pathlib import Path

class Logger:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
            cls._instance._initialize_logger()
        return cls._instance
    
    def _initialize_logger(self):
        """初始化日志配置"""
        # 创建日志目录
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # 设置日志文件名
        log_file = log_dir / f"app_{datetime.now().strftime('%Y%m%d')}.log"
        
        # 配置日志格式
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # 文件处理器
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        
        # 获取根日志记录器
        self.logger = logging.getLogger('VectorSearch')
        self.logger.setLevel(logging.DEBUG)
        
        # 添加处理器
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    @classmethod
    def get_logger(cls):
        """获取日志记录器实例"""
        if cls._instance is None:
            cls()
        return cls._instance.logger

# 创建全局日志记录器
logger = Logger.get_logger() 