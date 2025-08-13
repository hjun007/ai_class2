from flask import Blueprint, render_template, redirect, url_for, flash
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
    """在线答题页面 - 显示试卷列表"""
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

@student_bp.route('/take_quiz/<int:paper_id>')
def take_quiz(paper_id):
    """学生在线答题页面 - 显示试卷题目"""
    paper = Paper.get_paper_by_id(paper_id)
    if not paper:
        flash('试卷不存在！', 'error')
        return redirect(url_for('student.quiz'))
    
    # 确保试卷已发布
    if paper.status != 'published':
        flash('该试卷未发布，无法进行答题。' , 'error')
        return redirect(url_for('student.quiz'))

    # 获取试卷中的所有题目
    paper_quizzes = PaperQuiz.get_paper_quizzes(paper_id)
    quizzes_in_paper = []
    for pq in paper_quizzes:
        quiz = Quiz.get_quiz_by_id(pq.quiz_id)
        if quiz:
            quizzes_in_paper.append({
                'paper_quiz': pq,
                'quiz': quiz
            })
    
    return render_template('student/take_quiz.html', paper=paper, quizzes=quizzes_in_paper)

@student_bp.route('/ai-assistant')
def ai_assistant():
    """AI智能体页面"""
    return render_template('student/ai_assistant.html') 