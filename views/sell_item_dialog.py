from PyQt5.QtWidgets import QDialog
from PyQt5.QtCore import Qt, QDateTime
from PyQt5 import uic
import os

class SellItemDialog(QDialog):
    def __init__(self, item_data, parent=None):
        super().__init__(parent)
        self.item_data = item_data
        
        # 加载UI文件
        ui_file = os.path.join(os.path.dirname(__file__), 'ui/sell_item_dialog.ui')
        uic.loadUi(ui_file, self)
        
        # 初始化界面
        self.setup_ui()
        
        # 连接信号
        self.connect_signals()
        
    def setup_ui(self):
        """初始化界面数据"""
        # 设置商品信息
        name = self.item_data["goods_name"]
        if self.item_data.get("is_stattrak", False):
            name += " (StatTrak™)"
        self.item_name_label.setText(name)
        self.goods_type_label.setText(self.item_data["goods_type"])
        self.wear_label.setText(f'{self.item_data["goods_wear"]} ({self.item_data["goods_wear_value"]:.4f})')
        self.buy_price_label.setText(f"¥{self.item_data['buy_price']:.2f}")
        
        # 设置默认值
        self.sell_price_input.setValue(self.item_data.get('now_price', 0.0))
        self.extra_income_input.setValue(0.0)
        self.sell_time_input.setDateTime(QDateTime.currentDateTime())
        
        # 更新预计收益
        self.update_profit()
        
    def connect_signals(self):
        """连接信号和槽"""
        self.sell_price_input.valueChanged.connect(self.update_profit)
        self.extra_income_input.valueChanged.connect(self.update_profit)
        
    def update_profit(self):
        """更新预计收益"""
        buy_price = self.item_data['buy_price']
        sell_price = self.sell_price_input.value()
        extra_income = self.extra_income_input.value()
        profit = sell_price + extra_income - buy_price
        self.profit_label.setText(
            f'预计收益: ¥{extra_income:.2f}\n'
            f'售价: ¥{sell_price:.2f}\n'
            f'额外收入: ¥{extra_income:.2f}\n'
            f'成本: ¥{buy_price:.2f}'
        )
        
    def get_data(self):
        """获取表单数据"""
        return {
            'sell_price': self.sell_price_input.value(),
            'extra_income': self.extra_income_input.value(),
            'sell_time': self.sell_time_input.dateTime().toPyDateTime()
        }
