import streamlit as st
import cv2
import numpy as np
from PIL import Image
import io
from ultralytics import YOLO
from src.recycling_price_calculator import RecyclingPriceCalculator
from src.enhanced_detection import EnhancedRecyclingDetector
from src.database_manager import DatabaseManager
from src.feedback_system import FeedbackSystem
from src.performance_config import get_performance_config
import time
from functools import lru_cache

# 頁面設定
st.set_page_config(
    page_title="資源回收物分類檢測",
    page_icon="♻️",
    layout="wide"
)

# 獲取性能配置
performance_config = get_performance_config()

# 初始化數據庫和反饋系統
@st.cache_resource
def load_systems():
    """載入系統組件"""
    try:
        # 使用增強檢測系統
        detector = EnhancedRecyclingDetector()
        price_calculator = RecyclingPriceCalculator()
        db_manager = DatabaseManager()
        feedback_system = FeedbackSystem()
        return detector, price_calculator, db_manager, feedback_system
    except Exception as e:
        st.error(f"載入系統時發生錯誤: {e}")
        return None, None, None, None

# 載入系統組件
detector, price_calculator, db_manager, feedback_system = load_systems()

def preprocess_image(image_array):
    """預處理圖片以提高檢測速度"""
    # 獲取預處理配置
    preprocessing_config = performance_config.get_preprocessing_config()
    
    if not preprocessing_config['enable']:
        return image_array
    
    # 調整圖片大小以加快處理速度
    height, width = image_array.shape[:2]
    max_size = preprocessing_config['max_size']
    
    # 如果圖片太大，縮小到合適的尺寸
    if max(height, width) > max_size:
        scale = max_size / max(height, width)
        new_width = int(width * scale)
        new_height = int(height * scale)
        image_array = cv2.resize(image_array, (new_width, new_height))
    
    return image_array

def process_image(image, detection_mode="增強檢測 (推薦)"):
    """處理圖片並檢測回收物 - 優化版"""
    if detector is None:
        return None, []
    
    try:
        start_time = time.time()
        
        # 預處理圖片
        if isinstance(image, Image.Image):
            image_np = np.array(image)
        else:
            image_np = image
        
        # 預處理圖片以提高速度
        processed_image = preprocess_image(image_np)
        
        # 根據檢測模式選擇檢測方法
        if detection_mode == "自定義模型 (5類回收物)":
            # 只使用自定義模型
            detections = detector.detect_with_custom_model(processed_image)
        elif detection_mode == "通用模型":
            # 只使用通用模型
            detections = detector.detect_with_general_model(processed_image)
        else:
            # 增強檢測（推薦）
            detections = detector.detect_recycling_objects(processed_image)
        
        # 處理檢測結果
        results = []
        for detection in detections:
            bbox = detection['bbox']
            original_class_name = detection['class_name']
            confidence = detection['confidence']
            source = detection['source']
            
            # 計算相對面積
            img_height, img_width = processed_image.shape[:2]
            
            x1, y1, x2, y2 = bbox
            width = x2 - x1
            height = y2 - y1
            object_area = width * height
            total_image_area = img_width * img_height
            relative_area = object_area / total_image_area
            
            # 計算價格（使用映射後的類別名稱）
            price_info = price_calculator.calculate_price(original_class_name, relative_area)
            
            # 獲取映射後的類別名稱用於顯示
            mapped_class_name = price_calculator.map_class_name(original_class_name)
            
            results.append({
                'bbox': bbox,
                'original_class_name': original_class_name,  # 原始檢測類別
                'class_name': mapped_class_name,  # 映射後的顯示類別
                'confidence': confidence,
                'source': source,
                'relative_area': relative_area,
                'price_info': price_info
            })
        
        processing_time = time.time() - start_time
        print(f"圖片處理總時間: {processing_time:.3f}秒")
        
        return processed_image, results
    
    except Exception as e:
        st.error(f"處理圖片時發生錯誤: {e}")
        return None, []

def display_price_info(price_info_list):
    """顯示價格資訊"""
    if not price_info_list:
        st.warning("無法估算價格，請檢查檢測結果")
        return
    
    # 計算總價格
    total_price = sum(item['price_info']['price'] for item in price_info_list)
    
    # 顯示總價格
    st.subheader("💰 價格估算")
    st.metric("總估算價值", f"${total_price:.2f}")
    
    # 顯示各項目價格
    st.subheader("📋 詳細價格")
    for i, item in enumerate(price_info_list):
        price_info = item['price_info']
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.write(f"**{item['class_name']}**")
            st.write(f"重量估算: {price_info['weight']:.3f} kg")
        
        with col2:
            st.write(f"單價: ${price_info['unit_price']:.2f}/kg")
        
        with col3:
            st.write(f"**${price_info['price']:.2f}**")
    
    # 保存檢測記錄到數據庫
    if db_manager:
        try:
            db_manager.save_detection_record(
                detection_mode=st.session_state.get('current_detection_mode', '未知'),
                total_detections=len(price_info_list),
                detection_results=price_info_list,
                total_price=total_price
            )
        except Exception as e:
            st.error(f"保存檢測記錄時出錯: {e}")

