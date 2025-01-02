# CS2饰品交易系统

基于PyQt5的CS2饰品交易管理系统，采用MVC架构设计，使用Excel作为数据存储。

## 项目结构

```
CS2_1.0/
├── models/             # 数据模型
│   ├── __init__.py
│   └── item_model.py  # 商品数据模型
├── views/              # 视图
│   ├── __init__.py
│   └── main_view.py   # 主界面视图
├── controllers/        # 控制器
│   ├── __init__.py
│   └── main_controller.py  # 主控制器
├── data/              # 数据存储
│   └── items.xlsx     # 商品数据文件
├── main.py            # 程序入口
└── requirements.txt   # 项目依赖
```

## 功能特性

- 商品管理
  - 添加新商品（名称、类型、磨损等）
  - 查看商品列表
  - 更新商品价格
  - 出售商品
- 数据统计
  - 总投资额
  - 总收益
  - 投资回报率
- Excel数据存储
  - 自动创建数据文件
  - 数据持久化

## 系统要求

- Python 3.10+
- PyQt5 5.15.9
- pandas 2.0.3
- numpy 1.23.5
- openpyxl 3.1.2

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用说明

1. 启动程序
```bash
python main.py
```

2. 添加商品
   - 点击"添加商品"按钮
   - 填写商品信息（名称、类型、磨损等级等）
   - 点击确定保存

3. 筛选功能
   - 使用界面上的筛选控件进行筛选
   - 可按名称、类型、磨损等级、状态、价格范围筛选
   - 点击"清除筛选"重置所有筛选条件

4. 出售商品
   - 在商品列表中找到要出售的商品
   - 点击"出售"按钮
   - 输入售出价格
   - 确认出售

## 函数使用说明

```
📁 项目函数结构
├── 📄 models/item_model.py
│   ├── 🔧 __init__(file_path='data/inventory.xlsx')
│   │   └── 初始化库存模型，指定Excel文件路径
│   ├── 📦 add_item()
│   │   └── 添加新商品到库存
│   │       ├── goods_name: 商品名称
│   │       ├── goods_type: 商品类型
│   │       ├── goods_wear: 磨损度类型
│   │       ├── goods_wear_value: 磨损度数值
│   │       ├── buy_price: 购买价格
│   │       ├── buy_time: 购买时间
│   │       └── is_stattrak: 是否为StatTrak™商品
│   ├── 💰 sell_item()
│   │   └── 出售指定商品
│   │       ├── goods_id: 商品唯一标识
│   │       ├── sell_price: 出售价格
│   │       ├── extra_income: 额外收入
│   │       └── sell_time: 出售时间
│   ├── 📋 get_all_items()
│   │   └── 获取所有库存商品
│   └── 📊 get_analytics()
│       └── 获取指定时间周期的分析数据
│           └── period_type: 统计周期类型（默认月度）
│
├── 📄 controllers/main_controller.py
│   ├── 🔧 __init__(model, view)
│   │   └── 初始化主控制器，连接模型和视图
│   ├── 📦 add_item()
│   │   └── 触发添加新商品对话框
│   ├── 💰 sell_item()
│   │   └── 触发出售指定商品的对话框
│   ├── 🔄 refresh_tables()
│   │   └── 刷新表格显示
│   └── 📊 refresh_statistics()
│       └── 刷新统计信息
│
├── 📄 views/main_view.py
│   ├── 🔧 __init__()
│   │   └── 初始化主视图界面
│   ├── 📋 create_inventory_tab()
│   │   └── 创建库存标签页
│   ├── 📊 create_statistics_tab()
│   │   └── 创建统计标签页
│   ├── 📦 show_add_dialog()
│   │   └── 显示添加商品对话框
│   ├── 🔍 on_filter_changed()
│   │   └── 处理筛选条件变更
│   └── ➕ on_add_item_clicked()
│       └── 处理添加商品按钮点击事件
│
├── 📄 views/add_item_dialog.py
│   ├── 🔧 __init__()
│   │   └── 初始化添加商品对话框
│   └── 📋 get_data()
│       └── 获取添加商品对话框中的商品信息
│
├── 📄 views/sell_item_dialog.py
│   ├── 🔧 __init__(item_data, parent=None)
│   │   └── 初始化出售商品对话框
│   └── 📋 get_data()
│       └── 获取出售商品对话框中的出售信息
│
└── 📄 main.py
    └── 🚀 main()
        └── 程序启动入口，初始化MVC组件并启动应用
```

### 图例说明
- 🔧 初始化函数
- 📦 添加/创建函数
- 💰 销售/交易函数
- 📋 获取/展示函数
- 🔍 筛选/过滤函数
- 📊 统计/分析函数
- 🔄 刷新函数
- ➕ 事件处理函数
- 🚀 主入口函数

## 数据存储

所有数据存储在 `items.xlsx` 文件中，包含以下字段：
- id: 商品ID
- name: 商品名称
- type: 商品类型
- wear: 商品磨损等级
- wear_value: 商品磨损值
- buy_price: 购买价格
- buy_time: 购买时间
- current_price: 当前价格
- sell_price: 售出价格
- sell_time: 售出时间
- benefit: 收益
- state: 商品状态（1: 持有中, 2: 已售出）

## 注意事项

1. 首次运行程序时会自动创建 `items.xlsx` 文件
2. 请确保程序运行时 `items.xlsx` 文件没有被其他程序占用
3. 建议定期备份 `items.xlsx` 文件以防数据丢失

## 更新日志

### 2024-12-29
- 初始版本发布
- 实现基本的MVC架构
- 创建主要功能模块：
  - 商品管理模型
  - 主界面视图
  - 控制器逻辑
- 添加Excel数据存储功能
- 实现基础的商品管理和统计功能

### 2024-12-29 13:40
- 添加data目录用于数据存储
- 整合现有Excel数据文件
- 更新ItemModel以适配Excel文件结构
- 优化数据读写操作

### 2024-12-29 13:50
- 新增添加商品对话框
  - 支持选择商品类型
  - 支持选择磨损等级
  - 添加日历选择购买日期功能
  - 添加表单验证
- 优化用户界面交互
- 改进数据录入流程

## 待实现功能
- 商品批量导入
- 价格趋势图表
- 数据备份功能
- 多币种支持

## 贡献指南
1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 许可证
MIT License
