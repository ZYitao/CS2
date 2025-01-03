from PyQt5.QtWidgets import QPushButton, QTableWidgetItem, QMessageBox, QHeaderView, QDialog, QTableWidget
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from datetime import datetime
import pandas as pd
from views.sell_item_dialog import SellItemDialog
from config.goods_types import GOODS_TYPES

class MainController:
    # 定义状态颜色（深色和浅色）
    STATUS_COLORS = {
        0: {  # 冷却期
            'light': QColor(255, 200, 200),  # 浅红色
            'dark': QColor(255, 180, 180)    # 深红色
        },
        1: {  # 持有中
            'light': QColor(200, 255, 200),  # 浅绿色
            'dark': QColor(180, 255, 180)    # 深绿色
        },
        2: {  # 已售出
            'light': QColor(200, 200, 255),  # 浅蓝色
            'dark': QColor(180, 180, 255)    # 深蓝色
        }
    }

    # 定义按钮样式
    BUTTON_STYLES = {
        "出售": """
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 3px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """,
    }

    def __init__(self, model, view):
        self.model = model
        self.view = view
        self.view.controller = self
        # 初始化筛选条件
        self.current_filters = {
            'name': '',
            'goods_type': '全部',
            'sub_type': '全部',  # 添加子类型筛选条件
            'wear': '全部',
            'state': '全部',
            'price_min': 0,
            'price_max': float('inf')
        }
        self._update_tables()

    def add_item(self):
        data = self.view.show_add_dialog()
        if data:
            try:
                self.model.add_item(
                    goods_name=data['goods_name'],
                    goods_type=data['goods_type'],
                    sub_type=data['sub_type'],
                    goods_wear=data['goods_wear'],
                    goods_wear_value=data['goods_wear_value'],
                    is_stattrak=data['is_stattrak'],
                    buy_price=data['buy_price'],
                    buy_time=data['buy_time']
                )
                self.view.show_success('商品添加成功')
                self._update_tables()
            except Exception as e:
                self.view.show_error(f'添加商品失败: {str(e)}')

    def apply_filters(self, goods_type='全部', sub_type='全部', wear='全部', state='全部', price_min=0, price_max=0):
        self.current_filters = {
            'goods_type': goods_type,
            'sub_type': sub_type,
            'wear': wear,
            'state': state,
            'price_min': price_min,
            'price_max': price_max if price_max > 0 else float('inf')
        }
        self._update_tables()

    def sell_item(self, inventory_id):
        """出售商品"""
        # 检查是否可以出售
        can_sell, message = self.model.can_sell_item(inventory_id)
        if not can_sell:
            self.view.show_error(message)
            return

        # 获取商品详情
        item = self.model.get_item_by_id(inventory_id)
        if item is None:
            self.view.show_error('商品不存在')
            return

        # 显示出售对话框
        dialog = SellItemDialog(item, self.view)
        if dialog.exec_() == QDialog.Accepted:
            sell_data = dialog.get_data()
            success, message = self.model.sell_item(
                inventory_id=inventory_id,
                sell_price=sell_data['sell_price'],
                extra_income=sell_data['extra_income'],
                sell_time=sell_data['sell_time']
            )
            
            if success:
                self.view.show_success(message)
                self._update_tables()
            else:
                self.view.show_error(message)

    def _update_tables(self):
        """更新所有表格数据"""
        self._update_inventory_table()
        self._update_sold_items_table()

    def _update_inventory_table(self):
        """更新库存表格"""
        # 获取并过滤数据
        df = self.model.get_inventory_items()
        if df.empty:
            self.view.inventory_table.setRowCount(0)
            return

        filtered_df = self._apply_filters(df)
        if filtered_df.empty:
            self.view.inventory_table.setRowCount(0)
            return

        # 清空表格
        self.view.inventory_table.setRowCount(0)

        # 记录每个状态的行数，用于交替显示深浅色
        status_row_counts = {0: 0, 1: 0, 2: 0}

        # 填充数据
        for _, item in filtered_df.iterrows():
            row = self.view.inventory_table.rowCount()
            self.view.inventory_table.insertRow(row)
            
            # 设置基本信息
            name = item['goods_name']
            if item['is_stattrak']:
                name += " (StatTrak™)"
            
            # 获取状态和时间信息（拼接显示）
            status_text = self.model.get_item_status_text(item['goods_state'])
            time_info = self.model.get_time_info(item['inventory_id'])
            if time_info:
                status_text = f"{status_text} {time_info}"
            
            # 确定是否使用深色
            state = item['goods_state']
            is_dark_row = (status_row_counts[state] % 2) == 1
            color_key = 'dark' if is_dark_row else 'light'
            status_row_counts[state] += 1
            
            # 创建并设置单元格项
            for col, value in enumerate([
                f" {name} ",  # 添加空格
                f" {item['goods_type']} ",
                f" {item['sub_type']} ",
                f" {item['goods_wear']} ",
                f" {item['goods_wear_value']:.4f} ",
                f" ¥{item['buy_price']:.2f} ",
                f" {pd.to_datetime(item['buy_time']).strftime('%Y-%m-%d %H:%M')} ",
                f" ¥{self.model.get_current_price(item['inventory_id']):.2f} ",
                f" {status_text} "
            ]):
                cell_item = QTableWidgetItem(str(value))
                # 设置背景颜色（深浅交替）
                cell_item.setBackground(self.STATUS_COLORS[state][color_key])
                # 设置文本居中对齐
                cell_item.setTextAlignment(Qt.AlignCenter)
                self.view.inventory_table.setItem(row, col, cell_item)
            
            # 添加操作按钮
            if item['goods_state'] == self.model.STATUS_HOLDING:
                # 创建出售按钮
                sell_btn = QPushButton("出售")
                sell_btn.setStyleSheet(self.BUTTON_STYLES["出售"])
                sell_btn.clicked.connect(lambda checked, id=item['inventory_id']: self.sell_item(id))
                self.view.inventory_table.setCellWidget(row, 9, sell_btn)


        # 调整列宽
        self.view.inventory_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

    def _update_sold_items_table(self):
        """更新已售商品表格"""
        df = self.model.get_sold_items()
        if df.empty:
            self.view.sold_items_table.setRowCount(0)
            return

        # 清空表格
        self.view.sold_items_table.setRowCount(0)

        # 填充数据
        for _, item in df.iterrows():
            row = self.view.sold_items_table.rowCount()
            self.view.sold_items_table.insertRow(row)
            
            # 设置基本信息
            name = item['goods_name']
            if item['is_stattrak']:
                name += " (StatTrak™)"
            
            for col, value in enumerate([
                f" {name} ",  # 添加空格
                f" {item['goods_type']} ",
                f" {item['sub_type']} ",
                f" {item['goods_wear']} ",
                f" {item['goods_wear_value']:.4f} ",
                f" ¥{item['buy_price']:.2f} ",
                f" {pd.to_datetime(item['buy_time']).strftime('%Y-%m-%d %H:%M')} ",
                f" ¥{item['sell_price']:.2f} ",
                f" ¥{item['extra_income']:.2f} ",
                f" {pd.to_datetime(item['sell_time']).strftime('%Y-%m-%d %H:%M')} ",
                f" {item['hold_days']} ",
                f" ¥{item['total_profit']:.2f} "
            ]):
                cell_item = QTableWidgetItem(str(value))
                # 设置文本居中对齐
                cell_item.setTextAlignment(Qt.AlignCenter)
                self.view.sold_items_table.setItem(row, col, cell_item)

        # 调整列宽
        self.view.sold_items_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

    def _apply_filters(self, df):
        """应用筛选条件"""
        filtered_df = df.copy()

        # 应用商品类型筛选
        if self.current_filters['goods_type'] != '全部':
            if self.current_filters['sub_type'] != '全部':
                # 如果选择了具体子类型，直接用子类型筛选
                filtered_df = filtered_df[filtered_df['sub_type'] == self.current_filters['sub_type']]
            else:
                # 如果选择了全部，使用该大类下的所有子类型筛选
                subtypes = GOODS_TYPES[self.current_filters['goods_type']][1:]  # 排除"全部"选项
                filtered_df = filtered_df[filtered_df['sub_type'].isin(subtypes)]

        # 应用磨损等级筛选
        if self.current_filters['wear'] != '全部':
            filtered_df = filtered_df[filtered_df['goods_wear'] == self.current_filters['wear']]

        # 应用状态筛选
        if self.current_filters['state'] != '全部':
            state_map = {
                '冷却期': self.model.STATUS_COOLING,
                '持有中': self.model.STATUS_HOLDING,
                '已售出': self.model.STATUS_SOLD
            }
            filtered_df = filtered_df[filtered_df['goods_state'] == state_map[self.current_filters['state']]]

        # 应用价格范围筛选
        if self.current_filters['price_min'] > 0:
            filtered_df = filtered_df[filtered_df['buy_price'] >= self.current_filters['price_min']]
        if self.current_filters['price_max'] < float('inf'):
            filtered_df = filtered_df[filtered_df['buy_price'] <= self.current_filters['price_max']]

        return filtered_df
