from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QTableWidget, QTableWidgetItem, QTabWidget,
                             QLabel, QLineEdit, QComboBox, QDoubleSpinBox, QMessageBox,
                             QGroupBox, QDialog, QInputDialog, QGridLayout)
from PyQt5.QtCore import Qt
from PyQt5 import uic
import os
from .add_item_dialog import AddItemDialog
from config.goods_types import GOODS_TYPES
from PyQt5.QtWidgets import QHeaderView

class MainView(QMainWindow):
    def __init__(self):
        super().__init__()
        self.controller = None
        self.init_ui()
        
    def init_ui(self):
        # 加载UI文件
        ui_file = os.path.join(os.path.dirname(__file__), 'ui/main_window.ui')
        uic.loadUi(ui_file, self)
        
        # 设置表格属性
        self.setup_tables()
        
        # 初始化筛选器
        self.setup_filters()
        
        # 连接信号
        self.connect_signals()
        
    def setup_tables(self):
        """设置表格属性"""
        # 设置库存表格
        headers = ["商品名称", "商品类型", "具体类型", "磨损等级", 
                    "磨损值", "购买价格", "购买时间", "当前价格", 
                    "商品状态", "操作"]
        self.inventory_table.setColumnCount(len(headers))
        self.inventory_table.setHorizontalHeaderLabels(headers)
        
        # 设置已售商品表格
        sold_headers = ['商品名称', '商品类型', '具体类型', '磨损等级', 
                        '磨损值','购买价格', '购买时间', '售出价格', 
                        '额外收入', '售出时间', '持有天数', '总收益']
        self.sold_items_table.setColumnCount(len(sold_headers))
        self.sold_items_table.setHorizontalHeaderLabels(sold_headers)
        
        # 设置表格属性
        for table in [self.inventory_table, self.sold_items_table]:
            table.setEditTriggers(QTableWidget.NoEditTriggers)
            table.setSelectionBehavior(QTableWidget.SelectRows)
            table.setSelectionMode(QTableWidget.SingleSelection)
            table.horizontalHeader().setStretchLastSection(True)
            table.setAlternatingRowColors(True)
            
    def setup_filters(self):
        """初始化筛选器"""
        # 商品类型筛选
        self.type_filter.addItems(GOODS_TYPES.keys())
        self.subtype_filter.addItems(GOODS_TYPES['全部'])
        
        # 磨损等级筛选
        self.wear_filter.addItems(['全部', '崭新出厂', '略有磨损', '久经沙场', '破损不堪', '战痕累累'])
        
        # 状态筛选
        self.state_combo.addItems(['全部', '冷却期', '持有中', '已售出'])
        
    def connect_signals(self):
        """连接信号槽"""
        # 连接筛选器信号
        self.type_filter.currentTextChanged.connect(self.on_type_filter_changed)
        self.subtype_filter.currentTextChanged.connect(self.on_filter_changed)
        self.wear_filter.currentTextChanged.connect(self.on_filter_changed)
        self.state_combo.currentTextChanged.connect(self.on_filter_changed)
        self.price_min.valueChanged.connect(self.on_filter_changed)
        self.price_max.valueChanged.connect(self.on_filter_changed)
        self.btn_clear_filter.clicked.connect(self.on_clear_filter)
        
        # 连接添加按钮信号
        self.btn_add.clicked.connect(self.on_add_item)
        
        # 连接统计按钮信号
        self.btn_adjust_investment.clicked.connect(self.on_adjust_investment)
        self.btn_add_fee.clicked.connect(self.on_add_fee)
        
    def on_type_filter_changed(self, main_type):
        # 更新子类型下拉框
        self.subtype_filter.clear()
        self.subtype_filter.addItems(GOODS_TYPES[main_type])
        self.subtype_filter.setCurrentText('全部')
        # 触发筛选更新
        self.on_filter_changed()

    def on_add_item(self):
        if self.controller:
            self.controller.add_item()

    def show_add_dialog(self):
        dialog = AddItemDialog(self)
        if dialog.exec_() == AddItemDialog.Accepted:
            return dialog.get_data()
        return None

    def on_filter_changed(self):
        if self.controller:
            # 确保传递正确的子类型
            self.controller.apply_filters(
                goods_type=self.type_filter.currentText(),
                sub_type=self.subtype_filter.currentText(),  
                wear=self.wear_filter.currentText(),
                state=self.state_combo.currentText(),
                price_min=self.price_min.value(),
                price_max=self.price_max.value()
            )

    def on_clear_filter(self):
        self.type_filter.setCurrentText('全部')
        self.subtype_filter.clear()
        self.subtype_filter.addItems(GOODS_TYPES['全部'])
        self.wear_filter.setCurrentText('全部')
        self.state_combo.setCurrentText('全部')
        self.price_min.setValue(0)
        self.price_max.setValue(0)
        if self.controller:
            self.controller.apply_filters()

    def on_adjust_investment(self):
        """调整总投资对话框"""
        amount, ok = QInputDialog.getDouble(
            self, '调整总投资',
            '请输入调整金额（正数增加，负数减少）：',
            0, -1000000, 1000000, 2
        )
        if ok and self.controller:
            self.controller.update_total_investment(amount)

    def on_add_fee(self):
        """添加手续费对话框"""
        amount, ok = QInputDialog.getDouble(
            self, '添加手续费',
            '请输入手续费金额：',
            0, 0, 1000000, 2
        )
        if ok and self.controller:
            self.controller.add_fee(amount)

    def show_error(self, message):
        QMessageBox.critical(self, '错误', message)

    def show_success(self, message):
        QMessageBox.information(self, '成功', message)

    def update_statistics_labels(self, stats):
        """更新统计信息标签"""
        self.lbl_total_investment.setText(f"总投资: {stats['total_investment']:.2f}")
        self.lbl_total_profit.setText(f"总收益: {stats['total_profit']:.2f}")
        self.lbl_remaining_amount.setText(f"剩余金额: {stats['remaining_amount']:.2f}")
        self.lbl_total_fee.setText(f"总手续费: {stats['total_fee']:.2f}")
        self.lbl_purchase_market_value.setText(f"购买市值: {stats['purchase_market_value']:.2f}")
        self.lbl_current_market_value.setText(f"当前市值: {stats['current_market_value']:.2f}")
