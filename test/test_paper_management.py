#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
试卷管理功能测试脚本
"""

from app import app
from models.paper import Paper

def test_paper_management():
    """测试试卷管理功能"""
    with app.app_context():
        print("=== 试卷管理功能测试 ===")
        
        # 1. 创建测试试卷
        print("\n1. 创建测试试卷...")
        test_paper1 = Paper.add_paper("测试试卷1", "draft")
        print(f"   创建试卷: {test_paper1.name} (ID: {test_paper1.id})")
        
        test_paper2 = Paper.add_paper("测试试卷2", "draft")
        print(f"   创建试卷: {test_paper2.name} (ID: {test_paper2.id})")
        
        # 2. 获取所有试卷
        print("\n2. 获取所有试卷...")
        all_papers = Paper.get_all_papers()
        print(f"   总试卷数: {len(all_papers)}")
        for paper in all_papers[:5]:  # 只显示前5个
            print(f"   - {paper.name} (状态: {paper.status})")
        
        # 3. 发布试卷
        print("\n3. 发布试卷...")
        success = Paper.update_paper_status(test_paper1.id, "published")
        print(f"   发布试卷 {test_paper1.name}: {'成功' if success else '失败'}")
        
        # 4. 获取已发布试卷
        print("\n4. 获取已发布试卷...")
        published_papers = Paper.get_papers_by_status("published")
        print(f"   已发布试卷数: {len(published_papers)}")
        for paper in published_papers:
            print(f"   - {paper.name}")
        
        # 5. 获取草稿试卷
        print("\n5. 获取草稿试卷...")
        draft_papers = Paper.get_papers_by_status("draft")
        print(f"   草稿试卷数: {len(draft_papers)}")
        for paper in draft_papers[:3]:  # 只显示前3个
            print(f"   - {paper.name}")
        
        print("\n=== 测试完成 ===")
        print("现在可以访问以下页面测试功能:")
        print("- 试卷管理页面: http://localhost:8080/teacher/paper-management")
        print("- 新增试卷页面: http://localhost:8080/teacher/paper/create")
        print("- 编辑试卷页面: http://localhost:8080/teacher/paper/{paper_id}/edit")

if __name__ == '__main__':
    test_paper_management() 