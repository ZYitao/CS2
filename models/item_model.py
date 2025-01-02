from datetime import datetime, timedelta
import pandas as pd
import os
from .item_mapping import ItemMapping

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
        self.analytics_sheet = 'analytics'
        self.item_mapping = ItemMapping()  # 初始化商品ID映射
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
                'mapping_id',       # 商品类别ID
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
                'now_price',        # 当前估值
                'goods_state',      # 商品状态（冷却中/持有中）
            ]
            
            inventory_df = pd.DataFrame(columns=inventory_columns)
            
            # 创建已售商品表（已经售出的商品）
            sold_items_columns = base_columns + [
                'sell_price',       # 售出价格
                'extra_income',     # 额外收入（例如：Steam余额）
                'sell_time',        # 售出时间
                'hold_days',        # 持有天数
                'total_profit',     # 总收益（售出价格 + 额外收入 - 买入价格）
            ]
            
            sold_items_df = pd.DataFrame(columns=sold_items_columns)
            
            # 创建分析表（统计数据）
            analytics_df = pd.DataFrame(columns=[
                'date',                 # 统计日期
                'period_type',          # 统计周期类型（日/周/月/年）
                'total_value',          # 当前总市值（所有持有中商品的当前估值之和）
                'total_profit',         # 总收益（已售商品收益 + 持有商品预期收益）
                'total_sales',          # 总销售额（已售商品的售出价格之和）
                'remaining_balance',    # 剩余余额（当前总市值 - 总投入）
                'item_count',           # 当前持有数量
                'sold_count',           # 已售出数量
                'avg_profit_per_item'   # 平均每件收益
            ])
            
            # 保存所有表格
            with pd.ExcelWriter(self.file_path, engine='openpyxl') as writer:
                inventory_df.to_excel(writer, sheet_name=self.inventory_sheet, index=False)
                sold_items_df.to_excel(writer, sheet_name=self.sold_items_sheet, index=False)
                analytics_df.to_excel(writer, sheet_name=self.analytics_sheet, index=False)

    def _generate_inventory_id(self, buy_time, goods_wear_value):
        """生成商品唯一ID。
        该方法根据购买时间和磨损值生成一个唯一的商品ID，
        格式为'yyyyMMddHHmmss_磨损值'。
        如果购买时间是字符串，则会先转换为datetime对象。
        """ 
        # 将日期转换为yyyyMMddHHmmss格式
        if isinstance(buy_time, str):
            buy_time = pd.to_datetime(buy_time)
        date_str = buy_time.strftime('%Y%m%d%H%M%S')
        # 格式化磨损值为4位小数
        wear_value_str = f"{goods_wear_value:.4f}"
        # 拼接ID
        return f"{date_str}_{wear_value_str}"

    def add_item(self, goods_name, goods_type, goods_wear, goods_wear_value,
                buy_price, buy_time, is_stattrak=False):
        """添加新商品，初始状态为冷却期。
        该方法接收商品的基本信息，并生成唯一ID，
        检查是否已存在相同ID的商品，
        如果不存在，则将新商品添加到库存中。
        """ 
        # 生成商品唯一ID
        inventory_id = self._generate_inventory_id(buy_time, goods_wear_value)
        
        # 获取商品类别ID
        mapping_id = self.item_mapping.get_mapping_id(
            goods_name, goods_type, goods_wear, is_stattrak
        )
        
        df = self._read_inventory()
        
        # 检查是否已存在相同的inventory_id
        if inventory_id in df['inventory_id'].values:
            raise ValueError(f"商品已存在: {inventory_id}")
        
        # 创建新商品记录
        new_item = pd.DataFrame({
            'inventory_id': [inventory_id],
            'mapping_id': [mapping_id],
            'goods_name': [goods_name],
            'goods_type': [goods_type],
            'goods_wear': [goods_wear],
            'goods_wear_value': [goods_wear_value],
            'is_stattrak': [is_stattrak],
            'buy_price': [buy_price],
            'buy_time': [buy_time],
            'now_price': [buy_price],  # 初始当前价格设为购买价格
            'goods_state': [self.STATUS_COOLING],  # 初始状态为冷却期
        })
        
        # 添加到库存
        df = pd.concat([df, new_item], ignore_index=True)
        self._save_inventory(df)
        
        # 更新分析数据
        self._update_analytics()
        
        return True, "添加成功"

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
        current_time = datetime.now()
        
        # 找到所有冷却中的商品
        cooling_items = df[df['goods_state'] == self.STATUS_COOLING]
        
        for idx, item in cooling_items.iterrows():
            buy_time = pd.to_datetime(item['buy_time'])
            cooling_end_time = self.get_cooling_end_time(buy_time)
            
            # 如果已经过了冷却期，更新状态为持有中
            if current_time >= cooling_end_time:
                df.at[idx, 'goods_state'] = self.STATUS_HOLDING
        
        self._save_inventory(df)
        self._update_analytics()

    def get_item_status_text(self, status_code):
        """获取商品状态的文本描述。
        该方法根据状态码返回相应的状态描述，
        包括冷却期、持有中和已售出状态。
        """ 
        status_map = {
            self.STATUS_COOLING: '冷却期',
            self.STATUS_HOLDING: '持有中',
            self.STATUS_SOLD: '已售出'
        }
        return status_map.get(status_code, '未知')

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
        buy_time = pd.to_datetime(buy_time)
        # 获取购买当天的16:00时间点
        cutoff_time = buy_time.replace(hour=16, minute=0, second=0, microsecond=0)
        
        if buy_time <= cutoff_time:
            # 如果在16:00前购买，从购买日期开始算第7天的16:00结束
            end_date = buy_time.date() + pd.Timedelta(days=7)  # 加6天因为当天算第1天
        else:
            # 如果在16:00后购买，从购买日期开始算第8天的16:00结束
            end_date = buy_time.date() + pd.Timedelta(days=8)  # 加7天因为当天算第1天
        
        # 设置结束时间为16:00
        end_time = pd.Timestamp.combine(end_date, pd.Timestamp('16:00:00').time())
        return end_time

    def can_sell_item(self, inventory_id):
        """检查商品是否可以出售。
        该方法根据商品的唯一ID检查其状态，
        只有在持有中状态的商品才能出售。
        """ 
        df = self._read_inventory()
        item = df[df['inventory_id'] == inventory_id]
        if not item.empty:
            return item.iloc[0]['goods_state'] == self.STATUS_HOLDING
        return False

    def get_all_items(self):
        """获取所有商品。
        该方法从库存中读取所有商品，
        并确保购买时间格式正确，
        最后按购买时间排序返回商品列表。
        """ 
        df = self._read_inventory()
        self.check_cooling_items()  # 每次获取数据时检查并更新冷却状态
        # 确保日期格式正确
        df['buy_time'] = pd.to_datetime(df['buy_time'])
        # 按购买时间排序
        return df.sort_values('buy_time', ascending=True)

    def update_item_price(self, inventory_id, new_price):
        """更新商品当前价格。
        该方法根据商品的唯一ID更新其当前价格。
        """ 
        df = self._read_inventory()
        if inventory_id in df['inventory_id'].values:
            idx = df[df['inventory_id'] == inventory_id].index[0]
            df.at[idx, 'now_price'] = new_price
            self._save_inventory(df)
            self._update_analytics()

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
            'mapping_id': item['mapping_id'],
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
        
        # 更新分析数据
        self._update_analytics()
        
        return True, "商品出售成功"

    def get_sold_items(self):
        """获取已售商品列表。
        该方法从已售商品表中读取所有商品信息。
        """ 
        return self._read_sold_items()

    def _read_inventory(self):
        """读取库存数据。
        该方法从库存表中读取所有商品信息。
        """ 
        try:
            return pd.read_excel(self.file_path, sheet_name=self.inventory_sheet)
        except:
            return pd.DataFrame()

    def _read_sold_items(self):
        """读取已售商品数据。
        该方法从已售商品表中读取所有商品信息。
        """ 
        try:
            return pd.read_excel(self.file_path, sheet_name=self.sold_items_sheet)
        except:
            return pd.DataFrame()

    def _read_analytics(self):
        """读取分析数据。
        该方法从分析表中读取所有统计数据。
        """ 
        try:
            return pd.read_excel(self.file_path, sheet_name=self.analytics_sheet, dtype={
                'date': 'datetime64[ns]'  # 明确指定时间列的数据类型
            })
        except:
            return pd.DataFrame()

    def _save_inventory(self, df):
        """保存库存数据到Excel文件"""
        required_columns = [
            'inventory_id', 'goods_name', 'goods_type', 'goods_wear',
            'goods_wear_value', 'is_stattrak', 'buy_price', 'buy_time',
            'now_price', 'goods_state'
        ]
        
        # 确保所有必需的列都存在
        for col in required_columns:
            if col not in df.columns:
                df[col] = None
        
        # 只保存必需的列
        df = df[required_columns]
        
        with pd.ExcelWriter(self.file_path, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
            df.to_excel(writer, sheet_name=self.inventory_sheet, index=False)

    def _save_sold_items(self, df):
        """保存已售商品数据到Excel文件"""
        required_columns = [
            'inventory_id', 'goods_name', 'goods_type', 'goods_wear',
            'goods_wear_value', 'is_stattrak', 'buy_price', 'buy_time',
            'sell_price', 'sell_time', 'extra_income', 'hold_days', 'total_profit'
        ]
        
        # 确保所有必需的列都存在
        for col in required_columns:
            if col not in df.columns:
                df[col] = None
        
        # 只保存必需的列
        df = df[required_columns]
        
        with pd.ExcelWriter(self.file_path, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
            df.to_excel(writer, sheet_name=self.sold_items_sheet, index=False)

    def _save_analytics(self, df):
        """保存分析数据到Excel文件"""
        required_columns = [
            'date', 'period_type', 'total_value', 'total_profit',
            'total_sales', 'remaining_balance', 'item_count', 'sold_count', 'avg_profit_per_item'
        ]
        
        # 确保所有必需的列都存在
        for col in required_columns:
            if col not in df.columns:
                df[col] = None
        
        # 只保存必需的列
        df = df[required_columns]
        
        with pd.ExcelWriter(self.file_path, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
            df.to_excel(writer, sheet_name=self.analytics_sheet, index=False)

    def _calculate_analytics_data(self):
        """计算分析数据"""
        try:
            # 获取当前库存的商品数据
            inventory_df = self._read_inventory()
            # 获取所有商品数据（包括已售出的）
            all_items_df = pd.concat([self._read_inventory(), self._read_sold_items()], ignore_index=True)
            
            # 计算总市值（当前库存中所有商品的当前价格之和）
            total_value = inventory_df['now_price'].sum() if not inventory_df.empty else 0
            
            # 总投资固定为11000
            total_investment = 11000
            
            # 计算总收益（已售出商品的收益之和）
            sold_items = all_items_df[all_items_df['goods_state'] == self.STATUS_SOLD]  # 2表示已售出
            total_profit = sold_items['total_profit'].sum() if not sold_items.empty else 0
            
            # 计算购买商品总价格
            total_buy_price = all_items_df['buy_price'].sum()
            
            # 计算剩余金额（总投资+收益-购买商品价格之和）
            remaining_amount = total_investment + total_profit - total_buy_price
            
            # 计算当前持有数量
            holding_count = len(inventory_df) if not inventory_df.empty else 0
            
            # 计算平均收益
            avg_profit = total_profit / len(sold_items) if not sold_items.empty else 0
            
            return {
                'date': datetime.now().strftime('%Y-%m-%d'),
                'total_value': round(total_value, 2),  # 总市值
                'total_investment': total_investment,  # 总投资
                'total_profit': round(total_profit, 2),  # 总收益
                'remaining_amount': round(remaining_amount, 2),  # 剩余金额
                'holding_count': holding_count,  # 持有数量
                'avg_profit_per_item': round(avg_profit, 2),  # 平均收益
                'period_type': 'daily'  # 时间周期类型
            }
        except Exception as e:
            print(f"计算分析数据时出错: {str(e)}")
            return None

    def _update_analytics(self):
        """更新分析数据"""
        analytics_data = self._calculate_analytics_data()
        if analytics_data is None:
            return
        
        # 读取现有分析数据
        analytics_df = self._read_analytics()
        
        # 如果没有历史数据，直接添加新数据
        if analytics_df.empty:
            analytics_df = pd.DataFrame([analytics_data])
            self._save_analytics(analytics_df)
            return
            
        # 获取最后一条记录
        last_record = analytics_df.iloc[-1]
        
        # 比较新数据与最后一条记录
        # 忽略date字段和period_type字段的比较
        fields_to_compare = ['total_value', 'total_profit', 'remaining_amount', 'holding_count', 'avg_profit_per_item']
        
        needs_update = False
        for field in fields_to_compare:
            # 确保字段存在于last_record中
            if field not in last_record:
                needs_update = True
                break
            try:
                old_value = float(last_record[field]) if pd.notnull(last_record[field]) else 0
                new_value = float(analytics_data[field]) if pd.notnull(analytics_data[field]) else 0
                if abs(old_value - new_value) > 0.01:  # 使用0.01的误差范围
                    needs_update = True
                    break
            except (ValueError, TypeError):
                # 如果转换失败，认为数据有变化
                needs_update = True
                break
                
        # 只有在数据有变化时才更新
        if needs_update:
            analytics_df = pd.concat([analytics_df, pd.DataFrame([analytics_data])], ignore_index=True)
            self._save_analytics(analytics_df)

    def get_analytics(self, period_type='monthly'):
        """获取指定时间周期的分析数据"""
        analytics_df = self._read_analytics()
        
        if period_type == 'weekly':
            analytics_df['date'] = pd.to_datetime(analytics_df['date'])
            analytics_df['period'] = analytics_df['date'].dt.strftime('%Y-W%U')
            grouped = analytics_df.groupby('period').agg({
                'total_value': 'mean',
                'total_profit': 'sum',
                'remaining_amount': 'mean',
                'holding_count': 'mean'
            })
        elif period_type == 'monthly':
            analytics_df['date'] = pd.to_datetime(analytics_df['date'])
            analytics_df['period'] = analytics_df['date'].dt.strftime('%Y-%m')
            grouped = analytics_df.groupby('period').agg({
                'total_value': 'mean',
                'total_profit': 'sum',
                'remaining_amount': 'mean',
                'holding_count': 'mean'
            })
        elif period_type == 'yearly':
            analytics_df['date'] = pd.to_datetime(analytics_df['date'])
            analytics_df['period'] = analytics_df['date'].dt.strftime('%Y')
            grouped = analytics_df.groupby('period').agg({
                'total_value': 'mean',
                'total_profit': 'sum',
                'remaining_amount': 'mean',
                'holding_count': 'mean'
            })
        
        # 重置索引，使period成为一列
        grouped = grouped.reset_index()
        
        # 格式化数值
        grouped['total_value'] = grouped['total_value'].round(2)
        grouped['total_profit'] = grouped['total_profit'].round(2)
        grouped['remaining_amount'] = grouped['remaining_amount'].round(2)
        grouped['holding_count'] = grouped['holding_count'].round(0)
        
        return grouped

    def get_item_details(self, inventory_id):
        """获取商品详细信息"""
        df = self._read_inventory()
        item = df[df['inventory_id'] == inventory_id]
        if not item.empty:
            return item.iloc[0]
        return None
