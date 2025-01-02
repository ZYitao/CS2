from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QTableWidget, QTableWidgetItem, QTabWidget,
                             QLabel, QLineEdit, QComboBox, QDoubleSpinBox, QMessageBox,
                             QGroupBox, QDialog)
from PyQt5.QtCore import Qt
from PyQt5 import uic
import os
from .add_item_dialog import AddItemDialog
from .adjust_investment_dialog import AdjustInvestmentDialog
from config.item_types import ITEM_TYPES
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
        """设置表格的列和属性"""
        # 设置库存表格
        headers = ["商品ID", "商品名称", "商品类型", "商品磨损",
                  "磨损值", "是否暗金", "购买价格", "购买时间",
                  "当前价格", "商品状态", "操作"]
        self.inventory_table.setColumnCount(len(headers))
        self.inventory_table.setHorizontalHeaderLabels(headers)
        
        # 设置已售商品表格
        sold_headers = ['ID', '商品名称', '类型', '磨损等级', '磨损值',
                       '购买价格', '购买时间', '售出价格', '额外收入',
                       '售出时间', '持有天数', '总收益']
        self.sold_items_table.setColumnCount(len(sold_headers))
        self.sold_items_table.setHorizontalHeaderLabels(sold_headers)
        
        # 设置统计表格
        analytics_headers = ["时间段", "总市值", "总收益", "总销售额",
                           "剩余金额", "商品数量", "已售数量"]
        self.analytics_table.setColumnCount(len(analytics_headers))
        self.analytics_table.setHorizontalHeaderLabels(analytics_headers)
        
        # 设置表格属性
        for table in [self.inventory_table, self.sold_items_table, self.analytics_table]:
            table.setEditTriggers(QTableWidget.NoEditTriggers)
            table.setSelectionBehavior(QTableWidget.SelectRows)
            table.setSelectionMode(QTableWidget.SingleSelection)
            table.horizontalHeader().setStretchLastSection(True)
            table.setAlternatingRowColors(True)
            
    def setup_filters(self):
        """初始化筛选器"""
        # 商品类型筛选
        self.type_filter.addItems(ITEM_TYPES.keys())
        self.subtype_filter.addItems(ITEM_TYPES['全部'])
        
        # 磨损等级筛选
        self.wear_filter.addItems(['全部', '崭新出厂', '略有磨损', '久经沙场', '破损不堪', '战痕累累'])
        
        # 状态筛选
        self.state_combo.addItems(['全部', '冷却期', '持有中', '已售出'])
        
        # 时间段选择
        self.period_combo.addItems(["周", "月", "年"])
        self.period_combo.setCurrentText("月")
        
    def connect_signals(self):
        """连接信号和槽"""
        # 按钮信号
        self.btn_add.clicked.connect(self.on_add_item)
        self.btn_clear_filter.clicked.connect(self.clear_filters)
        self.btn_adjust_investment.clicked.connect(self.show_adjust_investment_dialog)
        
        # 筛选器信号
        self.name_filter.textChanged.connect(self.on_filter_changed)
        self.type_filter.currentTextChanged.connect(self.on_main_type_changed)
        self.subtype_filter.currentTextChanged.connect(self.on_filter_changed)
        self.wear_filter.currentTextChanged.connect(self.on_filter_changed)
        self.state_combo.currentTextChanged.connect(self.on_filter_changed)
        self.price_min.valueChanged.connect(self.on_filter_changed)
        self.price_max.valueChanged.connect(self.on_filter_changed)
        
        # 统计相关信号
        self.period_combo.currentTextChanged.connect(self._on_period_changed)
        
    def on_main_type_changed(self, main_type):
        # 更新子类型下拉框
        self.subtype_filter.clear()
        self.subtype_filter.addItems(ITEM_TYPES[main_type])
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
            main_type = self.type_filter.currentText()
            sub_type = self.subtype_filter.currentText()
            
            # 确保传递正确的子类型
            self.controller.apply_filters(
                name=self.name_filter.text(),
                item_type=main_type,
                subtype=sub_type,  
                wear=self.wear_filter.currentText(),
                state=self.state_combo.currentText(),
                price_min=self.price_min.value(),
                price_max=self.price_max.value()
            )

    def clear_filters(self):
        self.name_filter.clear()
        self.type_filter.setCurrentText('全部')
        self.subtype_filter.clear()
        self.subtype_filter.addItems(ITEM_TYPES['全部'])
        self.wear_filter.setCurrentText('全部')
        self.state_combo.setCurrentText('全部')
        self.price_min.setValue(0)
        self.price_max.setValue(0)
        if self.controller:
            self.controller.apply_filters()

    def show_error(self, message):
        QMessageBox.critical(self, '错误', message)

    def show_success(self, message):
        QMessageBox.information(self, '成功', message)

    def show_adjust_investment_dialog(self):
        """显示调整投资额的对话框"""
        dialog = AdjustInvestmentDialog(self)
        dialog.exec_()

    def _on_period_changed(self, period):
        """当时间段选择改变时触发更新"""
        period_map = {
            "周": "weekly",
            "月": "monthly",
            "年": "yearly"
        }
        if self.controller:
            self.controller.refresh_analytics(period_map[period])
