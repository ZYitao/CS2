from PyQt5.QtWidgets import QDialog
from PyQt5.QtCore import Qt
from PyQt5 import uic
import os

class AdjustInvestmentDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        # 加载UI文件
        ui_file = os.path.join(os.path.dirname(__file__), 'ui/adjust_investment_dialog.ui')
        uic.loadUi(ui_file, self)
        
        # 初始化数据
        self.current_investment = 0.0
        self.adjusted_investment = 0.0
        
        # 连接信号
        self.amount_input.valueChanged.connect(self.on_amount_changed)
        
    def set_current_investment(self, amount):
        """设置当前投资额"""
        self.current_investment = amount
        self.current_investment_label.setText(f"¥{amount:.2f}")
        self.update_adjusted_investment()
        
    def on_amount_changed(self, value):
        """当调整金额改变时更新显示"""
        self.update_adjusted_investment()
        
    def update_adjusted_investment(self):
        """更新调整后的投资额显示"""
        self.adjusted_investment = self.current_investment + self.amount_input.value()
        self.adjusted_investment_label.setText(f"¥{self.adjusted_investment:.2f}")
        
    def get_adjustment_amount(self):
        """获取调整金额"""
        return self.amount_input.value()
