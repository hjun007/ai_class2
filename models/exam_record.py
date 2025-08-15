from models import db
from datetime import datetime

class ExamRecord(db.Model):
    """考试记录模型"""
    __tablename__ = 'exam_records'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_id = db.Column(db.String(50), nullable=False, comment='学生ID')
    paper_id = db.Column(db.Integer, db.ForeignKey('papers.id'), nullable=False, comment='试卷ID')
    start_time = db.Column(db.DateTime, default=datetime.utcnow, comment='开始答题时间')
    submit_time = db.Column(db.DateTime, nullable=False, comment='提交时间')
    total_questions = db.Column(db.Integer, nullable=False, comment='总题目数')
    answered_questions = db.Column(db.Integer, nullable=False, comment='已答题目数')
    correct_answers = db.Column(db.Integer, nullable=False, comment='正确答案数')
    total_score = db.Column(db.Float, nullable=False, comment='总得分')
    max_score = db.Column(db.Float, nullable=False, comment='满分')
    accuracy_rate = db.Column(db.Float, nullable=False, comment='正确率(%)')
    status = db.Column(db.String(20), default='completed', comment='考试状态: completed, incomplete')
    
    # 关联关系
    paper = db.relationship('Paper', backref=db.backref('exam_records', lazy='dynamic'))
    
    def __repr__(self):
        return f'<ExamRecord student_id={self.student_id} paper_id={self.paper_id}>'
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'student_id': self.student_id,
            'paper_id': self.paper_id,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'submit_time': self.submit_time.isoformat() if self.submit_time else None,
            'total_questions': self.total_questions,
            'answered_questions': self.answered_questions,
            'correct_answers': self.correct_answers,
            'total_score': self.total_score,
            'max_score': self.max_score,
            'accuracy_rate': self.accuracy_rate,
            'status': self.status
        }
    
    @classmethod
    def add_exam_record(cls, student_id, paper_id, total_questions, answered_questions, 
                       correct_answers, total_score, max_score, start_time=None):
        """添加考试记录"""
        try:
            accuracy_rate = (correct_answers / answered_questions * 100) if answered_questions > 0 else 0
            
            exam_record = cls(
                student_id=student_id,
                paper_id=paper_id,
                start_time=start_time or datetime.utcnow(),
                submit_time=datetime.utcnow(),
                total_questions=total_questions,
                answered_questions=answered_questions,
                correct_answers=correct_answers,
                total_score=total_score,
                max_score=max_score,
                accuracy_rate=accuracy_rate,
                status='completed'
            )
            db.session.add(exam_record)
            db.session.commit()
            return exam_record
        except Exception as e:
            db.session.rollback()
            raise e
    
    @classmethod
    def get_student_exam_records(cls, student_id, limit=None):
        """获取学生的考试记录"""
        query = cls.query.filter_by(student_id=student_id).order_by(cls.submit_time.desc())
        if limit:
            query = query.limit(limit)
        return query.all()
    
    @classmethod
    def get_paper_exam_records(cls, paper_id):
        """获取某试卷的所有考试记录"""
        return cls.query.filter_by(paper_id=paper_id).order_by(cls.submit_time.desc()).all()
    
    @classmethod
    def get_exam_record_by_id(cls, record_id):
        """根据ID获取考试记录"""
        return cls.query.get(record_id)
    
    @classmethod
    def get_student_paper_records(cls, student_id, paper_id):
        """获取学生在某份试卷的所有考试记录"""
        return cls.query.filter_by(student_id=student_id, paper_id=paper_id).order_by(cls.submit_time.desc()).all()
    
    @classmethod
    def get_student_exam_count(cls, student_id):
        """获取学生的考试次数"""
        return cls.query.filter_by(student_id=student_id).count()
    
    @classmethod
    def get_student_average_score(cls, student_id):
        """获取学生的平均分"""
        records = cls.query.filter_by(student_id=student_id).all()
        if not records:
            return 0.0
        
        total_score = sum(record.total_score for record in records)
        return total_score / len(records)
    
    @classmethod
    def delete_exam_record(cls, record_id):
        """删除考试记录"""
        record = cls.get_exam_record_by_id(record_id)
        if record:
            db.session.delete(record)
            db.session.commit()
            return True
        return False 