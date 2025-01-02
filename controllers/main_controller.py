from PyQt5.QtWidgets import QPushButton, QTableWidgetItem, QMessageBox, QHeaderView, QDialog, QTableWidget
from PyQt5.QtCore import Qt
from datetime import datetime
import pandas as pd
from views.sell_item_dialog import SellItemDialog
from config.investment_config import InvestmentConfig
from config.item_types import ITEM_TYPES

class MainController:
    def __init__(self, model, view):
        self.model = model
        self.view = view
        self.view.controller = self
        # 初始化筛选条件
        self.current_filters = {
            'name': '',
            'item_type': '全部',
            'subtype': '全部',  # 添加子类型筛选条件
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
                    goods_wear=data['goods_wear'],
                    goods_wear_value=data['goods_wear_value'],
                    buy_price=data['buy_price'],
                    buy_time=data['buy_time']
                )
                self.view.show_success('商品添加成功')
                self._update_data_with_analytics()  # 更新所有数据，包括分析
            except Exception as e:
                self.view.show_error(f'添加商品失败: {str(e)}')

    def apply_filters(self, name='', item_type='全部', subtype='全部', wear='全部', state='全部', price_min=0, price_max=0):
        self.current_filters = {
            'name': name,
            'item_type': item_type,
            'subtype': subtype,
            'wear': wear,
            'state': state,
            'price_min': price_min,
            'price_max': price_max if price_max > 0 else float('inf')
        }
        self._update_tables()  # 只更新表格数据，不更新分析

    def _apply_filters_to_data(self, df):
        if not df.empty:
            # 名称筛选
            if self.current_filters.get('name'):
                df = df[df['goods_name'].str.contains(self.current_filters['name'], case=False, na=False)]
            
            # 类型筛选
            if self.current_filters.get('item_type') != '全部':
                if self.current_filters.get('subtype') == '全部':
                    # 如果子类型为全部，匹配所有大类下的子类型
                    subtypes = ITEM_TYPES.get(self.current_filters['item_type'], [])
                    df = df[df['goods_type'].isin(subtypes)]
                else:
                    # 直接匹配具体的子类型
                    df = df[df['goods_type'] == self.current_filters['subtype']]
            
            # 磨损筛选
            if self.current_filters.get('wear') != '全部':
                df = df[df['goods_wear'] == self.current_filters['wear']]
            
            # 状态筛选
            if self.current_filters.get('state') != '全部':
                state_map = {'冷却期': 0, '持有中': 1, '已售出': 2}
                state_value = state_map.get(self.current_filters['state'])
                if state_value is not None:
                    df = df[df['goods_state'] == state_value]
            
            # 价格范围筛选
            price_min = self.current_filters.get('price_min', 0)
            price_max = self.current_filters.get('price_max', float('inf'))
            df = df[(df['buy_price'] >= price_min) & (df['buy_price'] <= price_max)]
        
        return df

    def _update_tables(self):
        """更新所有表格数据"""
        self._update_inventory_table()
        self._update_sold_items_table()
        self.refresh_statistics()

    def _update_data_with_analytics(self):
        """更新所有表格数据，包括分析表格"""
        self._update_tables()
        self._update_analytics_table()

    def _update_inventory_table(self):
        """更新库存表格数据"""
        try:
            # 获取并筛选数据
            items = self.model.get_all_items()
            filtered_items = self._apply_filters_to_data(items)
            
            # 按照购买时间排序，早购买的在前面
            filtered_items['buy_time'] = pd.to_datetime(filtered_items['buy_time'])
            filtered_items = filtered_items.sort_values('buy_time', ascending=True)
            
            # 清空现有表格
            self.view.inventory_table.clearContents()
            self.view.inventory_table.setRowCount(0)
            
            # 只添加筛选后的数据行
            for index, item in filtered_items.iterrows():
                row = self.view.inventory_table.rowCount()
                self.view.inventory_table.insertRow(row)
                
                # 计算当前收益
                current_profit = item['now_price'] - item['buy_price']
                
                # 设置各列数据
                self._set_table_item(self.view.inventory_table, row, 0, str(item['inventory_id']))
                
                # 处理商品名称，如果是暗金枪械则添加StatTrak™标记
                goods_name = item['goods_name']
                if item['is_stattrak']:
                    goods_name = f"{goods_name}(StatTrak™ )"
                self._set_table_item(self.view.inventory_table, row, 1, goods_name)
                
                self._set_table_item(self.view.inventory_table, row, 2, item['goods_type'])
                self._set_table_item(self.view.inventory_table, row, 3, item['goods_wear'])
                self._set_table_item(self.view.inventory_table, row, 4, f"{item['goods_wear_value']:.4f}")
                self._set_table_item(self.view.inventory_table, row, 5, '是' if item['is_stattrak'] else '否')
                self._set_table_item(self.view.inventory_table, row, 6, f"¥{item['buy_price']:.2f}")
                self._set_table_item(self.view.inventory_table, row, 7, pd.to_datetime(item['buy_time']).strftime('%Y-%m-%d %H:%M'))
                self._set_table_item(self.view.inventory_table, row, 8, f"¥{item['now_price']:.2f}")
                
                # 显示状态文本
                status_text = self.model.get_item_status_text(item['goods_state'])
                if item['goods_state'] == self.model.STATUS_COOLING:
                    # 如果是冷却期，显示剩余时间
                    cooling_end = self.model.get_cooling_end_time(item['buy_time'])
                    remaining_time = cooling_end - datetime.now()
                    if remaining_time.total_seconds() > 0:
                        days = remaining_time.days
                        hours = remaining_time.seconds // 3600
                        minutes = (remaining_time.seconds % 3600) // 60
                        if days > 0:
                            status_text = f"冷却期({days}天{hours}小时)"
                        else:
                            status_text = f"冷却期({hours}小时{minutes}分钟)"
                self._set_table_item(self.view.inventory_table, row, 9, status_text)

                # 添加出售按钮
                if item['goods_state'] == self.model.STATUS_HOLDING:
                    sell_btn = QPushButton('  出售  ')
                    sell_btn.clicked.connect(lambda checked, x=item['inventory_id']: self.sell_item(x))
                    self.view.inventory_table.setCellWidget(row, 10, sell_btn)
                elif item['goods_state'] == self.model.STATUS_COOLING:
                    sell_btn = QPushButton('  冷却中  ')
                    sell_btn.setEnabled(False)
                    self.view.inventory_table.setCellWidget(row, 10, sell_btn)
            
            # 刷新完数据后让表格重新计算列宽
            self.view.inventory_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
            # 操作列保持固定宽度
            self.view.inventory_table.horizontalHeader().setSectionResizeMode(10, QHeaderView.Fixed)
            self.view.inventory_table.setColumnWidth(10, 60)
            
            self.refresh_statistics(filtered_items)
        except Exception as e:
            self.view.show_error(f"更新库存表格时出错: {str(e)}")

    def _update_sold_items_table(self):
        """更新已售商品表格数据"""
        items = self.model.get_sold_items()
        self.view.sold_items_table.setRowCount(len(items))
        
        for row, item in enumerate(items.iterrows()):
            item = item[1]  # 获取Series数据
            
            # 设置单元格数据
            self._set_table_item(self.view.sold_items_table, row, 0, str(item['inventory_id']))
            
            # 处理商品名称，如果是暗金枪械则添加StatTrak™标记
            goods_name = item['goods_name']
            if item['is_stattrak']:
                goods_name = f"StatTrak™ {goods_name}"
            self._set_table_item(self.view.sold_items_table, row, 1, goods_name)
            
            self._set_table_item(self.view.sold_items_table, row, 2, item['goods_type'])
            self._set_table_item(self.view.sold_items_table, row, 3, item['goods_wear'])
            self._set_table_item(self.view.sold_items_table, row, 4, f"{item['goods_wear_value']:.4f}")
            self._set_table_item(self.view.sold_items_table, row, 5, f"¥{item['buy_price']:.2f}")
            self._set_table_item(self.view.sold_items_table, row, 6, str(item['buy_time']))
            self._set_table_item(self.view.sold_items_table, row, 7, f"¥{item['sell_price']:.2f}")
            self._set_table_item(self.view.sold_items_table, row, 8, f"¥{item['extra_income']:.2f}")
            self._set_table_item(self.view.sold_items_table, row, 9, str(item['sell_time']))
            self._set_table_item(self.view.sold_items_table, row, 10, f"{item['hold_days']} 天")
            self._set_table_item(self.view.sold_items_table, row, 11, f"¥{item['total_profit']:.2f}")

    def _update_analytics_table(self):
        """更新统计分析表格"""
        # 获取当前选择的时间段
        period_map = {
            "周": "weekly",
            "月": "monthly",
            "年": "yearly"
        }
        current_period = period_map[self.view.period_combo.currentText()]
        
        # 获取分析数据
        analytics_data = self.model.get_analytics(current_period)
        
        # 更新表格数据
        table = self.view.analytics_table_widget
        table.clearContents()
        table.setRowCount(len(analytics_data))
        
        # 填充数据
        for row, data in analytics_data.iterrows():
            self._set_table_item(table, row, 0, str(data['period']))
            self._set_table_item(table, row, 1, f"¥{data['total_value']:.2f}")
            self._set_table_item(table, row, 2, f"¥{data['total_profit']:.2f}")
            self._set_table_item(table, row, 3, f"¥{data['total_sales']:.2f}")
            self._set_table_item(table, row, 4, f"¥{data['remaining_balance']:.2f}")
            self._set_table_item(table, row, 5, str(int(data['item_count'])))
            self._set_table_item(table, row, 6, str(int(data['sold_count'])))

    def _set_table_item(self, table, row, col, value):
        """设置表格单元格的值"""
        item = QTableWidgetItem(str(value))
        item.setTextAlignment(Qt.AlignCenter)
        table.setItem(row, col, item)

    def adjust_investment(self, amount):
        """调整总投资额"""
        try:
            self.model.adjust_investment(amount)
            self._update_data_with_analytics()  # 更新所有数据，包括分析
            self.view.show_success('投资额调整成功')
        except Exception as e:
            self.view.show_error(f'投资额调整失败: {str(e)}')

    def refresh_statistics(self, filtered_items=None):
        """刷新统计信息"""
        if filtered_items is None:
            items = self.model.get_all_items()
            filtered_items = self._apply_filters_to_data(items)
            
        # 确保filtered_items是DataFrame
        if not isinstance(filtered_items, pd.DataFrame):
            return
            
        # 获取在库商品（状态为冷却或持有）
        active_items = filtered_items[filtered_items['goods_state'].isin([self.model.STATUS_COOLING, self.model.STATUS_HOLDING])]
            
        # 从配置获取总投资额
        total_investment = InvestmentConfig.get_investment()
        
        # 计算已购买商品的总投资（所有在库商品的买入价格总和）
        current_investment = active_items['buy_price'].sum()
        
        # 计算剩余金额（总投资 - 已购买商品总投资）
        remaining_balance = total_investment - current_investment
        
        # 计算当前总市值（在库商品的当前价格总和 + 剩余金额）
        total_value = active_items['now_price'].sum() + remaining_balance
        
        # 计算当前总收益（在库商品的收益总和）
        current_profit = (active_items['now_price'] - active_items['buy_price']).sum()
        
        # 获取已售商品数据
        sold_items = self.model.get_sold_items()
        
        # 计算总销售额（已售商品的售出价格总和）
        total_sales = sold_items['sell_price'].sum() + sold_items['extra_income'].sum() if not sold_items.empty else 0
        sold_profit = sold_items['total_profit'].sum() if not sold_items.empty else 0
        total_profit = current_profit + sold_profit
        
        # 计算商品数量
        item_count = len(active_items)  # 只计算在库商品
        sold_count = len(sold_items)
        
        # 计算平均收益
        avg_profit = total_profit / (item_count + sold_count) if (item_count + sold_count) > 0 else 0
        
        # 更新UI标签
        self.view.total_investment_label.setText(f'总投资: ¥{total_investment:.2f}')
        self.view.total_value_label.setText(f'总市值: ¥{total_value:.2f}')
        self.view.total_profit_label.setText(f'总收益: ¥{total_profit:.2f}')
        self.view.total_sales_label.setText(f'总销售额: ¥{total_sales:.2f}')
        self.view.remaining_balance_label.setText(f'剩余余额: ¥{remaining_balance:.2f}')
        self.view.item_count_label.setText(f'持有数量: {item_count}')
        self.view.sold_count_label.setText(f'已售数量: {sold_count}')
        self.view.avg_profit_label.setText(f'平均收益: ¥{avg_profit:.2f}')

    def refresh_analytics(self, period_type='monthly'):
        """刷新统计分析数据"""
        self._update_analytics_table()

    def sell_item(self, inventory_id):
        """出售商品"""
        try:
            # 获取商品数据
            items = self.model.get_all_items()
            item = items[items['inventory_id'] == inventory_id].iloc[0]
            
            # 检查商品状态
            if item['goods_state'] != self.model.STATUS_HOLDING:
                QMessageBox.warning(self.view, '错误', '只能出售持有中的商品')
                return
            
            # 显示出售对话框
            dialog = SellItemDialog(item.to_dict(), self.view)
            result = dialog.exec_()
            
            if result == QDialog.Accepted:  # 只在用户点击确认时处理出售逻辑
                sell_data = dialog.get_data()
                success, message = self.model.sell_item(
                    inventory_id,
                    sell_data['sell_price'],
                    sell_data['extra_income'],
                    sell_data['sell_time']
                )
                
                if success:
                    QMessageBox.information(self.view, '成功', message)
                    self._update_data_with_analytics()  # 更新所有数据，包括分析
                else:
                    QMessageBox.warning(self.view, '错误', message)
            
        except Exception as e:
            QMessageBox.critical(self.view, '错误', f'出售过程中发生错误：{str(e)}')

    def _connect_signals(self):
        """连接信号和槽"""
        # 连接刷新按钮的点击信号
        self.view.refresh_button.clicked.connect(self.refresh_cooling_status)

    def refresh_cooling_status(self):
        """刷新冷却状态"""
        # 检查并更新冷却状态
        self.model.check_cooling_items()
        # 刷新表格显示
        self._update_tables()
