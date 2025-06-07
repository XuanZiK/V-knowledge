import os
import urllib.request
import subprocess


# 检查语言文件是否存在
inno_path = r"C:\Program Files (x86)\Inno Setup 6"
if not os.path.exists(inno_path):
    inno_path = r"C:\Program Files\Inno Setup 6"

lang_dir = os.path.join(inno_path, "Languages")
os.makedirs(lang_dir, exist_ok=True)

chinese_file = os.path.join(lang_dir, "ChineseSimplified.isl")
if not os.path.exists(chinese_file):
    print("下载中文语言文件...")
    url = "https://raw.githubusercontent.com/jrsoftware/issrc/main/Files/Languages/ChineseSimplified.isl"
    urllib.request.urlretrieve(url, chinese_file)
    print(f"已下载并保存到: {chinese_file}")

# 修改脚本使用默认语言路径
with open("setup.iss", "r", encoding="utf-8") as f:
    content = f.read()

if "compiler:Languages\\ChineseSimplified.isl" in content:
    content = content.replace(
        "compiler:Languages\\ChineseSimplified.isl", 
        "compiler:Default.isl"
    )
    with open("setup.iss", "w", encoding="utf-8") as f:
        f.write(content)
    print("已修改脚本使用默认语言")

# 编译
inno_compiler = os.path.join(inno_path, "ISCC.exe")
if os.path.exists(inno_compiler):
    print("编译脚本...")
    subprocess.run([inno_compiler, "setup.iss"])
    print("编译完成!")
else:
    print(f"找不到Inno Setup编译器: {inno_compiler}")