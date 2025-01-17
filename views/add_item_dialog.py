from PyQt5.QtWidgets import QDialog
from PyQt5.QtCore import Qt, QDateTime
from PyQt5 import uic
import os
from config.goods_types import GOODS_TYPES

class AddItemDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        # 加载UI文件
        ui_file = os.path.join(os.path.dirname(__file__), 'ui/add_item_dialog.ui')
        uic.loadUi(ui_file, self)
        
        # 初始化下拉框
        self.setup_combo_boxes()
        
        # 连接信号
        self.connect_signals()
        
    def setup_combo_boxes(self):
        """初始化下拉框的选项"""
        # 商品类型
        self.type_combo.addItems(list(GOODS_TYPES.keys()))
        
        # 商品子类型
        self.subtype_combo.clear()
        if self.type_combo.currentText() != '全部':
            self.subtype_combo.addItems(GOODS_TYPES[self.type_combo.currentText()][1:])
        
        # 磨损等级
        self.wear_combo.addItems(['崭新出厂', '略有磨损', '久经沙场', '破损不堪', '战痕累累'])
        
        # 设置当前时间
        self.time_input.setDateTime(QDateTime.currentDateTime())
        
    def connect_signals(self):
        """连接信号和槽"""
        self.type_combo.currentTextChanged.connect(self.on_type_changed)
        self.stattrak_checkbox.stateChanged.connect(self.on_stattrak_changed)
        
    def on_stattrak_changed(self, state):
        """当暗金选项改变时更新预览名称"""
        current_name = self.name_input.text()
        if state == Qt.Checked:  # 选中暗金
            if not current_name.endswith('(StatTrak™)'):
                self.name_input.setText(f"{current_name} (StatTrak™)")
        else:  # 取消选中暗金
            if current_name.endswith('(StatTrak™)'):
                self.name_input.setText(current_name.replace(' (StatTrak™)', ''))
                
    def on_type_changed(self, main_type):
        """当主类型改变时更新子类型列表和暗金选项状态"""
        # 更新子类型列表
        self.subtype_combo.clear()
        if main_type != '全部':
            self.subtype_combo.addItems(GOODS_TYPES[main_type][1:])  # 排除"全部"选项
            
        # 更新暗金选项状态
        is_gun = main_type in ['手枪', '匕首', '步枪']
        self.stattrak_checkbox.setEnabled(is_gun)  # 只有枪械可以选择暗金
        if not is_gun:
            self.stattrak_checkbox.setChecked(False)
            
    def get_data(self):
        """获取表单数据"""
        # 构建商品名称：子类型 + StatTrak™（如果选中）
        return {
            'goods_name': self.name_input.text(),
            'goods_type': self.type_combo.currentText(),  
            'sub_type': self.subtype_combo.currentText(),
            'goods_wear': self.wear_combo.currentText(),
            'goods_wear_value': self.wear_value_input.value(),
            'buy_price': self.price_input.value(),
            'buy_time': self.time_input.dateTime().toPyDateTime(),
            'is_stattrak': self.stattrak_checkbox.isChecked()
        }
