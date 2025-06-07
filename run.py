#!/usr/bin/env python
"""
知识库管理系统启动脚本
"""
import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# 导入并运行主程序
from src.main import main

if __name__ == "__main__":
    main()