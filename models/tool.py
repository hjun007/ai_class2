#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
工具模型
"""

from models import db
from datetime import datetime

class Tool(db.Model):
    """工具模型"""
    __tablename__ = 'tools'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False, comment='工具名称')
    description = db.Column(db.Text, comment='工具描述')
    file_path = db.Column(db.String(255), nullable=False, comment='文件路径')
    file_name = db.Column(db.String(100), nullable=False, comment='原始文件名')
    file_size = db.Column(db.Integer, comment='文件大小(字节)')
    upload_time = db.Column(db.DateTime, default=datetime.utcnow, comment='上传时间')
    status = db.Column(db.String(20), default='offline', comment='状态: online(上线), offline(下线)')
    creator = db.Column(db.String(50), comment='创建者')
    views = db.Column(db.Integer, default=0, comment='浏览次数')
    
    def __repr__(self):
        return f'<Tool {self.name}>'
    
    @classmethod
    def add_tool(cls, name, description, file_path, file_name, file_size, creator):
        """添加工具"""
        tool = cls(
            name=name,
            description=description,
            file_path=file_path,
            file_name=file_name,
            file_size=file_size,
            creator=creator
        )
        db.session.add(tool)
        db.session.commit()
        return tool
    
    @classmethod
    def get_all_tools(cls):
        """获取所有工具"""
        return cls.query.order_by(cls.upload_time.desc()).all()
    
    @classmethod
    def get_online_tools(cls):
        """获取已上线的工具"""
        return cls.query.filter_by(status='online').order_by(cls.upload_time.desc()).all()
    
    @classmethod
    def get_tool_by_id(cls, tool_id):
        """根据ID获取工具"""
        return cls.query.get(tool_id)
    
    def update_status(self, status):
        """更新工具状态"""
        if status in ['online', 'offline']:
            self.status = status
            db.session.commit()
            return True
        return False
    
    def delete_tool(self):
        """删除工具"""
        try:
            db.session.delete(self)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            return False
    
    def increment_views(self):
        """增加浏览次数"""
        self.views += 1
        db.session.commit()
    
    def get_file_size_formatted(self):
        """获取格式化的文件大小"""
        if not self.file_size:
            return "未知"
        
        size = self.file_size
        units = ['B', 'KB', 'MB', 'GB']
        
        for unit in units:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        
        return f"{size:.1f} TB"
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'file_path': self.file_path,
            'file_name': self.file_name,
            'file_size': self.file_size,
            'file_size_formatted': self.get_file_size_formatted(),
            'upload_time': self.upload_time.strftime('%Y-%m-%d %H:%M:%S'),
            'status': self.status,
            'creator': self.creator,
            'views': self.views
        } 