from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QDoubleSpinBox, QPushButton, QMessageBox)

class AdjustInvestmentDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("调整投资额")
        layout = QVBoxLayout()
        
        # 添加输入框
        amount_layout = QHBoxLayout()
        amount_label = QLabel("调整金额:")
        self.amount_input = QDoubleSpinBox()
        self.amount_input.setRange(-1000000, 1000000)  # 设置合理的范围
        self.amount_input.setDecimals(2)  # 设置小数位数
        self.amount_input.setSingleStep(100)  # 设置步进值
        amount_layout.addWidget(amount_label)
        amount_layout.addWidget(self.amount_input)
        
        # 添加说明标签
        hint_label = QLabel("正数表示增加投资，负数表示减少投资")
        hint_label.setStyleSheet("color: gray;")
        
        # 添加按钮
        button_layout = QHBoxLayout()
        ok_button = QPushButton("确定")
        cancel_button = QPushButton("取消")
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        
        # 组装布局
        layout.addLayout(amount_layout)
        layout.addWidget(hint_label)
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
        # 绑定按钮事件
        ok_button.clicked.connect(self.on_ok)
        cancel_button.clicked.connect(self.on_cancel)
    
    def on_ok(self):
        try:
            self.parent.controller.adjust_investment(self.amount_input.value())
            self.accept()
        except ValueError as e:
            QMessageBox.warning(self, "错误", str(e))
    
    def on_cancel(self):
        self.reject()
