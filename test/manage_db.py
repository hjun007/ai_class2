#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库管理脚本
用于测试试题数据库、试卷数据库和答题记录的增删改查操作
"""

from app import app, db
from models.quiz import Quiz
from models.paper import Paper
from models.paper_quiz import PaperQuiz
from models.answer import Answer

def test_database_operations():
    """测试数据库操作"""
    print("开始测试试题、试卷和答题记录数据库操作...")
    
    with app.app_context():
        # 创建数据库表
        db.create_all()
        print("数据库表创建成功！")
        
        # 添加示例题目
        print("\n=== 添加示例题目 ===")
        quiz1 = Quiz.add_quiz(
            content="什么是Python？",
            answer="Python是一种高级编程语言，具有简洁、易读的语法特点。",
            analysis="Python是一种解释型、面向对象、动态数据类型的高级程序设计语言。"
        )
        print(f"添加题目成功: {quiz1.content}")
        
        quiz2 = Quiz.add_quiz(
            content="Flask是什么？",
            answer="Flask是一个轻量级的Python Web应用框架。",
            analysis="Flask是一个使用Python编写的轻量级Web应用框架，它使用Werkzeug作为WSGI工具库，Jinja2作为模板引擎。"
        )
        print(f"添加题目成功: {quiz2.content}")
        
        quiz3 = Quiz.add_quiz(
            content="SQLite数据库的特点是什么？",
            answer="SQLite是一个轻量级的、自给自足的、高可靠性的、嵌入式的、全功能的、开源的SQL数据库引擎。",
            analysis="SQLite不需要服务器进程，数据存储在单个文件中，非常适合嵌入式应用和小型应用。"
        )
        print(f"添加题目成功: {quiz3.content}")
        
        # 添加示例试卷
        print("\n=== 添加示例试卷 ===")
        paper1 = Paper.add_paper(
            name="Python基础测试卷",
            status="published"
        )
        print(f"添加试卷成功: {paper1.name}")
        
        paper2 = Paper.add_paper(
            name="Web开发基础测试卷",
            status="draft"
        )
        print(f"添加试卷成功: {paper2.name}")
        
        # 向试卷添加题目
        print("\n=== 向试卷添加题目 ===")
        # 向第一份试卷添加所有题目
        for i, quiz in enumerate([quiz1, quiz2, quiz3], 1):
            PaperQuiz.add_quiz_to_paper(
                paper_id=paper1.id,
                quiz_id=quiz.id,
                question_order=i,
                score=2.0
            )
            print(f"向试卷 '{paper1.name}' 添加题目: {quiz.content}")
        
        # 向第二份试卷添加前两个题目
        for i, quiz in enumerate([quiz1, quiz2], 1):
            PaperQuiz.add_quiz_to_paper(
                paper_id=paper2.id,
                quiz_id=quiz.id,
                question_order=i,
                score=3.0
            )
            print(f"向试卷 '{paper2.name}' 添加题目: {quiz.content}")
        
        # 添加示例答题记录
        print("\n=== 添加示例答题记录 ===")
        # 学生1答题记录
        student1_id = "student001"
        
        # 学生1答第一道题（正确）
        answer1 = Answer.add_answer(
            student_id=student1_id,
            paper_id=paper1.id,
            quiz_id=quiz1.id,
            student_answer="Python是一种高级编程语言，具有简洁、易读的语法特点。",
            is_correct=True,
            score=2.0
        )
        print(f"学生{student1_id}答题记录1: {'正确' if answer1.is_correct else '错误'}")
        
        # 学生1答第二道题（错误）
        answer2 = Answer.add_answer(
            student_id=student1_id,
            paper_id=paper1.id,
            quiz_id=quiz2.id,
            student_answer="Flask是一个数据库系统",
            is_correct=False,
            score=0.0
        )
        print(f"学生{student1_id}答题记录2: {'正确' if answer2.is_correct else '错误'}")
        
        # 学生1答第三道题（正确）
        answer3 = Answer.add_answer(
            student_id=student1_id,
            paper_id=paper1.id,
            quiz_id=quiz3.id,
            student_answer="SQLite是一个轻量级的、自给自足的、高可靠性的、嵌入式的、全功能的、开源的SQL数据库引擎。",
            is_correct=True,
            score=2.0
        )
        print(f"学生{student1_id}答题记录3: {'正确' if answer3.is_correct else '错误'}")
        
        # 学生2答题记录
        student2_id = "student002"
        
        # 学生2答第一道题（部分正确）
        answer4 = Answer.add_answer(
            student_id=student2_id,
            paper_id=paper1.id,
            quiz_id=quiz1.id,
            student_answer="Python是一种编程语言",
            is_correct=False,
            score=1.0
        )
        print(f"学生{student2_id}答题记录1: {'正确' if answer4.is_correct else '错误'}")
        
        # 学生2答第二道题（正确）
        answer5 = Answer.add_answer(
            student_id=student2_id,
            paper_id=paper1.id,
            quiz_id=quiz2.id,
            student_answer="Flask是一个轻量级的Python Web应用框架。",
            is_correct=True,
            score=2.0
        )
        print(f"学生{student2_id}答题记录2: {'正确' if answer5.is_correct else '错误'}")
        
        # 显示所有题目
        print("\n=== 显示所有题目 ===")
        quizzes = Quiz.get_all_quizzes()
        print(f"当前数据库中共有 {len(quizzes)} 道题目:")
        print("-" * 50)
        for quiz in quizzes:
            print(f"ID: {quiz.id}")
            print(f"题目: {quiz.content}")
            print(f"答案: {quiz.answer}")
            print(f"分析: {quiz.analysis}")
            print(f"创建时间: {quiz.created_at}")
            print("-" * 50)
        
        # 显示所有试卷
        print("\n=== 显示所有试卷 ===")
        papers = Paper.get_all_papers()
        print(f"当前数据库中共有 {len(papers)} 份试卷:")
        print("-" * 50)
        for paper in papers:
            print(f"ID: {paper.id}")
            print(f"试卷名称: {paper.name}")
            print(f"状态: {paper.status}")
            print(f"创建时间: {paper.created_at}")
            
            # 显示试卷中的题目
            paper_quizzes = PaperQuiz.get_paper_quizzes(paper.id)
            print(f"题目数量: {len(paper_quizzes)}")
            for pq in paper_quizzes:
                quiz = Quiz.get_quiz_by_id(pq.quiz_id)
                print(f"  - 题目{pq.question_order}: {quiz.content} (分值: {pq.score})")
            print("-" * 50)
        
        # 显示答题记录
        print("\n=== 显示答题记录 ===")
        answers = Answer.query.order_by(Answer.answered_at.desc()).all()
        print(f"当前数据库中共有 {len(answers)} 条答题记录:")
        print("-" * 50)
        for answer in answers:
            print(f"ID: {answer.id}")
            print(f"学生ID: {answer.student_id}")
            print(f"试卷ID: {answer.paper_id}")
            print(f"题目ID: {answer.quiz_id}")
            print(f"学生答案: {answer.student_answer}")
            print(f"是否正确: {'是' if answer.is_correct else '否'}")
            print(f"得分: {answer.score}")
            print(f"答题时间: {answer.answered_at}")
            print("-" * 50)
        
        # 显示学生成绩统计
        print("\n=== 学生成绩统计 ===")
        for student_id in [student1_id, student2_id]:
            total_score = Answer.get_student_paper_score(student_id, paper1.id)
            print(f"学生{student_id}在试卷{paper1.id}的总分: {total_score}")
        
        # 显示试卷统计
        print("\n=== 试卷统计 ===")
        for paper in papers:
            if paper.status == 'published':
                stats = Answer.get_paper_statistics(paper.id)
                print(f"试卷'{paper.name}'统计:")
                print(f"  总答题数: {stats['total_answers']}")
                print(f"  正确答题数: {stats['correct_answers']}")
                print(f"  正确率: {stats['accuracy_rate']}%")
                print(f"  平均分: {stats['average_score']}")
        
        print("\n数据库操作测试完成！")

if __name__ == '__main__':
    test_database_operations() 