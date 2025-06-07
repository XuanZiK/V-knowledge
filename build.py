import PyInstaller.__main__
import os
 
# 获取当前目录
current_dir = os.path.dirname(os.path.abspath(__file__))

# 定义打包参数
params = [
    "run.py",  # 主程序入口
    "--name=Qdrant知识库管理系统",  # 应用程序名称
    "--onedir",  # 创建一个目录而不是单文件（对于Inno Setup更方便）
    "--windowed",  # 不显示控制台窗口
    # "--icon=icon.ico",  # 如果有图标请取消注释
    "--add-data=src;src",  # 添加源代码目录
    "--add-data=data;data",  # 添加数据目录
    "--hidden-import=PyQt6",
    "--hidden-import=PyQt6.QtSvg", 
    "--hidden-import=PyQt6.QtNetwork",
    "--hidden-import=qdrant_client",
    "--hidden-import=numpy",
    "--hidden-import=json",
]

# 执行打包
PyInstaller.__main__.run(params)