def show_feedback_section(detection_results=None):
    """顯示反饋區域"""
    if feedback_system:
        st.markdown("---")
        feedback_system.create_feedback_form(detection_results)

def main():
    st.title("♻️ 資源回收物分類檢測系統")
    
    # 初始化會話狀態
    if 'current_detection_mode' not in st.session_state:
        st.session_state.current_detection_mode = "增強檢測 (推薦)"
    
    # 模型說明區域
    with st.expander("📋 模型說明", expanded=False):
        st.markdown("""
        ### 🎯 檢測模型說明
        
        **1. 自定義模型 (5類回收物)**
        - ✅ **專為回收物設計**
        - 支持: 塑膠瓶、玻璃瓶、鋁罐、鐵罐、紙類
        - 檢測準確性高，價格計算準確
        
        **2. 增強檢測 (推薦)**
        - ✅ **結合多種檢測技術**
        - 適用於一般物體檢測
        - 提供全面的檢測結果
        
        **3. 通用模型**
        - ✅ **適用於一般物體檢測**
        - 使用預訓練的通用物體檢測模型
        - 支持多種物體類型
        """)
    
    st.markdown("---")
    
    # 側邊欄
    st.sidebar.header("📋 功能選項")
    
    # 檢測模式選擇
    detection_mode = st.sidebar.selectbox(
        "選擇檢測模式",
        ["自定義模型 (5類回收物)", "增強檢測 (推薦)", "通用模型"]
    )
    
    # 更新會話狀態
    st.session_state.current_detection_mode = detection_mode
    
    # 模型說明
    if detection_mode == "自定義模型 (5類回收物)":
        st.sidebar.success("✅ 專為回收物設計，檢測準確性高")
        st.sidebar.info("支持: 塑膠瓶、玻璃瓶、鋁罐、鐵罐、紙類")
    elif detection_mode == "增強檢測 (推薦)":
        st.sidebar.success("✅ 結合多種檢測技術")
        st.sidebar.info("適用於一般物體檢測")
    elif detection_mode == "通用模型":
        st.sidebar.success("✅ 適用於一般物體檢測")
        st.sidebar.info("支持多種物體類型")
    
    # 信心度閾值
    confidence_threshold = st.sidebar.slider(
        "信心度閾值",
        min_value=0.0,
        max_value=1.0,
        value=0.5,
        step=0.1
    )
    
    # 主要內容區域
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.header("📸 拍照檢測")
        
        # 相機輸入
        camera_input = st.camera_input(
            label="拍攝回收物照片",
            help="點擊相機按鈕拍攝回收物照片"
        )
        
        if camera_input is not None:
            # 轉換為PIL圖片
            image = Image.open(camera_input)
            
            # 顯示原始照片
            st.subheader("📷 原始照片")
            st.image(image, caption="拍攝的照片", use_container_width=True)
            
            # 處理圖片
            with st.spinner("🔄 正在分析回收物..."):
                processed_image, detections = process_image(image, detection_mode)
                
                if processed_image is not None:
                    # 過濾低信心度的檢測結果
                    filtered_detections = [
                        d for d in detections 
                        if d['confidence'] >= confidence_threshold
                    ]
                    
                    # 顯示結果
                    with col2:
                        st.header("📊 檢測結果")
                        
                        if filtered_detections:
                            # 顯示檢測統計
                            st.success(f"檢測到 {len(filtered_detections)} 個回收物")
                            
                            # 根據檢測模式顯示不同的反饋
                            if detection_mode == "自定義模型 (5類回收物)":
                                st.success("✅ 使用專用回收物模型，檢測結果可信度高")
                            elif detection_mode == "通用模型 (實驗性)":
                                st.error("❌ 使用通用模型，檢測結果可能不準確")
                                st.warning("建議使用自定義模型重新檢測")
                            
                            # 顯示檢測詳情
                            for i, detection in enumerate(filtered_detections):
                                with st.expander(f"回收物 {i+1}: {detection['class_name']}"):
                                    st.write(f"**類別:** {detection['class_name']}")
                                    st.write(f"**信心度:** {detection['confidence']:.2f}")
                                    st.write(f"**檢測來源:** {detection['source']}")
                                    st.write(f"**相對面積:** {detection['relative_area']:.3f}")
                                    
                                    # 根據模型顯示不同的建議
                                    if detection_mode == "通用模型 (實驗性)":
                                        st.warning("⚠️ 此結果可能不準確，建議使用自定義模型重新檢測")
                            
                            # 顯示價格資訊
                            display_price_info(filtered_detections)
                            
                            # 顯示反饋區域
                            show_feedback_section(filtered_detections)
                            
                            # 添加回收小提醒
                            st.markdown("---")
                            st.markdown("### 💡 回收小提醒")
                            if detection_mode == "自定義模型 (5類回收物)":
                                st.info("✅ 檢測結果可信度高，請根據結果正確分類回收物！")
                            else:
                                st.warning("⚠️ 檢測結果可能不準確，請謹慎參考並考慮重新檢測。")
                        else:
                            st.warning("未檢測到回收物或信心度過低")
    
    with col2:
        st.header("📁 上傳圖片")
        
        # 文件上傳
        uploaded_file = st.file_uploader(
            "選擇圖片檔案",
            type=['jpg', 'jpeg', 'png', 'bmp'],
            help="上傳回收物圖片進行分類檢測"
        )
        
        if uploaded_file is not None:
            # 讀取圖片
            image = Image.open(uploaded_file)
            
            # 顯示原始圖片
            st.subheader("📷 原始圖片")
            st.image(image, caption="上傳的圖片", use_container_width=True)
            
            # 檢測按鈕
            if st.button("🚀 開始檢測", type="primary"):
                with st.spinner("🔄 正在分析..."):
                    # 處理圖片
                    processed_image, detections = process_image(image, detection_mode)
                    
                    if processed_image is not None:
                        # 過濾低信心度的檢測結果
                        filtered_detections = [
                            d for d in detections 
                            if d['confidence'] >= confidence_threshold
                        ]
                        
                        # 顯示結果
                        if filtered_detections:
                            # 顯示檢測統計
                            st.success(f"檢測到 {len(filtered_detections)} 個回收物")
                            
                            # 根據檢測模式顯示不同的反饋
                            if detection_mode == "自定義模型 (5類回收物)":
                                st.success("✅ 使用專用回收物模型，檢測結果可信度高")
                            elif detection_mode == "增強檢測 (推薦)":
                                st.success("✅ 使用增強檢測模式，提供全面的檢測結果")
                            elif detection_mode == "通用模型":
                                st.success("✅ 使用通用模型，適用於一般物體檢測")
                            
                            # 顯示檢測詳情
                            for i, detection in enumerate(filtered_detections):
                                with st.expander(f"回收物 {i+1}: {detection['class_name']}"):
                                    st.write(f"**類別:** {detection['class_name']}")
                                    st.write(f"**信心度:** {detection['confidence']:.2f}")
                                    st.write(f"**檢測來源:** {detection['source']}")
                                    st.write(f"**相對面積:** {detection['relative_area']:.3f}")
                            
                            # 顯示價格資訊
                            display_price_info(filtered_detections)
                            
                            # 顯示反饋區域
                            show_feedback_section(filtered_detections)
                            
                            # 添加回收小提醒
                            st.markdown("---")
                            st.markdown("### 💡 回收小提醒")
                            st.info("✅ 系統已根據物品特性自動調整重量估算，請根據結果正確分類回收物！")
                        else:
                            st.warning("未檢測到回收物或信心度過低")
    
    # 底部資訊
    st.markdown("---")
    st.markdown("""
    ### 💡 使用說明
    1. **選擇檢測模式**: 
       - **自定義模型 (5類回收物)**: 專為回收物設計，檢測準確性高
       - **增強檢測 (推薦)**: 結合多種檢測技術，適用於一般物體檢測
       - **通用模型**: 適用於一般物體檢測，支持多種物體類型
    2. **拍照檢測**: 使用相機直接拍攝回收物照片
    3. **上傳圖片**: 上傳回收物圖片檔案
    4. **調整信心度**: 過濾低信心度的檢測結果
    5. **查看結果**: 檢測結果和智能價格估算
    6. **提供反饋**: 幫助改進系統準確性
    
    ### 🎯 推薦使用流程
    1. **選擇合適的檢測模式** - 根據需求選擇最佳檢測方法
    2. **拍攝清晰照片** - 確保回收物在照片中清晰可見
    3. **檢查檢測結果** - 確認檢測的類別是否正確
    4. **參考價格估算** - 系統已根據物品特性自動調整重量計算
    5. **提供反饋** - 幫助系統持續改進
    
    ### 🔧 技術特點
    - **多種檢測模式**: 自定義模型、增強檢測、通用模型
    - **智能重量估算**: 金屬物品使用實心計算，其他物品使用空心計算
    - **價格估算**: 基於物件大小和類別計算回收價格
    - **實時檢測**: 快速準確的物體檢測
    - **數據存儲**: 使用SQLite數據庫存儲檢測歷史和用戶反饋
    - **用戶反饋**: 收集用戶反饋以改進系統準確性
    
    ### ⚠️ 重要提醒
    - 重量估算已根據物品特性自動調整（實心/空心）
    - 價格估算基於物件大小和當前回收物價格
    - 實際價格可能因品質、地區、回收商等因素而異
    - 建議聯繫當地回收商獲取準確價格
    - 您的反饋將幫助改進系統準確性
    """)

if __name__ == "__main__":
    main() 