"""投资配置文件"""

class InvestmentConfig:
    """投资配置类，用于管理总投资额度"""
    
    _investment = 11000  # 初始投资额度
    
    @classmethod
    def get_investment(cls):
        """获取当前投资额度"""
        return cls._investment
    
    @classmethod
    def set_investment(cls, amount):
        """设置投资额度"""
        if amount < 0:
            raise ValueError("投资额度不能为负数")
        cls._investment = amount
