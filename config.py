import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class Config:
    """应用配置类"""
    
    # Flask基础配置
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')
    
    # 数据库配置
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///quiz.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # DeepSeek API配置
    DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY', '')
    DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"
    
    # AI聊天配置
    AI_MAX_TOKENS = int(os.getenv('AI_MAX_TOKENS', '1000'))
    AI_TEMPERATURE = float(os.getenv('AI_TEMPERATURE', '0.7'))
    AI_MAX_HISTORY = int(os.getenv('AI_MAX_HISTORY', '20'))  # 最多保存20条历史消息
    
    # 系统提示词
    AI_SYSTEM_PROMPT = """你是一个专业的AI课程助手，名字叫"小智"。你的主要职责是：

1. 帮助学生解答学习问题和课程相关疑问
2. 提供学习方法建议和学习计划指导
3. 解释复杂概念，用简单易懂的语言
4. 鼓励学生积极学习，保持学习热情
5. 当遇到你不确定的问题时，诚实地告知并建议学生咨询老师

请始终保持友好、耐心、专业的态度，用中文回答问题。回答要简洁明了，避免过于冗长。"""

    @classmethod
    def is_ai_enabled(cls):
        """检查AI功能是否已启用（是否配置了API密钥）"""
        return bool(cls.DEEPSEEK_API_KEY and cls.DEEPSEEK_API_KEY != 'your-deepseek-api-key-here') 