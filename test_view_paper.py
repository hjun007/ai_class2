#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试查看试卷详情功能
"""

from app import app
from models.paper import Paper
from models.paper_quiz import PaperQuiz
from models.quiz import Quiz

def test_view_paper():
    """测试查看试卷详情功能"""
    with app.app_context():
        print("=== 测试查看试卷详情功能 ===")
        
        # 获取所有试卷
        papers = Paper.get_all_papers()
        print(f"总共有 {len(papers)} 份试卷")
        
        # 查找有题目的试卷
        for paper in papers:
            paper_quizzes = PaperQuiz.get_paper_quizzes(paper.id)
            if paper_quizzes:
                print(f"\n试卷: {paper.name} (ID: {paper.id})")
                print(f"状态: {paper.status}")
                print(f"题目数量: {len(paper_quizzes)}")
                
                # 显示题目详情
                for i, pq in enumerate(paper_quizzes, 1):
                    quiz = Quiz.get_quiz_by_id(pq.quiz_id)
                    if quiz:
                        print(f"  题目{i}: {quiz.content[:50]}...")
                        print(f"    分值: {pq.score} 分")
                        print(f"    答案: {quiz.answer[:50]}...")
                
                # 计算总分
                total_score = sum(pq.score for pq in paper_quizzes)
                print(f"  总分: {total_score} 分")
                
                print(f"  查看详情URL: http://localhost:8080/teacher/paper/{paper.id}/view")
                break  # 只显示第一个有题目的试卷
        
        print("\n=== 测试完成 ===")
        print("现在可以访问以下页面:")
        print("- 试卷管理页面: http://localhost:8080/teacher/paper-management")
        print("- 查看试卷详情: http://localhost:8080/teacher/paper/{paper_id}/view")

if __name__ == '__main__':
    test_view_paper() 