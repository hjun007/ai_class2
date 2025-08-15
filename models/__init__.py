# 模型包初始化文件
from flask_sqlalchemy import SQLAlchemy

# 创建统一的数据库实例
db = SQLAlchemy()

# 导入所有模型
from .paper import Paper
from .quiz import Quiz
from .paper_quiz import PaperQuiz
from .answer import Answer
from .exam_record import ExamRecord
from .tool import Tool 