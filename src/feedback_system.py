#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用戶反饋系統 - 使用數據庫存儲
"""

import streamlit as st
import pandas as pd
from .database_manager import DatabaseManager

# 嘗試導入plotly，如果失敗則使用備用方案
try:
    import plotly.express as px
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    print("⚠️ plotly未安裝，將使用備用圖表方案")

class FeedbackSystem:
    def __init__(self):
        self.db_manager = DatabaseManager()
    
    def save_feedback(self, feedback_type, content, detection_results=None, user_rating=None):
        """保存用戶反饋到數據庫"""
        return self.db_manager.save_feedback(feedback_type, content, detection_results, user_rating)
    
    def create_feedback_form(self, detection_results=None):
        """創建反饋表單"""
        st.subheader("💬 用戶反饋")
        
        with st.expander("提交反饋", expanded=False):
            # 反饋類型
            feedback_type = st.selectbox(
                "反饋類型",
                ["檢測準確性", "價格估算", "界面使用", "功能建議", "錯誤報告", "其他"]
            )
            
            # 反饋內容
            content = st.text_area(
                "反饋內容",
                placeholder="請詳細描述您的反饋或建議...",
                height=100
            )
            
            # 用戶評分
            if detection_results:
                st.subheader("📊 檢測結果評分")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    accuracy_rating = st.slider("檢測準確性", 1, 5, 3, help="1=完全不準確, 5=非常準確")
                
                with col2:
                    price_rating = st.slider("價格估算準確性", 1, 5, 3, help="1=完全不準確, 5=非常準確")
                
                with col3:
                    overall_rating = st.slider("整體滿意度", 1, 5, 3, help="1=非常不滿意, 5=非常滿意")
                
                user_rating = {
                    "accuracy": accuracy_rating,
                    "price_accuracy": price_rating,
                    "overall": overall_rating
                }
            else:
                user_rating = None
            
            # 提交按鈕
            if st.button("提交反饋", type="primary"):
                if content.strip():
                    feedback_id = self.save_feedback(feedback_type, content, detection_results, user_rating)
                    st.success(f"✅ 反饋已提交！反饋ID: {feedback_id}")
                    st.balloons()
                else:
                    st.error("請填寫反饋內容")
    
    def show_feedback_analytics(self):
        """顯示反饋分析"""
        stats = self.db_manager.get_statistics()
        
        if stats['total_feedback'] == 0:
            st.warning("暫無用戶反饋")
            return
        
        st.subheader("📈 反饋分析")
        
        # 統計數據
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("總反饋數", stats['total_feedback'])
        
        with col2:
            st.metric("平均滿意度", f"{stats['avg_rating']}/5")
        
        with col3:
            st.metric("反饋類型數", len(stats['feedback_types']))
        
        # 反饋類型分布
        st.subheader("📊 反饋類型分布")
        if stats['feedback_types']:
            feedback_types = stats['feedback_types']
            
            if PLOTLY_AVAILABLE:
                # 使用plotly創建圖表
                fig_data = pd.DataFrame({
                    "類型": list(feedback_types.keys()),
                    "數量": list(feedback_types.values())
                })
                
                fig = px.pie(fig_data, values='數量', names='類型', title="反饋類型分布")
                st.plotly_chart(fig, use_container_width=True)
            else:
                # 備用方案：使用表格顯示
                st.write("**反饋類型統計:**")
                for feedback_type, count in feedback_types.items():
                    st.write(f"- {feedback_type}: {count} 條")
        
        # 最近反饋
        st.subheader("📋 最近反饋")
        recent_feedback = self.db_manager.get_recent_feedback(5)
        
        for feedback in recent_feedback:
            with st.expander(f"反饋 #{feedback['id']} - {feedback['type']}"):
                st.write(f"**時間**: {feedback['timestamp']}")
                st.write(f"**類型**: {feedback['type']}")
                st.write(f"**內容**: {feedback['content']}")
                
                if feedback.get('user_rating'):
                    rating = feedback['user_rating']
                    st.write(f"**檢測準確性**: {rating.get('accuracy', 'N/A')}/5")
                    st.write(f"**價格準確性**: {rating.get('price_accuracy', 'N/A')}/5")
                    st.write(f"**整體滿意度**: {rating.get('overall', 'N/A')}/5")

def main():
    feedback_system = FeedbackSystem()
    
    st.title("💬 用戶反饋系統")
    
    # 創建反饋表單
    feedback_system.create_feedback_form()
    
    # 顯示反饋分析
    feedback_system.show_feedback_analytics()

if __name__ == "__main__":
    main() 