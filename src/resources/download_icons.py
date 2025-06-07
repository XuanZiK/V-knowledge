import os
import requests
from pathlib import Path

def download_icon(url, filename):
    """下载图标文件"""
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        # 确保目录存在
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        # 保存文件
        with open(filename, "wb") as f:
            f.write(response.content)
            
        print(f"下载成功: {filename}")
    except Exception as e:
        print(f"下载失败 {filename}: {str(e)}")

def main():
    """Download all required icons"""
    # Icons directory
    icons_dir = Path(__file__).parent / "icons"
    
    # Icon URL list
    icons = {
        "app.png": "https://raw.githubusercontent.com/google/material-design-icons/master/src/navigation/apps/materialicons/24px.svg",
        "folder.png": "https://raw.githubusercontent.com/google/material-design-icons/master/src/file/folder/materialicons/24px.svg",
        "document.png": "https://raw.githubusercontent.com/google/material-design-icons/master/src/description/materialicons/24px.svg",
        "search.png": "https://raw.githubusercontent.com/google/material-design-icons/master/src/search/search/materialicons/24px.svg",
        "settings.png": "https://raw.githubusercontent.com/google/material-design-icons/master/src/settings/settings/materialicons/24px.svg",
        "import.png": "https://raw.githubusercontent.com/google/material-design-icons/master/src/file/upload/materialicons/24px.svg",
        "export.png": "https://raw.githubusercontent.com/google/material-design-icons/master/src/file/download/materialicons/24px.svg",
        "delete.png": "https://raw.githubusercontent.com/google/material-design-icons/master/src/action/delete/materialicons/24px.svg",
        "add.png": "https://raw.githubusercontent.com/google/material-design-icons/master/src/content/add/materialicons/24px.svg",
        "refresh.png": "https://raw.githubusercontent.com/google/material-design-icons/master/src/navigation/refresh/materialicons/24px.svg"
    }
    
    # 下载所有图标
    for filename, url in icons.items():
        filepath = icons_dir / filename
        download_icon(url, filepath)

if __name__ == "__main__":
    main() 