import requests
from bs4 import BeautifulSoup
import json
import time
import re
from datetime import datetime

class RecyclingPriceCalculator:
    def __init__(self):
        # 初始化價格計算器
        
        # 回收物價格資料庫 (可以從網站爬取或手動更新)
        self.price_data = {
            "塑膠瓶": {"price_per_kg": 8.5, "unit": "公斤"},
            "鋁罐": {"price_per_kg": 26.0, "unit": "公斤"},
            "鐵罐": {"price_per_kg": 3.8, "unit": "公斤"},
            "紙類": {"price_per_kg": 2.8, "unit": "公斤"},
            "玻璃瓶": {"price_per_kg": 1.2, "unit": "公斤"},
            "寶特瓶": {"price_per_kg": 8.5, "unit": "公斤"},
            "塑膠袋": {"price_per_kg": 5.5, "unit": "公斤"},
            "紙箱": {"price_per_kg": 2.8, "unit": "公斤"},
            "金屬": {"price_per_kg": 16.0, "unit": "公斤"},
            "電子廢棄物": {"price_per_kg": 55.0, "unit": "公斤"},
            "HDPEM": {"price_per_kg": 12.0, "unit": "公斤"},  # 高密度聚乙烯
            "PET": {"price_per_kg": 8.5, "unit": "公斤"},      # 聚對苯二甲酸乙二醇酯
            "PP": {"price_per_kg": 7.0, "unit": "公斤"},       # 聚丙烯
            "PS": {"price_per_kg": 6.0, "unit": "公斤"},       # 聚苯乙烯
            "PVC": {"price_per_kg": 5.0, "unit": "公斤"}       # 聚氯乙烯
        }
        
        # 物件大小到重量的估算係數 (考慮空心結構，調整為更合理的值)
        self.size_to_weight_factors = {
            "塑膠瓶": 0.02,  # 降低係數，考慮空心結構
            "鋁罐": 0.015,   # 鋁罐很輕
            "鐵罐": 0.04,    # 鐵罐較重
            "紙類": 0.01,    # 紙類很輕
            "玻璃瓶": 0.08,  # 玻璃瓶較重
            "寶特瓶": 0.02,  # 塑膠瓶
            "塑膠袋": 0.005, # 塑膠袋很輕
            "紙箱": 0.015,   # 紙箱較輕
            "金屬": 0.06,    # 金屬較重
            "電子廢棄物": 0.1, # 電子廢棄物較重
            "HDPEM": 0.025,  # 高密度聚乙烯
            "PET": 0.02,     # 聚對苯二甲酸乙二醇酯
            "PP": 0.02,      # 聚丙烯
            "PS": 0.02,      # 聚苯乙烯
            "PVC": 0.03      # 聚氯乙烯
        }
        
        # 類別名稱映射 (模型檢測的類別名稱 -> 價格資料庫中的名稱) - 改進版
        self.class_mapping = {
            # 自定義模型類別
            "AluCan": "鋁罐",
            "PlasticBottle": "塑膠瓶",
            "IronCan": "鐵罐",
            "Paper": "紙類",
            "GlassBottle": "玻璃瓶",
            
            # 通用模型檢測到的類別
            "plastic": "塑膠瓶",
            "bottle": "塑膠瓶",
            "can": "金屬罐",
            "glass": "玻璃瓶",
            "paper": "紙類",
            "metal": "金屬",
            
            # 中文類別（直接映射）
            "玻璃瓶": "玻璃瓶",
            "塑膠瓶": "塑膠瓶",
            "鋁罐": "鋁罐",
            "鐵罐": "鐵罐",
            "紙類": "紙類",
            "金屬": "金屬",
            
            # 塑膠類型
            "HDPEM": "HDPEM",
            "PET": "PET",
            "PP": "PP",
            "PS": "PS",
            "PVC": "PVC",
            
            # 其他映射
            "金屬罐": "金屬",
            "寶特瓶": "塑膠瓶",
            "塑膠袋": "塑膠袋",
            "紙箱": "紙箱",
            "電子廢棄物": "電子廢棄物",
            
            # 常見誤判類別的修正映射
            "electronics": "電子廢棄物",
            "electronic": "電子廢棄物",
            "device": "電子廢棄物",
            "phone": "電子廢棄物",
            "laptop": "電子廢棄物",
            "computer": "電子廢棄物",
            "tv": "電子廢棄物",
            "television": "電子廢棄物",
            "monitor": "電子廢棄物",
            "screen": "電子廢棄物",
            "cable": "電子廢棄物",
            "wire": "電子廢棄物",
            "battery": "電子廢棄物",
            "charger": "電子廢棄物",
            "adapter": "電子廢棄物",
            
            # 金屬相關映射
            "steel": "金屬",
            "iron": "金屬",
            "aluminum": "金屬",
            "copper": "金屬",
            "brass": "金屬",
            "bronze": "金屬",
            "tin": "金屬",
            "zinc": "金屬",
            "nickel": "金屬",
            "chrome": "金屬",
            "stainless": "金屬",
            "alloy": "金屬",
            
            # 塑膠相關映射
            "polymer": "塑膠瓶",
            "polyethylene": "塑膠瓶",
            "polypropylene": "塑膠瓶",
            "polystyrene": "塑膠瓶",
            "polyvinyl": "塑膠瓶",
            "nylon": "塑膠瓶",
            "acrylic": "塑膠瓶",
            "resin": "塑膠瓶",
            
            # 玻璃相關映射
            "ceramic": "玻璃瓶",
            "porcelain": "玻璃瓶",
            "crystal": "玻璃瓶",
            "mirror": "玻璃瓶",
            
            # 紙類相關映射
            "cardboard": "紙箱",
            "newspaper": "紙類",
            "magazine": "紙類",
            "book": "紙類",
            "notebook": "紙類",
            "envelope": "紙類",
            "folder": "紙類",
            "box": "紙箱"
        }
        
        # 嘗試載入已儲存的價格資料
        self.load_saved_prices()
    
    def load_saved_prices(self):
        """載入已儲存的價格資料"""
        try:
            # 嘗試從JSON文件載入價格資料
            with open('recycling_prices.json', 'r', encoding='utf-8') as f:
                saved_prices = json.load(f)
                for item, data in saved_prices.items():
                    if item in self.price_data:
                        self.price_data[item]["price_per_kg"] = data["price_per_kg"]
                        self.price_data[item]["source"] = data.get("source", "本地配置")
                        self.price_data[item]["last_updated"] = data.get("date", "未知")
                        
        except Exception as e:
            print(f"載入價格資料時發生錯誤: {e}")
            print("使用預設價格資料")
    
    def scrape_recycling_prices(self):
        """載入回收物價格"""
        try:
            print("🔄 正在載入回收物價格...")
            
            # 嘗試從JSON文件載入價格資料
            with open('recycling_prices.json', 'r', encoding='utf-8') as f:
                new_prices = json.load(f)
                
                if new_prices:
                    # 更新價格資料
                    for item, data in new_prices.items():
                        if item in self.price_data:
                            self.price_data[item]["price_per_kg"] = data["price_per_kg"]
                            self.price_data[item]["source"] = data.get("source", "本地配置")
                            self.price_data[item]["last_updated"] = data.get("date", "未知")
                    
                    print("✅ 價格資料已載入！")
                    return True
                else:
                    print("⚠️ 無法載入價格，使用預設價格")
                    return False
                    
        except Exception as e:
            print(f"載入價格時發生錯誤: {e}")
            return False
    
    def calculate_object_area(self, bbox):
        """計算檢測物件的面積"""
        x1, y1, x2, y2 = bbox
        width = x2 - x1
        height = y2 - y1
        area = width * height
        return area
    
    def estimate_weight(self, object_class, relative_area):
        """根據物件類型和相對面積估算重量 - 改進版"""
        print(f"估算重量 - 物件類型: {object_class}, 相對面積: {relative_area}")
        
        # 定義實心物品（金屬類、電子廢棄物等）
        solid_objects = {"金屬", "鐵罐", "鋁罐", "電子廢棄物", "金屬罐"}
        
        # 定義空心物品（塑膠、玻璃、紙類等）
        hollow_objects = {"塑膠瓶", "玻璃瓶", "紙類", "寶特瓶", "塑膠袋", "紙箱", 
                         "HDPEM", "PET", "PP", "PS", "PVC"}
        
        # 檢查是否為實心物品
        is_solid = object_class in solid_objects
        
        # 獲取基礎係數
        factor = self.size_to_weight_factors.get(object_class, 0.02)
        
        if is_solid:
            # 實心物品使用較高的密度係數
            weight = relative_area * factor * 8  # 實心物品使用更高係數
            weight = max(weight, 0.02)  # 最小重量0.02kg
            print(f"實心物品 - 使用係數: {factor}, 計算重量: {weight:.3f}kg")
            return weight
        elif object_class in hollow_objects:
            # 空心物品使用較低的密度係數
            weight = relative_area * factor * 1.5  # 空心物品使用較低係數
            weight = max(weight, 0.005)  # 最小重量0.005kg
            print(f"空心物品 - 使用係數: {factor}, 計算重量: {weight:.3f}kg")
            return weight
        else:
            # 未知物品使用預設係數
            weight = relative_area * factor * 2
            weight = max(weight, 0.005)
            print(f"未知物品 - 使用係數: {factor}, 計算重量: {weight:.3f}kg")
            return weight
    
    def calculate_price(self, object_class, relative_area):
        """計算回收物價格"""
        print(f"計算價格 - 物件類型: {object_class}, 相對面積: {relative_area}")
        
        # 映射類別名稱
        mapped_class = self.map_class_name(object_class)
        
        if mapped_class not in self.price_data:
            print(f"未找到 {mapped_class} 的價格資料")
            return {"price": 0, "weight": 0, "unit_price": 0}
        
        # 估算重量
        weight = self.estimate_weight(mapped_class, relative_area)
        
        # 計算價格
        unit_price = self.price_data[mapped_class]["price_per_kg"]
        total_price = weight * unit_price
        
        print(f"單價: {unit_price}, 總價: {total_price:.2f}")
        
        return {
            "price": round(total_price, 2),
            "weight": round(weight, 3),
            "unit_price": unit_price,
            "unit": self.price_data[mapped_class]["unit"],
            "source": self.price_data[mapped_class].get("source", "預設"),
            "last_updated": self.price_data[mapped_class].get("last_updated", "未知")
        }
    
    def get_price_info(self, object_class):
        """獲取物件價格資訊"""
        if object_class in self.price_data:
            return self.price_data[object_class]
        return None
    
    def get_price_report(self):
        """獲取價格報告"""
        report = "📊 回收物價格報告\n"
        report += "=" * 50 + "\n"
        
        for item, data in self.price_data.items():
            report += f"{item}: ${data['price_per_kg']:.2f}/{data['unit']}\n"
        
        report += "=" * 50 + "\n"
        report += f"總共 {len(self.price_data)} 種回收物類別\n"
        
        return report
    
    def get_all_categories(self):
        """獲取所有可用的回收物類別"""
        return list(self.price_data.keys())
    
    def get_extended_price_data(self):
        """獲取擴展的價格數據"""
        return self.price_data
    
    def update_prices_from_website(self, website_url):
        """從特定網站更新價格"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(website_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 這裡需要根據實際網站結構來解析價格
            # 這是一個範例，實際需要根據目標網站調整
            price_elements = soup.find_all('div', class_='price')  # 根據實際網站調整
            
            for element in price_elements:
                # 解析價格資料
                pass
            
            return True
        except Exception as e:
            print(f"更新價格時發生錯誤: {e}")
            return False

    def map_class_name(self, detected_class):
        """將檢測到的類別名稱映射到價格資料庫中的名稱（改進版）"""
        if detected_class in self.class_mapping:
            mapped_class = self.class_mapping[detected_class]
            print(f"類別映射: {detected_class} -> {mapped_class}")
            return mapped_class
        else:
            print(f"未找到 {detected_class} 的映射，使用原始名稱")
            return detected_class

# 使用範例
if __name__ == "__main__":
    calculator = RecyclingPriceCalculator()
    
    # 更新價格
    calculator.scrape_recycling_prices()
    
    # 測試計算
    test_objects = [
        {"class": "塑膠瓶", "area": 5000},
        {"class": "鋁罐", "area": 3000},
        {"class": "紙箱", "area": 8000}
    ]
    
    print("\n📊 測試價格計算:")
    for obj in test_objects:
        result = calculator.calculate_price(obj["class"], obj["area"])
        print(f"{obj['class']}: 重量 {result['weight']}kg, 價格 ${result['price']:.2f}")
    
    # 顯示價格報告
    print("\n" + calculator.get_price_report()) 