#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
數據庫管理器 - 使用SQLite存儲反饋和分析數據
"""

import sqlite3
import json
import os
import numpy as np
from datetime import datetime
from typing import List, Dict, Any, Optional

class DatabaseManager:
    def __init__(self, db_path: str = "data/recycling_app.db"):
        """初始化數據庫管理器"""
        self.db_path = db_path
        self.ensure_data_directory()
        self.init_database()
    
    def _serialize_for_json(self, obj):
        """序列化對象為JSON兼容格式"""
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, dict):
            return {key: self._serialize_for_json(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._serialize_for_json(item) for item in obj]
        else:
            return obj
    
    def ensure_data_directory(self):
        """確保數據目錄存在"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
    
    def init_database(self):
        """初始化數據庫表"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 創建用戶反饋表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    feedback_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    detection_results TEXT,
                    user_rating TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 創建檢測歷史表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS detection_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    image_path TEXT,
                    detection_mode TEXT,
                    total_detections INTEGER,
                    detection_results TEXT,
                    total_price REAL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 創建系統設置表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
    
    def save_feedback(self, feedback_type: str, content: str, 
                     detection_results: Optional[Dict] = None, 
                     user_rating: Optional[Dict] = None) -> int:
        """保存用戶反饋"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 序列化檢測結果和用戶評分
            serialized_detection_results = None
            if detection_results:
                serialized_detection_results = json.dumps(self._serialize_for_json(detection_results))
            
            serialized_user_rating = None
            if user_rating:
                serialized_user_rating = json.dumps(self._serialize_for_json(user_rating))
            
            cursor.execute('''
                INSERT INTO user_feedback 
                (timestamp, feedback_type, content, detection_results, user_rating)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                datetime.now().isoformat(),
                feedback_type,
                content,
                serialized_detection_results,
                serialized_user_rating
            ))
            
            feedback_id = cursor.lastrowid
            conn.commit()
            return feedback_id
    
    def get_all_feedback(self) -> List[Dict]:
        """獲取所有反饋"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, timestamp, feedback_type, content, 
                       detection_results, user_rating, created_at
                FROM user_feedback 
                ORDER BY created_at DESC
            ''')
            
            rows = cursor.fetchall()
            feedback_list = []
            
            for row in rows:
                feedback = {
                    'id': row[0],
                    'timestamp': row[1],
                    'type': row[2],
                    'content': row[3],
                    'detection_results': json.loads(row[4]) if row[4] else None,
                    'user_rating': json.loads(row[5]) if row[5] else None,
                    'created_at': row[6]
                }
                feedback_list.append(feedback)
            
            return feedback_list
    
    def save_detection_record(self, detection_mode: str, total_detections: int,
                            detection_results: List[Dict], total_price: float,
                            image_path: Optional[str] = None) -> int:
        """保存檢測記錄"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 序列化檢測結果
            serialized_detection_results = json.dumps(self._serialize_for_json(detection_results))
            
            cursor.execute('''
                INSERT INTO detection_history 
                (timestamp, image_path, detection_mode, total_detections, 
                 detection_results, total_price)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                datetime.now().isoformat(),
                image_path,
                detection_mode,
                total_detections,
                serialized_detection_results,
                total_price
            ))
            
            record_id = cursor.lastrowid
            conn.commit()
            return record_id
    
    def get_detection_history(self, limit: int = 100) -> List[Dict]:
        """獲取檢測歷史"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, timestamp, image_path, detection_mode, 
                       total_detections, detection_results, total_price, created_at
                FROM detection_history 
                ORDER BY created_at DESC 
                LIMIT ?
            ''', (limit,))
            
            rows = cursor.fetchall()
            history_list = []
            
            for row in rows:
                record = {
                    'id': row[0],
                    'timestamp': row[1],
                    'image_path': row[2],
                    'detection_mode': row[3],
                    'total_detections': row[4],
                    'detection_results': json.loads(row[5]) if row[5] else [],
                    'total_price': row[6],
                    'created_at': row[7]
                }
                history_list.append(record)
            
            return history_list
    
    def get_statistics(self) -> Dict[str, Any]:
        """獲取統計數據"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 反饋統計
            cursor.execute('SELECT COUNT(*) FROM user_feedback')
            total_feedback = cursor.fetchone()[0]
            
            cursor.execute('''
                SELECT AVG(CAST(json_extract(user_rating, '$.overall') AS REAL))
                FROM user_feedback 
                WHERE user_rating IS NOT NULL
            ''')
            avg_rating_result = cursor.fetchone()[0]
            avg_rating = round(avg_rating_result, 1) if avg_rating_result else 0
            
            # 檢測統計
            cursor.execute('SELECT COUNT(*) FROM detection_history')
            total_detections = cursor.fetchone()[0]
            
            cursor.execute('SELECT SUM(total_price) FROM detection_history')
            total_value_result = cursor.fetchone()[0]
            total_value = total_value_result if total_value_result else 0
            
            cursor.execute('SELECT AVG(total_detections) FROM detection_history')
            avg_detections_result = cursor.fetchone()[0]
            avg_detections = round(avg_detections_result, 1) if avg_detections_result else 0
            
            # 反饋類型分布
            cursor.execute('''
                SELECT feedback_type, COUNT(*) 
                FROM user_feedback 
                GROUP BY feedback_type
            ''')
            feedback_types = dict(cursor.fetchall())
            
            return {
                'total_feedback': total_feedback,
                'avg_rating': avg_rating,
                'total_detections': total_detections,
                'total_value': total_value,
                'avg_detections': avg_detections,
                'feedback_types': feedback_types
            }
    
    def get_recent_feedback(self, limit: int = 5) -> List[Dict]:
        """獲取最近的反饋"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, timestamp, feedback_type, content, 
                       detection_results, user_rating, created_at
                FROM user_feedback 
                ORDER BY created_at DESC 
                LIMIT ?
            ''', (limit,))
            
            rows = cursor.fetchall()
            feedback_list = []
            
            for row in rows:
                feedback = {
                    'id': row[0],
                    'timestamp': row[1],
                    'type': row[2],
                    'content': row[3],
                    'detection_results': json.loads(row[4]) if row[4] else None,
                    'user_rating': json.loads(row[5]) if row[5] else None,
                    'created_at': row[6]
                }
                feedback_list.append(feedback)
            
            return feedback_list
    
    def backup_json_data(self):
        """備份JSON數據到數據庫（如果存在）"""
        # 備份反饋數據
        feedback_file = "data/user_feedback.json"
        if os.path.exists(feedback_file):
            try:
                with open(feedback_file, 'r', encoding='utf-8') as f:
                    feedback_data = json.load(f)
                
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    for feedback in feedback_data:
                        cursor.execute('''
                            INSERT OR IGNORE INTO user_feedback 
                            (id, timestamp, feedback_type, content, detection_results, user_rating)
                            VALUES (?, ?, ?, ?, ?, ?)
                        ''', (
                            feedback.get('id'),
                            feedback.get('timestamp'),
                            feedback.get('type'),
                            feedback.get('content'),
                            json.dumps(feedback.get('detection_results')),
                            json.dumps(feedback.get('user_rating'))
                        ))
                    conn.commit()
                
                # 重命名原文件為備份
                backup_file = feedback_file + '.backup'
                os.rename(feedback_file, backup_file)
                print(f"✅ 反饋數據已備份到數據庫，原文件重命名為: {backup_file}")
                
            except Exception as e:
                print(f"⚠️ 備份反饋數據時出錯: {e}")
        
        # 備份檢測歷史數據
        history_file = "data/detection_history.json"
        if os.path.exists(history_file):
            try:
                with open(history_file, 'r', encoding='utf-8') as f:
                    history_data = json.load(f)
                
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    for record in history_data:
                        cursor.execute('''
                            INSERT OR IGNORE INTO detection_history 
                            (timestamp, image_path, detection_mode, total_detections, 
                             detection_results, total_price)
                            VALUES (?, ?, ?, ?, ?, ?)
                        ''', (
                            record.get('timestamp'),
                            record.get('image_path'),
                            record.get('detection_mode'),
                            record.get('total_detections'),
                            json.dumps(record.get('detection_results')),
                            record.get('total_price')
                        ))
                    conn.commit()
                
                # 重命名原文件為備份
                backup_file = history_file + '.backup'
                os.rename(history_file, backup_file)
                print(f"✅ 檢測歷史數據已備份到數據庫，原文件重命名為: {backup_file}")
                
            except Exception as e:
                print(f"⚠️ 備份檢測歷史數據時出錯: {e}")

def main():
    """測試數據庫管理器"""
    db_manager = DatabaseManager()
    
    # 備份現有JSON數據
    db_manager.backup_json_data()
    
    # 測試保存反饋
    feedback_id = db_manager.save_feedback(
        feedback_type="測試反饋",
        content="這是一個測試反饋",
        user_rating={"accuracy": 4, "price_accuracy": 5, "overall": 4}
    )
    print(f"✅ 測試反饋已保存，ID: {feedback_id}")
    
    # 測試獲取統計
    stats = db_manager.get_statistics()
    print(f"📊 統計數據: {stats}")

if __name__ == "__main__":
    main() 