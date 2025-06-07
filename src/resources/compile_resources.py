import os
import subprocess

def compile_resources():
    """编译Qt资源文件"""
    # 获取当前目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 资源文件路径
    qrc_file = os.path.join(current_dir, "resources.qrc")
    
    # 输出文件路径
    output_file = os.path.join(current_dir, "resources_rc.py")
    
    # 编译命令
    cmd = f"pyrcc5 {qrc_file} -o {output_file}"
    
    try:
        subprocess.run(cmd, shell=True, check=True)
        print("资源文件编译成功！")
    except subprocess.CalledProcessError as e:
        print(f"资源文件编译失败: {str(e)}")
    except Exception as e:
        print(f"发生错误: {str(e)}")

if __name__ == "__main__":
    compile_resources() 