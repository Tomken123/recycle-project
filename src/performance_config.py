"""
性能優化配置文件
用於調整檢測系統的性能參數
"""

import torch
import cv2
import os

class PerformanceConfig:
    """性能配置類"""
    
    def __init__(self):
        # 圖片處理配置
        self.MAX_IMAGE_SIZE = 1024  # 最大圖片尺寸
        self.MIN_CONFIDENCE = 0.5   # 提高最小信心度閾值以提高準確率
        self.OVERLAP_THRESHOLD = 0.5  # 重疊檢測閾值
        
        # 緩存配置
        self.CACHE_SIZE = 100  # 檢測結果緩存大小
        self.CLASSIFICATION_CACHE_SIZE = 1000  # 分類緩存大小
        
        # 模型配置
        self.USE_GPU = torch.cuda.is_available()  # 是否使用GPU
        self.MODEL_DEVICE = 'cuda' if self.USE_GPU else 'cpu'
        
        # 檢測配置
        self.ENABLE_VERBOSE = False  # 關閉詳細輸出
        self.ENABLE_CACHE = True     # 啟用緩存
        self.ENABLE_PREPROCESSING = True  # 啟用預處理
        
        # 並行處理配置
        self.MAX_WORKERS = 2  # 最大並行工作數
        
        # 內存優化
        self.CLEAR_CACHE_INTERVAL = 50  # 每50次檢測清理一次緩存
        
    def optimize_torch_settings(self):
        """優化 PyTorch 設置"""
        if self.USE_GPU:
            # GPU 優化
            torch.backends.cudnn.benchmark = True
            torch.backends.cudnn.deterministic = False
        else:
            # CPU 優化
            torch.set_num_threads(min(4, os.cpu_count()))
    
    def get_model_config(self):
        """獲取模型配置"""
        return {
            'device': self.MODEL_DEVICE,
            'verbose': self.ENABLE_VERBOSE,
            'conf': self.MIN_CONFIDENCE,
            'iou': 0.5
        }
    
    def get_preprocessing_config(self):
        """獲取預處理配置"""
        return {
            'max_size': self.MAX_IMAGE_SIZE,
            'enable': self.ENABLE_PREPROCESSING
        }
    
    def get_cache_config(self):
        """獲取緩存配置"""
        return {
            'detection_cache_size': self.CACHE_SIZE,
            'classification_cache_size': self.CLASSIFICATION_CACHE_SIZE,
            'enable': self.ENABLE_CACHE,
            'clear_interval': self.CLEAR_CACHE_INTERVAL
        }

# 全局性能配置實例
performance_config = PerformanceConfig()

def get_performance_config():
    """獲取性能配置"""
    return performance_config

def optimize_system():
    """優化系統設置"""
    # 優化 PyTorch 設置
    performance_config.optimize_torch_settings()
    
    # 設置 OpenCV 優化
    cv2.setUseOptimized(True)
    cv2.setNumThreads(min(4, os.cpu_count()))
    
    print(f"✅ 系統優化完成:")
    print(f"   - GPU 可用: {performance_config.USE_GPU}")
    print(f"   - 設備: {performance_config.MODEL_DEVICE}")
    print(f"   - 最大圖片尺寸: {performance_config.MAX_IMAGE_SIZE}")
    print(f"   - 緩存啟用: {performance_config.ENABLE_CACHE}") 