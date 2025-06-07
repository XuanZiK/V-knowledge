import os
import json
from typing import Dict, List, Optional, Union, Any
import logging
from sentence_transformers import SentenceTransformer

class ModelRegistry:
    """Model registry, manages all available embedding and rerank models"""
    
    def __init__(self, config_path: str = "resources/models_config.json"):
        self.config_path = config_path
        self.embedding_models = {}
        self.rerank_models = {}
        self.active_embedding_model = None
        self.active_rerank_model = None
        self.load_models_config()
    
    def load_models_config(self):
        """Load model information from config file"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.embedding_models = config.get("embedding_models", {})
                    self.rerank_models = config.get("rerank_models", {})
                    self.active_embedding_model = config.get("active_embedding_model")
                    self.active_rerank_model = config.get("active_rerank_model")
            else:
                # Default configuration
                self.embedding_models = {
                    "all-MiniLM-L6-v2": {
                        "name": "all-MiniLM-L6-v2", 
                        "path": "sentence-transformers/all-MiniLM-L6-v2",
                        "dimension": 384,
                        "description": "General text embedding model, fast and lightweight"
                    }
                }
                self.rerank_models = {}
                self.active_embedding_model = "all-MiniLM-L6-v2"
                self.save_models_config()
        except Exception as e:
            logging.error(f"Failed to load model configuration: {str(e)}")
            raise
    
    def save_models_config(self):
        """保存模型配置到文件"""
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        config = {
            "embedding_models": self.embedding_models,
            "rerank_models": self.rerank_models,
            "active_embedding_model": self.active_embedding_model,
            "active_rerank_model": self.active_rerank_model
        }
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
            
    def add_embedding_model(self, name: str, model_path: str, dimension: int, description: str = ""):
        """添加新的embedding模型"""
        self.embedding_models[name] = {
            "name": name,
            "path": model_path,
            "dimension": dimension,
            "description": description
        }
        self.save_models_config()
    
    def add_rerank_model(self, name: str, model_path: str, description: str = ""):
        """添加新的rerank模型"""
        self.rerank_models[name] = {
            "name": name,
            "path": model_path,
            "description": description
        }
        self.save_models_config()
    
    def set_active_models(self, embedding_model: str = None, rerank_model: str = None):
        """设置当前活动的模型"""
        if embedding_model and embedding_model in self.embedding_models:
            self.active_embedding_model = embedding_model
        
        if rerank_model and rerank_model in self.rerank_models:
            self.active_rerank_model = rerank_model
            
        self.save_models_config()

class EmbeddingService:
    """嵌入服务，负责文本向量化"""
    
    def __init__(self, model_registry: ModelRegistry):
        self.model_registry = model_registry
        self.model = None
        self.load_active_model()
    
    def load_active_model(self):
        """加载当前活动的embedding模型"""
        if not self.model_registry.active_embedding_model:
            raise ValueError("未设置活动的embedding模型")
        
        model_info = self.model_registry.embedding_models.get(
            self.model_registry.active_embedding_model
        )
        if not model_info:
            raise ValueError(f"找不到模型: {self.model_registry.active_embedding_model}")
        
        try:
            self.model = SentenceTransformer(model_info["path"])
            logging.info(f"已加载embedding模型: {model_info['name']}")
        except Exception as e:
            logging.error(f"加载embedding模型失败: {str(e)}")
            raise
    
    def embed_text(self, text: Union[str, List[str]]) -> Union[List[float], List[List[float]]]:
        """将文本转换为向量"""
        if not self.model:
            self.load_active_model()
        
        try:
            embeddings = self.model.encode(text)
            return embeddings.tolist()
        except Exception as e:
            logging.error(f"文本向量化失败: {str(e)}")
            raise

class RerankService:
    """重排序服务，用于结果精排"""
    
    def __init__(self, model_registry: ModelRegistry):
        self.model_registry = model_registry
        self.model = None
        
    def load_model(self):
        """加载重排序模型"""
        if not self.model_registry.active_rerank_model:
            return None  # 重排序模型是可选的
            
        model_info = self.model_registry.rerank_models.get(
            self.model_registry.active_rerank_model
        )
        if not model_info:
            return None
            
        try:
            # 根据模型类型加载不同的模型实现
            # 这里仅为示例，实际实现可能需要根据具体模型类型调整
            from sentence_transformers import CrossEncoder
            self.model = CrossEncoder(model_info["path"])
            logging.info(f"已加载rerank模型: {model_info['name']}")
            return self.model
        except Exception as e:
            logging.error(f"加载rerank模型失败: {str(e)}")
            return None
    
    def rerank(self, query: str, documents: List[str], scores: List[float] = None) -> List[Dict[str, Any]]:
        """Rerank documents"""
        if not self.model:
            model = self.load_model()
            if not model:
                # If no reranking model available, return original order
                return [{"text": doc, "score": scores[i] if scores else 0} 
                        for i, doc in enumerate(documents)]
        
        try:
            # Create pairs for each document and query
            pairs = [[query, doc] for doc in documents]
            # Calculate relevance scores
            rerank_scores = self.model.predict(pairs)
            
            # Combine documents and scores, sort by score
            results = [{"text": doc, "score": float(score)} 
                       for doc, score in zip(documents, rerank_scores)]
            results.sort(key=lambda x: x["score"], reverse=True)
            
            return results
        except Exception as e:
            logging.error(f"Reranking failed: {str(e)}")
            # Return original order
            return [{"text": doc, "score": scores[i] if scores else 0} 
                    for i, doc in enumerate(documents)]
