from models import db
from datetime import datetime

class Paper(db.Model):
    """试卷模型"""
    __tablename__ = 'papers'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(200), nullable=False, comment='试卷名称')
    status = db.Column(db.String(20), default='draft', comment='试卷状态：draft-草稿, published-已发布, archived-已归档')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    def __repr__(self):
        return f'<Paper {self.name}>'
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'name': self.name,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def add_paper(cls, name, status='draft'):
        """添加试卷的类方法"""
        try:
            paper = cls(
                name=name,
                status=status
            )
            db.session.add(paper)
            db.session.commit()
            return paper
        except Exception as e:
            db.session.rollback()
            raise e
    
    @classmethod
    def get_all_papers(cls):
        """获取所有试卷"""
        return cls.query.order_by(cls.created_at.desc()).all()
    
    @classmethod
    def get_paper_by_id(cls, paper_id):
        """根据ID获取试卷"""
        return cls.query.get(paper_id)
    
    @classmethod
    def get_papers_by_status(cls, status):
        """根据状态获取试卷"""
        return cls.query.filter_by(status=status).order_by(cls.created_at.desc()).all()
    
    @classmethod
    def update_paper_status(cls, paper_id, new_status):
        """更新试卷状态"""
        paper = cls.get_paper_by_id(paper_id)
        if paper:
            paper.status = new_status
            db.session.commit()
            return True
        return False
    
    @classmethod
    def delete_paper(cls, paper_id):
        """删除试卷"""
        paper = cls.get_paper_by_id(paper_id)
        if paper:
            db.session.delete(paper)
            db.session.commit()
            return True
        return False 