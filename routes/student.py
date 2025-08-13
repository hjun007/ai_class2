from flask import Blueprint, render_template, redirect, url_for
from models.paper import Paper
from models.paper_quiz import PaperQuiz
from models.quiz import Quiz

# 创建学生蓝图
student_bp = Blueprint('student', __name__, url_prefix='/student')

@student_bp.route('/login')
def login():
    """学生登录页面"""
    return render_template('student/login.html')

@student_bp.route('/dashboard')
def dashboard():
    """学生仪表板页面"""
    return render_template('student/dashboard.html')

@student_bp.route('/quiz')
def quiz():
    """在线答题页面"""
    # 获取已发布的试卷
    published_papers = Paper.get_papers_by_status('published')
    
    # 为每个试卷获取题目信息
    papers_with_quizzes = []
    for paper in published_papers:
        paper_quizzes = PaperQuiz.get_paper_quizzes(paper.id)
        quiz_count = len(paper_quizzes)
        total_score = sum(pq.score for pq in paper_quizzes)
        
        papers_with_quizzes.append({
            'paper': paper,
            'quiz_count': quiz_count,
            'total_score': total_score
        })
    
    return render_template('student/quiz.html', papers=papers_with_quizzes)

@student_bp.route('/ai-assistant')
def ai_assistant():
    """AI智能体页面"""
    return render_template('student/ai_assistant.html') 