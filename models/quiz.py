from models import db
from datetime import datetime

class Quiz(db.Model):
    """试题模型"""
    __tablename__ = 'quizzes'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    content = db.Column(db.Text, nullable=False, comment='题目内容')
    answer = db.Column(db.Text, nullable=False, comment='题目答案')
    analysis = db.Column(db.Text, comment='题目分析')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    def __repr__(self):
        return f'<Quiz {self.id}>'
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'content': self.content,
            'answer': self.answer,
            'analysis': self.analysis,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def add_quiz(cls, content, answer, analysis=None):
        """添加题目的类方法"""
        try:
            quiz = cls(
                content=content,
                answer=answer,
                analysis=analysis
            )
            db.session.add(quiz)
            db.session.commit()
            return quiz
        except Exception as e:
            db.session.rollback()
            raise e
    
    @classmethod
    def get_all_quizzes(cls):
        """获取所有题目"""
        return cls.query.order_by(cls.created_at.desc()).all()
    
    @classmethod
    def get_quiz_by_id(cls, quiz_id):
        """根据ID获取题目"""
        return cls.query.get(quiz_id)
    
    @classmethod
    def delete_quiz(cls, quiz_id):
        """删除题目"""
        quiz = cls.get_quiz_by_id(quiz_id)
        if quiz:
            db.session.delete(quiz)
            db.session.commit()
            return True
        return False 