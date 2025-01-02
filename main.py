import sys
from PyQt5.QtWidgets import QApplication
from models.item_model import ItemModel
from views.main_view import MainView
from controllers.main_controller import MainController

def main():
    app = QApplication(sys.argv)
    
    # 创建 MVC 组件
    model = ItemModel()
    view = MainView()
    controller = MainController(model, view)  # 创建控制器实例
    view.controller = controller  # 设置视图的控制器引用
    
    # 显示主窗口
    view.show()
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
