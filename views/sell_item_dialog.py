from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QDoubleSpinBox, QPushButton, QDateTimeEdit, QFrame)
from PyQt5.QtCore import QDateTime, Qt

class SellItemDialog(QDialog):
    def __init__(self, item_data, parent=None):
        super().__init__(parent)
        self.item_data = item_data
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # 商品信息显示
        info_layout = QVBoxLayout()
        
        # 添加商品基本信息
        name = self.item_data["goods_name"]
        if self.item_data.get("is_stattrak", False):
            name += " (StatTrak™)"
            
        info_layout.addWidget(QLabel(f'商品名称: {name}'))
        info_layout.addWidget(QLabel(f'商品类型: {self.item_data["goods_type"]}'))
        info_layout.addWidget(QLabel(f'磨损度: {self.item_data["goods_wear"]} ({self.item_data["goods_wear_value"]:.4f})'))
        info_layout.addWidget(QLabel(f'购买价格: ¥{self.item_data["buy_price"]:.2f}'))
        layout.addLayout(info_layout)

        # 出售价格
        price_layout = QHBoxLayout()
        price_layout.addWidget(QLabel('出售价格:'))
        self.price_input = QDoubleSpinBox()
        self.price_input.setRange(0, 1000000)
        self.price_input.setDecimals(2)
        self.price_input.setValue(self.item_data['now_price'])
        self.price_input.valueChanged.connect(self.calculate_profit)
        price_layout.addWidget(self.price_input)
        layout.addLayout(price_layout)

        # 额外收入（比如回扣）
        extra_layout = QHBoxLayout()
        extra_layout.addWidget(QLabel('额外收入:'))
        self.extra_input = QDoubleSpinBox()
        self.extra_input.setRange(0, 1000000)
        self.extra_input.setDecimals(2)
        self.extra_input.setValue(0)
        self.extra_input.valueChanged.connect(self.calculate_profit)
        extra_layout.addWidget(self.extra_input)
        layout.addLayout(extra_layout)

        # 出售时间
        time_layout = QHBoxLayout()
        time_layout.addWidget(QLabel('出售时间:'))
        self.time_input = QDateTimeEdit(QDateTime.currentDateTime())
        self.time_input.setDisplayFormat('yyyy-MM-dd HH:mm')
        time_layout.addWidget(self.time_input)
        layout.addLayout(time_layout)

        # 预计收益显示框
        profit_layout = QVBoxLayout()
        self.profit_label = QLabel()
        self.profit_label.setAlignment(Qt.AlignLeft)
        profit_layout.addWidget(self.profit_label)
        layout.addLayout(profit_layout)
        
        self.calculate_profit()  # 初始计算收益

        # 按钮
        button_layout = QHBoxLayout()
        ok_button = QPushButton('确认出售')
        ok_button.clicked.connect(self.accept)
        cancel_button = QPushButton('取消')
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)
        self.setWindowTitle('出售商品')
        self.setFixedSize(300, 300)  # 设置固定大小

    def calculate_profit(self):
        """计算预计收益"""
        sell_price = self.price_input.value()
        extra_income = self.extra_input.value()
        
        self.profit_label.setText(
            f'预计收益: ¥{extra_income:.2f}\n'
            f'售价: ¥{sell_price:.2f}\n'
            f'额外收入: ¥{extra_income:.2f}\n'
            f'成本: ¥{self.item_data["buy_price"]:.2f}'
        )

    def get_data(self):
        """获取出售数据"""
        return {
            'sell_price': self.price_input.value(),
            'extra_income': self.extra_input.value(),
            'sell_time': self.time_input.dateTime().toPyDateTime()
        }
