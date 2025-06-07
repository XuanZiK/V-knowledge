from typing import List, Dict, Any
import time
import numpy as np
from sentence_transformers import SentenceTransformer
from sentence_transformers.evaluation import SentenceEvaluator
from torch.utils.data import DataLoader
import torch

class ModelTester:
    def __init__(self):
        self.test_sentences = [
            "This is a test sentence",
            "This is another test sentence",
            "This sentence is different from the above",
            "This sentence is completely different from the above",
            "This sentence is completely different from the above, but has similar length",
            "This sentence is completely different from the above, but has similar length and is in English",
            "This sentence is completely different from the above, but has similar length and is in English, with different content",
            "This sentence is completely different from the above, but has similar length and is in English, with different content, and they are all test sentences",
            "This sentence is completely different from the above, but has similar length and is in English, with different content, and they are all test sentences used for testing",
            "This sentence is completely different from the above, but has similar length and is in English, with different content, and they are all test sentences used for testing models"
        ]

    def test_model(self, model_name: str, device: str = "cpu") -> Dict[str, Any]:
        """测试模型性能"""
        try:
            # 加载模型
            model = SentenceTransformer(model_name)
            model.to(device)

            # 测试编码速度
            start_time = time.time()
            embeddings = model.encode(self.test_sentences, batch_size=32)
            encode_time = time.time() - start_time

            # 测试相似度计算
            start_time = time.time()
            similarities = np.zeros((len(self.test_sentences), len(self.test_sentences)))
            for i in range(len(self.test_sentences)):
                for j in range(i+1, len(self.test_sentences)):
                    sim = np.dot(embeddings[i], embeddings[j]) / (
                        np.linalg.norm(embeddings[i]) * np.linalg.norm(embeddings[j])
                    )
                    similarities[i][j] = sim
                    similarities[j][i] = sim
            similarity_time = time.time() - start_time

            # 测试内存使用
            if torch.cuda.is_available() and device == "cuda":
                memory_allocated = torch.cuda.memory_allocated() / 1024 / 1024  # MB
                memory_reserved = torch.cuda.memory_reserved() / 1024 / 1024  # MB
            else:
                memory_allocated = 0
                memory_reserved = 0

            return {
                "model_name": model_name,
                "device": device,
                "encode_time": encode_time,
                "similarity_time": similarity_time,
                "total_time": encode_time + similarity_time,
                "memory_allocated": memory_allocated,
                "memory_reserved": memory_reserved,
                "vector_size": embeddings.shape[1],
                "batch_size": 32
            }

        except Exception as e:
            raise Exception(f"模型测试失败: {str(e)}")

    def evaluate_model(self, model_name: str, test_data: List[Dict[str, str]], device: str = "cpu") -> Dict[str, float]:
        """评估模型性能"""
        try:
            model = SentenceTransformer(model_name)
            model.to(device)

            # 准备评估数据
            sentences1 = [item["query"] for item in test_data]
            sentences2 = [item["reference"] for item in test_data]
            scores = [item["score"] for item in test_data]

            # 计算相似度
            embeddings1 = model.encode(sentences1, batch_size=32)
            embeddings2 = model.encode(sentences2, batch_size=32)

            # 计算余弦相似度
            similarities = []
            for i in range(len(sentences1)):
                sim = np.dot(embeddings1[i], embeddings2[i]) / (
                    np.linalg.norm(embeddings1[i]) * np.linalg.norm(embeddings2[i])
                )
                similarities.append(sim)

            # 计算评估指标
            mse = np.mean((np.array(similarities) - np.array(scores)) ** 2)
            mae = np.mean(np.abs(np.array(similarities) - np.array(scores)))
            correlation = np.corrcoef(similarities, scores)[0, 1]

            return {
                "mse": mse,
                "mae": mae,
                "correlation": correlation
            }

        except Exception as e:
            raise Exception(f"模型评估失败: {str(e)}") 