from datetime import datetime, timedelta
import pandas as pd
import os

class ItemModel:
    # 商品状态常量
    STATUS_COOLING = 0    # 冷却期
    STATUS_HOLDING = 1    # 持有中
    STATUS_SOLD = 2       # 已售出

    def __init__(self, file_path='data/inventory.xlsx'):
        """初始化商品模型，设置文件路径和工作表名称。
        该构造函数会初始化商品模型，并确保库存文件存在。
        """ 
        self.file_path = file_path
        self.inventory_sheet = 'inventory'
        self.sold_items_sheet = 'sold_items'
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        """确保文件存在，不存在则创建。
        该方法会检查指定路径下的文件是否存在，
        如果文件或目录不存在，则会创建相应的目录和文件。
        """ 
        if not os.path.exists(os.path.dirname(self.file_path)):
            os.makedirs(os.path.dirname(self.file_path))
        
        if not os.path.exists(self.file_path):
            # 定义基础属性（两个表共用的属性）
            base_columns = [
                'inventory_id',     # 具体商品的唯一ID（购买日期+磨损值）
                'goods_name',       # 商品名称
                'goods_type',       # 商品类型
                'goods_wear',       # 商品磨损等级
                'goods_wear_value', # 具体磨损值
                'is_stattrak',      # 是否暗金
                'buy_price',        # 购买价格
                'buy_time',         # 购买时间
            ]
            
            # 创建库存表（当前持有的商品）
            inventory_columns = base_columns + [
                'goods_state',      # 商品状态（冷却中/持有中）
            ]
            
            # 创建DataFrame
            inventory_df = pd.DataFrame(columns=inventory_columns)
            sold_items_df = pd.DataFrame(columns=base_columns + [
                'sell_price',      # 售出价格
                'sell_time',       # 售出时间
                'extra_income',    # 额外收入
                'hold_days',       # 持有天数
                'total_profit'     # 总收益
            ])
            
            # 保存到Excel
            with pd.ExcelWriter(self.file_path) as writer:
                inventory_df.to_excel(writer, sheet_name=self.inventory_sheet, index=False)
                sold_items_df.to_excel(writer, sheet_name=self.sold_items_sheet, index=False)

    def _generate_inventory_id(self, buy_time, goods_wear_value):
        """生成商品唯一ID。
        该方法根据购买时间和磨损值生成一个唯一的商品ID，
        格式为'yyyyMMddHHmmss_磨损值'。
        如果购买时间是字符串，则会先转换为datetime对象。
        """ 
        if isinstance(buy_time, str):
            buy_time = pd.to_datetime(buy_time)
        return f"{buy_time.strftime('%Y%m%d%H%M%S')}_{goods_wear_value:.4f}"

    def add_item(self, goods_name, goods_type, goods_wear, goods_wear_value,
                buy_price, buy_time, is_stattrak=False):
        """添加新商品，初始状态为冷却期。
        该方法接收商品的基本信息，并生成唯一ID，
        检查是否已存在相同ID的商品，
        如果不存在，则将新商品添加到库存中。
        """ 
        # 生成商品ID
        inventory_id = self._generate_inventory_id(buy_time, goods_wear_value)
        
        # 读取现有数据
        df = self._read_inventory()
        
        # 检查是否已存在
        if inventory_id in df['inventory_id'].values:
            return False, "商品ID已存在"
        
        # 创建新商品记录
        new_item = pd.DataFrame({
            'inventory_id': [inventory_id],
            'goods_name': [goods_name],
            'goods_type': [goods_type],
            'goods_wear': [goods_wear],
            'goods_wear_value': [goods_wear_value],
            'is_stattrak': [is_stattrak],
            'buy_price': [buy_price],
            'buy_time': [buy_time],
            'goods_state': [self.STATUS_COOLING]  # 初始状态为冷却期
        })
        
        # 添加新商品
        df = pd.concat([df, new_item], ignore_index=True)
        self._save_inventory(df)
        
        return True, "商品添加成功"

    def check_cooling_items(self):
        """检查并更新冷却中的商品状态。
        此方法会遍历所有冷却中的商品，
        检查当前时间是否超过冷却期结束时间，
        如果超过，则将商品状态更新为持有中。
        
        冷却期规则：
        1. 如果在当天16:00前购买，冷却期在第7天的16:00结束
        2. 如果在当天16:00后购买，冷却期在第8天的16:00结束
        """ 
        df = self._read_inventory()
        
        # 获取所有冷却中的商品
        cooling_items = df[df['goods_state'] == self.STATUS_COOLING]
        if cooling_items.empty:
            return
        
        current_time = datetime.now()
        updated = False
        
        for idx, item in cooling_items.iterrows():
            buy_time = pd.to_datetime(item['buy_time'])
            cooling_end = self.get_cooling_end_time(buy_time)
            
            if current_time >= cooling_end:
                df.at[idx, 'goods_state'] = self.STATUS_HOLDING
                updated = True
        
        if updated:
            self._save_inventory(df)

    def get_item_status_text(self, status_code):
        """获取商品状态的文本描述。
        该方法根据状态码返回相应的状态描述，
        包括冷却期、持有中和已售出状态。
        """ 
        status_map = {
            self.STATUS_COOLING: "冷却期",
            self.STATUS_HOLDING: "持有中",
            self.STATUS_SOLD: "已售出"
        }
        return status_map.get(status_code, "未知状态")

    def get_cooling_end_time(self, buy_time):
        """
        计算冷却期结束时间
        规则：
        1. 如果在当天16:00前购买，冷却期在第7天的16:00结束
        2. 如果在当天16:00后购买，冷却期在第8天的16:00结束
        
        例如：
        - 1月1日13:00购买 -> 1月7日16:00结束
        - 1月1日14:23购买 -> 1月7日16:00结束
        - 1月1日17:23购买 -> 1月8日16:00结束
        - 1月2日15:00购买 -> 1月8日16:00结束
        """ 
        if isinstance(buy_time, str):
            buy_time = pd.to_datetime(buy_time)
        
        # 获取购买当天16:00的时间点
        cutoff_time = buy_time.replace(hour=16, minute=0, second=0, microsecond=0)
        
        # 确定基础等待天数
        if buy_time <= cutoff_time:
            days_to_add = 7
        else:
            days_to_add = 8
        
        # 计算结束时间（第N天的16:00）
        end_date = (buy_time + timedelta(days=days_to_add)).replace(
            hour=16, minute=0, second=0, microsecond=0
        )
        
        return end_date

    def can_sell_item(self, inventory_id):
        """检查商品是否可以出售。
        该方法根据商品的唯一ID检查其状态，
        只有在持有中状态的商品才能出售。
        """ 
        df = self._read_inventory()
        item_mask = df['inventory_id'] == inventory_id
        
        if not item_mask.any():
            return False, "商品不存在"
            
        item_state = df[item_mask]['goods_state'].iloc[0]
        if item_state != self.STATUS_HOLDING:
            return False, "商品不在持有状态"
            
        return True, "可以出售"

    def sell_item(self, inventory_id, sell_price, extra_income, sell_time):
        """出售商品。
        该方法根据商品的唯一ID找到对应商品，
        检查其状态是否为持有中，
        如果可以出售，则将商品信息复制到已售商品表中，
        并更新原商品状态为已售出。
        """ 
        df = self._read_inventory()
        item_mask = df['inventory_id'] == inventory_id
        
        if not item_mask.any():
            return False, "商品不存在"
        
        item = df[item_mask].iloc[0]
        if item['goods_state'] != self.STATUS_HOLDING:
            return False, "商品状态不正确"
        
        # 计算持有天数和总收益
        buy_time = pd.to_datetime(item['buy_time'])
        sell_time = pd.to_datetime(sell_time)
        hold_days = (sell_time - buy_time).days
        total_profit = sell_price + extra_income - item['buy_price']
        
        # 创建已售商品记录（只保留基础属性和销售相关属性）
        sold_item = pd.Series({
            'inventory_id': item['inventory_id'],
            'goods_name': item['goods_name'],
            'goods_type': item['goods_type'],
            'goods_wear': item['goods_wear'],
            'goods_wear_value': item['goods_wear_value'],
            'is_stattrak': item['is_stattrak'],
            'buy_price': item['buy_price'],
            'buy_time': item['buy_time'],
            'sell_price': sell_price,
            'sell_time': sell_time,
            'extra_income': extra_income,
            'hold_days': hold_days,
            'total_profit': total_profit
        })
        
        # 更新库存中商品状态为已售出
        idx = df[item_mask].index[0]
        df.at[idx, 'goods_state'] = self.STATUS_SOLD
        self._save_inventory(df)
        
        # 添加到已售商品表
        sold_df = self._read_sold_items()
        sold_df = pd.concat([sold_df, pd.DataFrame([sold_item])], ignore_index=True)
        self._save_sold_items(sold_df)
        
        return True, "商品出售成功"

    def get_sold_items(self):
        """获取已售商品列表。
        该方法从已售商品表中读取所有商品信息。
        """ 
        return self._read_sold_items()

    def get_inventory_items(self):
        """获取库存商品列表。
        该方法从库存表中读取所有商品信息。
        """ 
        return self._read_inventory()

    def get_current_price(self, inventory_id):
        """获取商品当前价格
        暂时返回购买价格作为当前价格
        """
        df = self._read_inventory()
        item = df[df['inventory_id'] == inventory_id]
        if not item.empty:
            return item['buy_price'].iloc[0]
        return 0.0

    def get_item_details(self, inventory_id):
        """获取商品详细信息"""
        df = self._read_inventory()
        item_mask = df['inventory_id'] == inventory_id
        
        if not item_mask.any():
            return None
            
        return df[item_mask].iloc[0]

    def _read_inventory(self):
        """读取库存数据。
        该方法从库存表中读取所有商品信息。
        """ 
        try:
            return pd.read_excel(self.file_path, sheet_name=self.inventory_sheet)
        except Exception as e:
            print(f"读取库存数据时出错: {str(e)}")
            return pd.DataFrame()

    def _read_sold_items(self):
        """读取已售商品数据。
        该方法从已售商品表中读取所有商品信息。
        """ 
        try:
            return pd.read_excel(self.file_path, sheet_name=self.sold_items_sheet)
        except Exception as e:
            print(f"读取已售商品数据时出错: {str(e)}")
            return pd.DataFrame()

    def _save_inventory(self, df):
        """保存库存数据到Excel文件"""
        try:
            with pd.ExcelWriter(self.file_path, mode='a', if_sheet_exists='replace') as writer:
                df.to_excel(writer, sheet_name=self.inventory_sheet, index=False)
        except Exception as e:
            print(f"保存库存数据时出错: {str(e)}")

    def _save_sold_items(self, df):
        """保存已售商品数据到Excel文件"""
        try:
            with pd.ExcelWriter(self.file_path, mode='a', if_sheet_exists='replace') as writer:
                df.to_excel(writer, sheet_name=self.sold_items_sheet, index=False)
        except Exception as e:
            print(f"保存已售商品数据时出错: {str(e)}")
