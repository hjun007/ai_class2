from models import db
from datetime import datetime

class Answer(db.Model):
    """答题记录模型"""
    __tablename__ = 'answers'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_id = db.Column(db.String(50), nullable=False, comment='学生ID')
    paper_id = db.Column(db.Integer, db.ForeignKey('papers.id'), nullable=False, comment='试卷ID')
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id'), nullable=False, comment='题目ID')
    student_answer = db.Column(db.Text, nullable=False, comment='学生答案')
    is_correct = db.Column(db.Boolean, default=False, comment='是否正确')
    score = db.Column(db.Float, default=0.0, comment='得分')
    answered_at = db.Column(db.DateTime, default=datetime.utcnow, comment='答题时间')
    
    # 关联关系
    paper = db.relationship('Paper', backref=db.backref('answers', lazy='dynamic'))
    quiz = db.relationship('Quiz', backref=db.backref('answers', lazy='dynamic'))
    
    def __repr__(self):
        return f'<Answer student_id={self.student_id} paper_id={self.paper_id} quiz_id={self.quiz_id}>'
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'student_id': self.student_id,
            'paper_id': self.paper_id,
            'quiz_id': self.quiz_id,
            'student_answer': self.student_answer,
            'is_correct': self.is_correct,
            'score': self.score,
            'answered_at': self.answered_at.isoformat() if self.answered_at else None
        }
    
    @classmethod
    def add_answer(cls, student_id, paper_id, quiz_id, student_answer, is_correct=False, score=0.0):
        """添加答题记录"""
        try:
            answer = cls(
                student_id=student_id,
                paper_id=paper_id,
                quiz_id=quiz_id,
                student_answer=student_answer,
                is_correct=is_correct,
                score=score
            )
            db.session.add(answer)
            db.session.commit()
            return answer
        except Exception as e:
            db.session.rollback()
            raise e
    
    @classmethod
    def get_student_answers(cls, student_id, paper_id=None):
        """获取学生的答题记录"""
        query = cls.query.filter_by(student_id=student_id)
        if paper_id:
            query = query.filter_by(paper_id=paper_id)
        return query.order_by(cls.answered_at.desc()).all()
    
    @classmethod
    def get_paper_answers(cls, paper_id):
        """获取试卷的所有答题记录"""
        return cls.query.filter_by(paper_id=paper_id).order_by(cls.answered_at.desc()).all()
    
    @classmethod
    def get_quiz_answers(cls, quiz_id):
        """获取题目的所有答题记录"""
        return cls.query.filter_by(quiz_id=quiz_id).order_by(cls.answered_at.desc()).all()
    
    @classmethod
    def get_answer_by_id(cls, answer_id):
        """根据ID获取答题记录"""
        return cls.query.get(answer_id)
    
    @classmethod
    def update_answer(cls, answer_id, student_answer=None, is_correct=None, score=None):
        """更新答题记录"""
        answer = cls.get_answer_by_id(answer_id)
        if answer:
            if student_answer is not None:
                answer.student_answer = student_answer
            if is_correct is not None:
                answer.is_correct = is_correct
            if score is not None:
                answer.score = score
            db.session.commit()
            return True
        return False
    
    @classmethod
    def delete_answer(cls, answer_id):
        """删除答题记录"""
        answer = cls.get_answer_by_id(answer_id)
        if answer:
            db.session.delete(answer)
            db.session.commit()
            return True
        return False
    
    @classmethod
    def get_student_paper_score(cls, student_id, paper_id):
        """获取学生在某份试卷的总分"""
        answers = cls.query.filter_by(student_id=student_id, paper_id=paper_id).all()
        total_score = sum(answer.score for answer in answers)
        return total_score
    
    @classmethod
    def get_paper_statistics(cls, paper_id):
        """获取试卷答题统计"""
        answers = cls.query.filter_by(paper_id=paper_id).all()
        if not answers:
            return {
                'total_answers': 0,
                'correct_answers': 0,
                'accuracy_rate': 0.0,
                'average_score': 0.0
            }
        
        total_answers = len(answers)
        correct_answers = len([a for a in answers if a.is_correct])
        accuracy_rate = (correct_answers / total_answers) * 100 if total_answers > 0 else 0
        average_score = sum(a.score for a in answers) / total_answers if total_answers > 0 else 0
        
        return {
            'total_answers': total_answers,
            'correct_answers': correct_answers,
            'accuracy_rate': round(accuracy_rate, 2),
            'average_score': round(average_score, 2)
        } 