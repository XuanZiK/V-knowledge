import os
import json
import shutil
from pathlib import Path
from typing import Dict, List, Optional
import torch
from sentence_transformers import SentenceTransformer
from transformers import AutoModelForSequenceClassification, AutoTokenizer
from datetime import datetime

class ModelManager:
    def __init__(self, cache_dir: str = "models"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.models_info_file = self.cache_dir / "models_info.json"
        self.models_info = self._load_models_info()

    def _load_models_info(self) -> Dict:
        """加载模型信息"""
        if self.models_info_file.exists():
            with open(self.models_info_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _save_models_info(self):
        """保存模型信息"""
        with open(self.models_info_file, "w", encoding="utf-8") as f:
            json.dump(self.models_info, f, ensure_ascii=False, indent=2)

    def get_available_models(self) -> List[Dict]:
        """获取可用模型列表"""
        models = []
        for model_name, info in self.models_info.items():
            model_path = self.cache_dir / info["path"]
            if model_path.exists():
                models.append({
                    "name": model_name,
                    "type": info["type"],
                    "size": self._format_size(model_path.stat().st_size),
                    "download_date": info["download_date"]
                })
        return models

    def download_model(self, model_name: str, model_type: str) -> bool:
        """下载模型"""
        try:
            # 创建模型目录
            model_dir = self.cache_dir / model_type / model_name
            model_dir.mkdir(parents=True, exist_ok=True)
            
            # 模拟下载过程
            # TODO: 实现实际的模型下载逻辑
            
            # 保存模型信息
            self.models_info[model_name] = {
                "type": model_type,
                "path": str(model_dir.relative_to(self.cache_dir)),
                "download_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            self._save_models_info()
            
            return True
        except Exception as e:
            print(f"下载模型失败: {str(e)}")
            # 清理未完成的下载
            if model_dir.exists():
                shutil.rmtree(model_dir)
            return False

    def delete_model(self, model_name: str) -> bool:
        """删除模型"""
        try:
            if model_name in self.models_info:
                model_path = self.cache_dir / self.models_info[model_name]["path"]
                if model_path.exists():
                    shutil.rmtree(model_path)
                del self.models_info[model_name]
                self._save_models_info()
                return True
            return False
        except Exception as e:
            print(f"删除模型失败: {str(e)}")
            return False

    def _format_size(self, size_bytes: int) -> str:
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} TB"

    def load_model(self, model_name: str, device: str = "cpu"):
        """Load model"""
        try:
            if model_name not in self.models_info:
                return None

            model_info = self.models_info[model_name]
            if model_info["type"] == "Embedding Models":
                model = SentenceTransformer(model_info["path"])
                model.to(device)
            else:
                model = AutoModelForSequenceClassification.from_pretrained(model_info["path"])
                model.to(device)
            return model
        except Exception as e:
            print(f"Failed to load model: {str(e)}")
            return None

    def get_local_models(self, model_type: Optional[str] = None) -> List[Dict]:
        """Get local model list"""
        models = []
        for name, info in self.models_info.items():
            if model_type is None or info["type"] == model_type:
                models.append({
                    "name": name,
                    **info
                })
        return models

    def _get_model_size(self, path: str) -> str:
        """Get model size"""
        total_size = 0
        path = Path(path)
        if path.is_dir():
            for file in path.glob("**/*"):
                if file.is_file():
                    total_size += file.stat().st_size
        else:
            total_size = path.stat().st_size

        # 转换为合适的单位
        units = ["B", "KB", "MB", "GB"]
        size = total_size
        unit_index = 0
        while size >= 1024 and unit_index < len(units) - 1:
            size /= 1024
            unit_index += 1
        return f"{size:.2f}{units[unit_index]}" 