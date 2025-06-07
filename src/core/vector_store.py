import os
import sys
import json
import shutil
import ast

import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from qdrant_client import QdrantClient, models
from qdrant_client.http.models import Distance, VectorParams
from src.core.logger import Logger
import numpy as np

# 简单的文本嵌入替代方案
class SimpleEmbedder:
    def __init__(self, vector_size=384):
        self.vector_size = vector_size

    def encode(self, texts):
        """简单的文本嵌入方法，生成随机向量"""
        # 使用文本的哈希值作为随机种子，确保相同文本生成相同向量
        vectors = []
        for text in texts:
            # 使用文本的哈希值作为随机种子
            seed = hash(str(text)) % 10000
            np.random.seed(seed)
            # 生成随机向量并转换为列表
            vector = np.random.rand(self.vector_size).tolist()
            vectors.append(vector)
        return vectors

class VectorStore:
    def __init__(self, host: str = "localhost", port: int = 6333, reset: bool = False):
        """初始化向量存储
        Args:
            host: Qdrant服务器地址
            port: Qdrant服务器端口
            reset: 是否重置数据目录
        """
        try:
            self.logger = Logger.get_logger()

            # 读取设置文件
            settings = self.load_settings()

            # 使用可在打包环境中工作的路径
            if getattr(sys, 'frozen', False):
                # 如果应用被打包（使用 PyInstaller 或类似工具）
                base_dir = os.path.dirname(sys.executable)
                self.logger.info(f"应用程序在打包环境中运行，基础目录: {base_dir}")
            else:
                # 如果应用在开发环境中运行
                base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                self.logger.info(f"应用程序在开发环境中运行，基础目录: {base_dir}")

            # 数据目录
            # 1. 尝试使用工作目录下的 data/qdrant
            data_dir = os.path.join(os.getcwd(), "data", "qdrant")
            if not os.path.exists(data_dir) or not os.access(data_dir, os.W_OK):
                # 2. 如果工作目录不可写，尝试使用用户目录
                data_dir = os.path.join(os.path.expanduser("~"), "qdrant_knowledge_base", "data")
                os.makedirs(data_dir, exist_ok=True)

            # 确保路径使用正确的分隔符
            data_dir = os.path.normpath(data_dir)

            # 只有在明确指定 reset=True 时才重置数据目录
            if reset and os.path.exists(data_dir):
                self.logger.warning("正在重置数据目录，所有数据将被删除！")
                shutil.rmtree(data_dir)
                self.logger.info("已重置数据目录")

            # 确保数据目录存在
            os.makedirs(data_dir, exist_ok=True)
            self.logger.info(f"数据目录路径: {data_dir}")

            # 根据设置决定使用本地存储模式还是服务器模式
            if settings and settings.get("qdrant", {}).get("mode") == "server":
                # 服务器模式
                server_host = settings["qdrant"].get("host", host)
                server_port = settings["qdrant"].get("port", port)

                self.logger.info(f"正在连接到 Qdrant 服务器: {server_host}:{server_port}")
                self.client = QdrantClient(
                    host=server_host,
                    port=server_port,
                    prefer_grpc=False,
                    timeout=10.0
                )

                # 测试连接
                self.client.get_collections()
                self.logger.info(f"成功连接到 Qdrant 服务器: {server_host}:{server_port}")
            else:
                # 本地存储模式
                storage_dir = os.path.join(data_dir, "storage")
                os.makedirs(storage_dir, exist_ok=True)

                self.client = QdrantClient(
                    path=storage_dir,
                    prefer_grpc=False,
                    timeout=10.0
                )

                # 测试连接
                self.client.get_collections()
                self.logger.info("成功使用本地存储模式")

            self.embedding_model = None
            self.embedder = SimpleEmbedder()
            self.current_collection = None
            self.config_file = os.path.join(data_dir, "kb_config.json")
            self.load_config()

        except Exception as e:
            self.logger.error(f"初始化向量存储失败: {str(e)}")
            raise ConnectionError(f"初始化向量存储失败: {str(e)}")

    def __del__(self):
        """清理资源"""
        try:
            if hasattr(self, 'client'):
                self.client.close()
        except Exception as e:
            self.logger.error(f"关闭 Qdrant 客户端失败: {str(e)}")

    def load_config(self):
        """加载知识库配置"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, "r", encoding="utf-8") as f:
                    self.config = json.load(f)
                self.logger.info(f"成功加载知识库配置: {self.config_file}")

                # 检查配置中的集合是否存在于 Qdrant 中
                collections = self.client.get_collections().collections
                collection_names = [collection.name for collection in collections]

                # 如果配置中的集合不存在于 Qdrant 中，则从配置中移除
                for name in list(self.config["collections"].keys()):
                    if name not in collection_names:
                        self.logger.warning(f"配置中的集合 {name} 不存在于 Qdrant 中，将从配置中移除")
                        del self.config["collections"][name]

                # 如果 Qdrant 中的集合不存在于配置中，则添加到配置中
                for name in collection_names:
                    if name not in self.config["collections"]:
                        self.logger.warning(f"Qdrant 中的集合 {name} 不存在于配置中，将添加到配置中")
                        collection_info = self.client.get_collection(name)
                        self.config["collections"][name] = {
                            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "doc_count": collection_info.points_count,
                            "vector_size": collection_info.config.params.vectors.size
                        }

                self.save_config()
            else:
                self.config = {"collections": {}}
                self.save_config()
                self.logger.info(f"创建新的知识库配置: {self.config_file}")
        except Exception as e:
            self.logger.error(f"加载配置失败: {str(e)}")
            self.config = {"collections": {}}
            self.save_config()

    def save_config(self):
        """保存知识库配置"""
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            self.logger.info(f"成功保存知识库配置: {self.config_file}")
        except Exception as e:
            self.logger.error(f"保存配置失败: {str(e)}")

    def create_collection(self, name, vector_size=384):
        """创建新的集合"""
        try:
            # 检查集合是否已存在
            collections = self.client.get_collections().collections
            collection_names = [collection.name for collection in collections]

            if name in collection_names:
                raise ValueError(f"集合 {name} 已存在")

            # 创建集合
            self.client.create_collection(
                collection_name=name,
                vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
            )

            # 更新配置
            self.config["collections"][name] = {
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "doc_count": 0,
                "vector_size": vector_size
            }
            self.save_config()

            self.current_collection = name
            self.logger.info(f"成功创建集合: {name}")
            return True
        except Exception as e:
            self.logger.error(f"创建集合失败: {str(e)}")
            return False

    def get_collections(self):
        """获取所有集合"""
        try:
            collections = self.client.get_collections().collections
            collection_names = []
            for collection in collections:
                collection_names.append(collection.name)
            return collection_names
        except Exception as e:
            self.logger.error(f"获取集合失败: {str(e)}")
            return []

    def get_collection_info(self, collection_name: str) -> Dict:
        """获取集合信息"""
        try:
            collection_info = self.client.get_collection(collection_name)
            # 使用配置文件中的文档计数，而不是points_count
            doc_count = self.config["collections"][collection_name]["doc_count"]
            return {
                "name": collection_name,
                "points_count": doc_count,  # 使用doc_count替代points_count
                "created_at": self.config["collections"][collection_name]["created_at"],  # 使用配置中的创建时间
                "status": collection_info.status
            }
        except Exception as e:
            self.logger.error(f"获取集合信息失败: {str(e)}")
            return {
                "name": collection_name,
                "points_count": 0,
                "created_at": "未知",
                "status": "未知"
            }

    def delete_collection(self, name):
        """删除集合"""
        try:
            self.client.delete_collection(collection_name=name)

            # 更新配置
            if name in self.config["collections"]:
                del self.config["collections"][name]
                self.save_config()

            if self.current_collection == name:
                self.current_collection = None

            return True
        except Exception as e:
            print(f"删除集合失败: {str(e)}")
            return False

    def add_texts(self, collection_name: str, texts: list, is_first_chunk: bool = False):
        """Add texts to collection
        Args:
            collection_name: Collection name
            texts: List of texts
            is_first_chunk: Whether this is the first chunk of the document, used to control document count, defaults to False
        """
        try:
            # Get current number of points in collection as starting ID
            collection_info = self.client.get_collection(collection_name)
            start_id = collection_info.points_count

            # Get vector representation of texts
            vectors = []
            for text in texts:
                vector = self.embedder.encode([text])[0]
                vectors.append(vector)

            # Prepare point data
            points = []
            for i, (vector, text) in enumerate(zip(vectors, texts)):
                point = models.PointStruct(
                    id=start_id + i,  # Use dynamically generated ID
                    vector=vector,
                    payload={
                        "text": str(text),  # Ensure text is string
                        "timestamp": str(datetime.now().isoformat())  # Ensure timestamp is string
                    }
                )
                points.append(point)

            # Batch add to collection
            self.client.upsert(
                collection_name=collection_name,
                points=points
            )

            # Update document count in config, only when processing first chunk
            if is_first_chunk and collection_name in self.config["collections"]:
                self.config["collections"][collection_name]["doc_count"] += 1
                self.save_config()

            self.logger.info(f"Successfully added {len(texts)} texts to collection {collection_name}")

        except Exception as e:
            self.logger.error(f"Failed to add texts: {str(e)}")
            raise

    def search(self, query, collection_name=None, limit=5):
        """Search texts
        Args:
            query: Search query
            collection_name: Collection name, if None use current collection
            limit: Result count limit
        Returns:
            list: Search results list, each element is a (score, source, text) tuple
        """
        try:
            # If no collection name specified, use current collection
            if collection_name is None:
                if self.current_collection is None:
                    # If no current collection, try to get first available collection
                    collections = self.get_collections()
                    if not collections:
                        raise ValueError("No available collections, please create one first")
                    collection_name = collections[0]
                    self.current_collection = collection_name
                else:
                    collection_name = self.current_collection

            # Encode query
            query_vector = self.embedder.encode([query])[0]
            print(
                'Encoding query'
            )
            # Search
            search_result = self.client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=limit
            )

            # Format results
            results = []
            for hit in search_result:
                print(hit.payload)
                document_name="Unknown Document"
                document_name=hit.payload.get("text","")
                if isinstance(document_name,str) and (document_name is not None):
                    document_name=ast.literal_eval(document_name).get('filename','Unknown Document')
                results.append((
                    hit.score,
                    document_name,
                    hit.payload.get("text", "")
                ))

            return results
        except Exception as e:
            self.logger.error(f"搜索失败: {str(e)}")
            return []

    def set_embedding_model(self, model):
        """设置嵌入模型"""
        self.embedding_model = model
        return True

    def load_settings(self):
        """加载设置"""
        try:
            # 1. 尝试从工作目录加载设置
            settings_path = os.path.join(os.getcwd(), "data", "settings.json")
            if os.path.exists(settings_path):
                with open(settings_path, "r", encoding="utf-8") as f:
                    return json.load(f)

            # 2. 如果找不到，尝试从用户目录加载设置
            user_settings_path = os.path.join(os.path.expanduser("~"), "qdrant_knowledge_base", "settings.json")
            if os.path.exists(user_settings_path):
                with open(user_settings_path, "r", encoding="utf-8") as f:
                    return json.load(f)

            # 3. 如果还是找不到，返回 None
            return None
        except Exception as e:
            self.logger.error(f"加载设置失败: {str(e)}")
            return None