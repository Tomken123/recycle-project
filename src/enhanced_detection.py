import cv2
import numpy as np
from ultralytics import YOLO
import torch
from PIL import Image
import streamlit as st
import os
import torch.serialization
import warnings
from functools import lru_cache
import time
from src.performance_config import get_performance_config, optimize_system
warnings.filterwarnings("ignore")

# 優化系統設置
optimize_system()

class EnhancedRecyclingDetector:
    def __init__(self):
        # 獲取性能配置
        self.config = get_performance_config()
        
        # 修復 PyTorch 2.6 模型載入問題
        self._setup_torch_compatibility()
        
        # 使用您的自定義模型和預訓練模型
        try:
            # 獲取模型配置
            model_config = self.config.get_model_config()
            
            # 先嘗試載入通用模型（這個應該能正常工作）
            self.general_model = YOLO("yolov8n.pt")
            
            # 嘗試載入自定義模型
            try:
                self.custom_model = YOLO("yolov8_models/best.pt")
                print("✅ 所有模型載入成功")
            except Exception as custom_error:
                print(f"自定義模型載入失敗: {custom_error}")
                print("將只使用通用模型進行檢測")
                self.custom_model = None
                
        except Exception as e:
            print(f"模型載入錯誤: {e}")
            # 使用備用方案
            self.custom_model = None
            self.general_model = None
        
        # 回收物關鍵詞映射（高準確率版）
        self.recycling_keywords = {
            # 塑膠類（高信心度）
            "bottle": "塑膠瓶",
            "plastic": "塑膠瓶", 
            "container": "塑膠容器",
            "bag": "塑膠袋",
            "cup": "塑膠杯",
            "straw": "吸管",
            "hdpe": "HDPE",    # 高密度聚乙烯
            "pet": "PET",        # 聚對苯二甲酸乙二醇酯
            "pp": "PP",          # 聚丙烯
            "ps": "PS",          # 聚苯乙烯
            "pvc": "PVC",        # 聚氯乙烯
            
            # 金屬類（高信心度）
            "can": "金屬罐",
            "aluminum": "鋁罐", 
            "steel": "鐵罐",
            "metal": "金屬",
            "wire": "銅線",
            "scrap": "廢金屬",
            
            # 紙類（高信心度）
            "paper": "紙類",
            "cardboard": "紙箱",
            "newspaper": "報紙",
            "magazine": "雜誌",
            "book": "書籍",
            "box": "紙箱",
            
            # 玻璃類（需要更明確的指示）
            "glass": "玻璃瓶",
            "jar": "玻璃罐",
            "wine": "玻璃瓶",  # 酒瓶通常是玻璃
            "beer": "玻璃瓶",   # 啤酒瓶通常是玻璃
            
            # 電子類（高信心度）
            "phone": "電子廢棄物",
            "laptop": "電子廢棄物", 
            "computer": "電子廢棄物",
            "battery": "廢電池",
            "electronics": "電子廢棄物",
            
            # 其他（高信心度）
            "tire": "廢輪胎",
            "wood": "廢木材",
            "fabric": "廢紡織品",
            "ceramic": "廢陶瓷",
            "oil": "廢機油"
        }
        
        # 高信心度關鍵詞（只匹配這些詞才分類為回收物）
        self.high_confidence_keywords = {
            "bottle", "can", "paper", "glass", "plastic", "metal",
            "cardboard", "newspaper", "book", "phone", "laptop",
            "battery", "tire", "wood", "fabric", "ceramic", "container",
            "box", "jar", "cup", "bag", "wire", "scrap", "wine", "water"
        }
        
        # 性能優化：緩存檢測結果
        cache_config = self.config.get_cache_config()
        self._detection_cache = {}
        self._cache_size = cache_config['detection_cache_size']
        self._cache_counter = 0
        
    def _setup_torch_compatibility(self):
        """設置 PyTorch 2.6 兼容性"""
        try:
            import torch.serialization
            from ultralytics.nn.tasks import DetectionModel
            from torch.nn.modules.container import Sequential
            from ultralytics.nn.modules.conv import Conv
            from ultralytics.nn.modules.block import C2f, SPPF
            from ultralytics.nn.modules.head import Detect
            from ultralytics.nn.modules.transformer import TransformerBlock
            from torch.nn.modules.conv import Conv2d
            from torch.nn.modules.batchnorm import BatchNorm2d
            from torch.nn.modules.activation import SiLU
            from torch.nn.modules.container import ModuleList
            from ultralytics.nn.modules.block import Bottleneck, DFL
            from torch.nn.modules.pooling import MaxPool2d
            from torch.nn.modules.upsampling import Upsample
            from ultralytics.nn.modules.conv import Concat
            
            # 添加安全的全局類
            torch.serialization.add_safe_globals([
                DetectionModel,
                Sequential,
                Conv,
                Conv2d,
                BatchNorm2d,
                SiLU,
                ModuleList,
                Bottleneck,
                MaxPool2d,
                Upsample,
                Concat,
                DFL,
                C2f,
                SPPF,
                Detect,
                TransformerBlock
            ])
        except Exception as e:
            print(f"PyTorch 兼容性設置警告: {e}")
    
    def _clear_cache_if_needed(self):
        """根據配置清理緩存"""
        cache_config = self.config.get_cache_config()
        self._cache_counter += 1
        
        if self._cache_counter >= cache_config['clear_interval']:
            self._detection_cache.clear()
            self._cache_counter = 0
            print("🧹 緩存已清理")
    
    @lru_cache(maxsize=1000)
    def classify_as_recycling(self, class_name):
        """將通用類別分類為回收物類別（改進版本）"""
        class_name_lower = class_name.lower()
        
        # 直接映射常見的檢測結果
        direct_mapping = {
            "glass": "玻璃瓶",
            "bottle": "塑膠瓶",
            "can": "金屬罐",
            "box": "紙箱",
            "paper": "紙類",
            "plastic": "塑膠瓶",
            "metal": "金屬",
            "container": "塑膠容器",
            "jar": "玻璃罐",
            "cup": "塑膠杯",
            "bag": "塑膠袋"
        }
        
        # 首先檢查直接映射
        if class_name_lower in direct_mapping:
            return direct_mapping[class_name_lower]
        
        # 然後檢查是否為高信心度關鍵詞
        for keyword in self.high_confidence_keywords:
            if keyword in class_name_lower:
                # 找到高信心度關鍵詞，返回對應的回收物類型
                return self.recycling_keywords.get(keyword, keyword)
        
        # 進行更寬鬆的匹配
        for keyword, recycling_type in self.recycling_keywords.items():
            if keyword in class_name_lower:
                return recycling_type
        
        # 如果沒有匹配到，檢查是否包含常見的回收物詞彙
        common_recycling_words = ["bottle", "can", "box", "paper", "plastic", "glass", "metal"]
        for word in common_recycling_words:
            if word in class_name_lower:
                return self.recycling_keywords.get(word, word)
        
        return None
    
    def detect_with_custom_model(self, image):
        """使用你的自定義模型檢測（5類）- 優化版"""
        if self.custom_model is None:
            return []
        
        try:
            start_time = time.time()
            
            # 使用性能配置
            model_config = self.config.get_model_config()
            results = self.custom_model(
                image, 
                verbose=model_config['verbose'],
                conf=model_config['conf'],
                iou=model_config['iou'],
                device=model_config['device']
            )
            
            detection_time = time.time() - start_time
            
            detections = []
            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    for box in boxes:
                        bbox = box.xyxy[0].cpu().numpy()
                        confidence = float(box.conf[0])
                        class_id = int(box.cls[0])
                        class_name = result.names[class_id]
                        
                        # 檢查是否為回收物
                        recycling_type = self.classify_as_recycling(class_name)
                        if recycling_type:
                            detections.append({
                                'bbox': bbox.tolist(),
                                'class_name': recycling_type,
                                'confidence': confidence,
                                'source': 'custom_model'
                            })
                        else:
                            detections.append({
                                'bbox': bbox.tolist(),
                                'class_name': class_name,
                                'confidence': confidence,
                                'source': 'custom_model'
                            })
            
            print(f"自定義模型檢測完成，耗時: {detection_time:.3f}秒")
            return detections
            
        except Exception as e:
            print(f"自定義模型檢測錯誤: {e}")
            return []
    
    def detect_with_general_model(self, image):
        """使用通用模型檢測 - 優化版"""
        if self.general_model is None:
            return []
        
        try:
            start_time = time.time()
            
            # 使用較低的信心度閾值以確保檢測到物體，但後續會過濾
            model_config = self.config.get_model_config()
            detection_conf = 0.3  # 降低檢測信心度以確保能檢測到物體
            
            results = self.general_model(
                image, 
                verbose=model_config['verbose'],
                conf=detection_conf,  # 使用較低的信心度進行檢測
                iou=model_config['iou'],
                device=model_config['device']
            )
            
            detection_time = time.time() - start_time
            
            detections = []
            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    for box in boxes:
                        bbox = box.xyxy[0].cpu().numpy()
                        confidence = float(box.conf[0])
                        class_id = int(box.cls[0])
                        class_name = result.names[class_id]
                        
                        # 處理所有檢測到的物體
                        if confidence >= 0.3:  # 降低信心度要求
                            # 檢查是否為回收物
                            recycling_type = self.classify_as_recycling(class_name)
                            if recycling_type:
                                detections.append({
                                    'bbox': bbox.tolist(),
                                    'class_name': recycling_type,
                                    'confidence': confidence,
                                    'source': 'general_model'
                                })
                            else:
                                # 如果沒有分類為回收物，但信心度較高，也記錄下來
                                if confidence >= 0.5:
                                    detections.append({
                                        'bbox': bbox.tolist(),
                                        'class_name': class_name,
                                        'confidence': confidence,
                                        'source': 'general_model'
                                    })
            
            print(f"通用模型檢測完成，耗時: {detection_time:.3f}秒，檢測到 {len(detections)} 個回收物")
            return detections
            
        except Exception as e:
            print(f"通用模型檢測錯誤: {e}")
            return []
    
    def fast_check_overlap(self, bbox1, bbox2, threshold=None):
        """快速重疊檢查（優化版）"""
        if threshold is None:
            threshold = self.config.OVERLAP_THRESHOLD
            
        x1_1, y1_1, x2_1, y2_1 = bbox1
        x1_2, y1_2, x2_2, y2_2 = bbox2
        
        # 快速邊界檢查
        if x2_1 < x1_2 or x2_2 < x1_1 or y2_1 < y1_2 or y2_2 < y1_1:
            return False
        
        # 計算交集
        x1_i = max(x1_1, x1_2)
        y1_i = max(y1_1, y1_2)
        x2_i = min(x2_1, x2_2)
        y2_i = min(y2_1, y2_2)
        
        intersection = (x2_i - x1_i) * (y2_i - y1_i)
        area1 = (x2_1 - x1_1) * (y2_1 - y1_1)
        area2 = (x2_2 - x1_2) * (y2_2 - y1_2)
        union = area1 + area2 - intersection
        
        return intersection / union > threshold
    
    def combine_detections_fast(self, custom_detections, general_detections):
        """快速合併檢測結果（優化版）"""
        combined = custom_detections.copy()
        
        # 創建自定義檢測的邊界框索引
        custom_bboxes = [det['bbox'] for det in custom_detections]
        
        # 快速過濾通用檢測
        for general_detection in general_detections:
            is_duplicate = False
            
            # 只檢查與自定義檢測的重疊
            for custom_bbox in custom_bboxes:
                if self.fast_check_overlap(general_detection['bbox'], custom_bbox):
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                combined.append(general_detection)
        
        return combined
    
    def detect_recycling_objects(self, image):
        """主要檢測函數（高性能版本）"""
        start_time = time.time()
        
        # 檢查緩存
        if self.config.ENABLE_CACHE:
            image_hash = hash(str(image.shape) + str(image.dtype))
            if image_hash in self._detection_cache:
                print("使用緩存結果")
                return self._detection_cache[image_hash]
        
        # 檢測（優化版本）
        custom_detections = []
        general_detections = []
        
        # 優先使用通用模型（更快）
        if self.general_model is not None:
            general_detections = self.detect_with_general_model(image)
            
            # 如果通用模型檢測到足夠的物體，就不使用自定義模型
            if len(general_detections) >= 2:
                final_detections = general_detections
            else:
                # 如果通用模型檢測結果不足，嘗試自定義模型
                if self.custom_model is not None:
                    custom_detections = self.detect_with_custom_model(image)
                    # 合併結果
                    combined_detections = self.combine_detections_fast(custom_detections, general_detections)
                    
                    # 快速去重
                    final_detections = []
                    seen_combinations = set()
                    
                    for detection in combined_detections:
                        # 創建唯一標識符
                        bbox_key = tuple(round(x, 2) for x in detection['bbox'])
                        class_key = detection['class_name']
                        combination = (bbox_key, class_key)
                        
                        if combination not in seen_combinations:
                            seen_combinations.add(combination)
                            final_detections.append(detection)
                else:
                    final_detections = general_detections
        else:
            # 只有自定義模型可用
            if self.custom_model is not None:
                final_detections = self.detect_with_custom_model(image)
            else:
                final_detections = []
        
        # 緩存結果
        if self.config.ENABLE_CACHE and len(self._detection_cache) < self._cache_size:
            self._detection_cache[image_hash] = final_detections
        
        # 清理緩存
        self._clear_cache_if_needed()
        
        total_time = time.time() - start_time
        print(f"總檢測時間: {total_time:.3f}秒")
        
        return final_detections

# 使用範例
if __name__ == "__main__":
    detector = EnhancedRecyclingDetector()
    
    # 測試圖片
    test_image = "test_image.jpg"
    if os.path.exists(test_image):
        image = cv2.imread(test_image)
        detections = detector.detect_recycling_objects(image)
        
        print(f"檢測到 {len(detections)} 個回收物:")
        for detection in detections:
            print(f"- {detection['class_name']} (信心度: {detection['confidence']:.2f})") 