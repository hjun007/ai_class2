from models import db
from datetime import datetime

class PaperQuiz(db.Model):
    """试卷题目关联表"""
    __tablename__ = 'paper_quizzes'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    paper_id = db.Column(db.Integer, db.ForeignKey('papers.id'), nullable=False, comment='试卷ID')
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id'), nullable=False, comment='题目ID')
    question_order = db.Column(db.Integer, nullable=False, comment='题目顺序')
    score = db.Column(db.Float, default=1.0, comment='题目分值')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    
    # 关联关系
    paper = db.relationship('Paper', backref=db.backref('paper_quizzes', lazy='dynamic'))
    quiz = db.relationship('Quiz', backref=db.backref('paper_quizzes', lazy='dynamic'))
    
    def __repr__(self):
        return f'<PaperQuiz paper_id={self.paper_id} quiz_id={self.quiz_id}>'
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'paper_id': self.paper_id,
            'quiz_id': self.quiz_id,
            'question_order': self.question_order,
            'score': self.score,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @classmethod
    def add_quiz_to_paper(cls, paper_id, quiz_id, question_order, score=1.0):
        """向试卷添加题目"""
        try:
            paper_quiz = cls(
                paper_id=paper_id,
                quiz_id=quiz_id,
                question_order=question_order,
                score=score
            )
            db.session.add(paper_quiz)
            db.session.commit()
            return paper_quiz
        except Exception as e:
            db.session.rollback()
            raise e
    
    @classmethod
    def get_paper_quizzes(cls, paper_id):
        """获取试卷的所有题目"""
        return cls.query.filter_by(paper_id=paper_id).order_by(cls.question_order).all()
    
    @classmethod
    def remove_quiz_from_paper(cls, paper_id, quiz_id):
        """从试卷中移除题目"""
        paper_quiz = cls.query.filter_by(paper_id=paper_id, quiz_id=quiz_id).first()
        if paper_quiz:
            db.session.delete(paper_quiz)
            db.session.commit()
            return True
        return False
    
    @classmethod
    def update_quiz_order(cls, paper_id, quiz_id, new_order):
        """更新题目顺序"""
        paper_quiz = cls.query.filter_by(paper_id=paper_id, quiz_id=quiz_id).first()
        if paper_quiz:
            paper_quiz.question_order = new_order
            db.session.commit()
            return True
        return False 