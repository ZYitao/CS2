import pandas as pd
import os

class ItemMapping:
    def __init__(self, file_path='data/item_mapping.xlsx'):
        self.file_path = file_path
        self._ensure_file_exists()
        
    def _ensure_file_exists(self):
        """确保映射文件存在"""
        if not os.path.exists(os.path.dirname(self.file_path)):
            os.makedirs(os.path.dirname(self.file_path))
        
        if not os.path.exists(self.file_path):
            df = pd.DataFrame(columns=[
                'mapping_id',       # 商品类别ID（相同属性的商品共享同一ID）
                'item_name',        # 商品名称
                'goods_type',        # 商品类型
                'item_wear',        # 商品磨损
                'is_stattrak',      # 是否暗金
                'last_used',        # 最后使用时间
                'current_price'     # 当前市场参考价格
            ])
            df.to_excel(self.file_path, index=False)
    
    def get_mapping_id(self, name, type_, wear, is_stattrak):
        """获取或创建商品类别ID"""
        df = pd.read_excel(self.file_path)
        
        # 查找匹配的商品类别
        mask = (
            (df['item_name'] == name) &
            (df['goods_type'] == type_) &
            (df['item_wear'] == wear) &
            (df['is_stattrak'] == is_stattrak)
        )
        matching_items = df[mask]
        
        if not matching_items.empty:
            # 更新最后使用时间
            mapping_id = matching_items.iloc[0]['mapping_id']
            idx = matching_items.index[0]
            df.at[idx, 'last_used'] = pd.Timestamp.now()
            df.to_excel(self.file_path, index=False)
            return mapping_id
        
        # 创建新ID
        new_id = 1 if df.empty else df['mapping_id'].max() + 1
        new_item = pd.DataFrame({
            'mapping_id': [new_id],
            'item_name': [name],
            'goods_type': [type_],
            'item_wear': [wear],
            'is_stattrak': [is_stattrak],
            'last_used': [pd.Timestamp.now()],
            'current_price': [0.0]  # 初始价格设为0
        })
        
        df = pd.concat([df, new_item], ignore_index=True)
        df.to_excel(self.file_path, index=False)
        return new_id
    
    def update_current_price(self, mapping_id, price):
        """更新商品类别的当前市场参考价格"""
        df = pd.read_excel(self.file_path)
        mask = df['mapping_id'] == mapping_id
        if any(mask):
            df.loc[mask, 'current_price'] = price
            df.to_excel(self.file_path, index=False)
    
    def get_item_details(self, mapping_id):
        """获取商品类别详细信息"""
        df = pd.read_excel(self.file_path)
        item = df[df['mapping_id'] == mapping_id]
        if not item.empty:
            return item.iloc[0].to_dict()
        return None
