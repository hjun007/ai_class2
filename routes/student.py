from flask import Blueprint, render_template, redirect, url_for, flash, request, session, jsonify, current_app
from models.paper import Paper
from models.paper_quiz import PaperQuiz
from models.quiz import Quiz
from models.answer import Answer
from models.exam_record import ExamRecord
from models.tool import Tool
from openai import OpenAI
from config import Config
import re
import os

# 创建学生蓝图
student_bp = Blueprint('student', __name__, url_prefix='/student')
URL_LINK_PREFIX = 'url_'

@student_bp.route('/login', methods=['GET', 'POST'])
def login():
    """学生登录页面"""
    if request.method == 'POST':
        # 兼容首页弹窗和登录页面的字段名
        student_id = request.form.get('username', '').strip() or request.form.get('student_id', '').strip()
        password = request.form.get('password', '').strip()
        
        if not student_id:
            flash('请输入学号！', 'error')
            return render_template('student/login.html')
        
        # 暂不核对密码，直接将用户名保存到session
        session['student_id'] = student_id
        session['student_name'] = student_id  # 可以后续改为真实姓名
        
        flash(f'欢迎 {student_id}！', 'success')
        return redirect(url_for('student.dashboard'))
    
    return render_template('student/login.html')

@student_bp.route('/dashboard')
def dashboard():
    """学生仪表板页面"""
    # 检查是否已登录
    if 'student_id' not in session:
        flash('请先登录！', 'error')
        return redirect(url_for('student.login'))
    
    return render_template('student/dashboard.html')

@student_bp.route('/quiz')
def quiz():
    """在线答题页面 - 显示试卷列表"""
    # 检查是否已登录
    if 'student_id' not in session:
        flash('请先登录！', 'error')
        return redirect(url_for('student.login'))
    
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
    # 检查是否已登录
    if 'student_id' not in session:
        flash('请先登录！', 'error')
        return redirect(url_for('student.login'))
    
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

@student_bp.route('/take_quiz2/<int:paper_id>')
def take_quiz2(paper_id):
    """学生逐步答题页面 - 单题显示模式"""
    # 检查是否已登录
    if 'student_id' not in session:
        flash('请先登录！', 'error')
        return redirect(url_for('student.login'))
    
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
                'paper_quiz': {
                    'question_order': pq.question_order,
                    'score': pq.score
                },
                'quiz': {
                    'id': quiz.id,
                    'content': quiz.content
                }
            })
    
    return render_template('student/take_quiz2.html', paper=paper, quizzes=quizzes_in_paper)

@student_bp.route('/ai-assistant')
def ai_assistant():
    """AI智能体页面"""
    # 检查是否已登录
    if 'student_id' not in session:
        flash('请先登录！', 'error')
        return redirect(url_for('student.login'))
    
    return render_template('student/ai_assistant.html') 

@student_bp.route('/ai_chat', methods=['POST'])
def ai_chat():
    """AI聊天接口"""
    # 检查是否已登录
    if 'student_id' not in session:
        return jsonify({'success': False, 'error': '请先登录'})
    
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        conversation_history = data.get('conversation_history', [])
        
        if not user_message:
            return jsonify({'success': False, 'error': '消息不能为空'})
        
        # 检查AI功能是否启用
        if not Config.is_ai_enabled():
            # 如果没有配置API密钥，返回模拟回复
            return get_mock_response(user_message, conversation_history)
        
        # 初始化DeepSeek客户端
        client = OpenAI(
            api_key=Config.DEEPSEEK_API_KEY,
            base_url=Config.DEEPSEEK_BASE_URL
        )
        
        # 构建消息历史
        messages = []
        
        # 添加系统提示
        messages.append({
            "role": "system",
            "content": Config.AI_SYSTEM_PROMPT
        })
        
        # 添加历史对话
        for msg in conversation_history:
            messages.append(msg)
        
        # 添加新的用户消息
        messages.append({"role": "user", "content": user_message})
        
        # 调用DeepSeek API
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            max_tokens=Config.AI_MAX_TOKENS,
            temperature=Config.AI_TEMPERATURE
        )
        
        ai_response = response.choices[0].message.content
        
        # 更新对话历史
        conversation_history.append({"role": "user", "content": user_message})
        conversation_history.append({"role": "assistant", "content": ai_response})
        
        # 限制历史记录长度
        if len(conversation_history) > Config.AI_MAX_HISTORY:
            conversation_history = conversation_history[-Config.AI_MAX_HISTORY:]
        
        return jsonify({
            'success': True,
            'response': ai_response,
            'conversation_history': conversation_history
        })
        
    except Exception as e:
        print(f"AI Chat Error: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'AI服务暂时不可用: {str(e)}'
        })

def get_mock_response(user_message, conversation_history):
    """当没有配置API密钥时的模拟回复"""
    mock_responses = {
        "你好": "你好！我是AI智能体助手，很高兴为你服务！",
        "hello": "Hello! I'm here to help you with your studies!",
        "帮助": "我可以帮你解答学习问题、提供课程辅导、解释概念等。有什么具体问题吗？",
        "python": "Python是一门非常流行的编程语言，语法简洁易学。你想了解Python的哪个方面呢？",
        "数学": "数学是所有科学的基础！你遇到什么数学问题了吗？我可以帮你解答。",
        "算法": "算法是解决问题的步骤和方法。你想学习哪种算法呢？排序、搜索、还是其他？"
    }
    
    # 简单的关键词匹配
    user_lower = user_message.lower()
    response = "我理解你的问题。虽然当前是演示模式，但在实际部署中，我会使用DeepSeek大模型为你提供更智能的回答。请配置DEEPSEEK_API_KEY环境变量以启用完整功能。"
    
    for keyword, mock_reply in mock_responses.items():
        if keyword in user_lower:
            response = mock_reply + "\n\n(当前为演示模式，请配置API密钥以获得完整AI功能)"
            break
    
    # 更新对话历史
    conversation_history.append({"role": "user", "content": user_message})
    conversation_history.append({"role": "assistant", "content": response})
    
    return jsonify({
        'success': True,
        'response': response,
        'conversation_history': conversation_history
    })

@student_bp.route('/submit_quiz/<int:paper_id>', methods=['POST'])
def submit_quiz(paper_id):
    """提交试卷答案"""
    # 检查是否已登录
    if 'student_id' not in session:
        flash('请先登录！', 'error')
        return redirect(url_for('student.login'))
    
    paper = Paper.get_paper_by_id(paper_id)
    if not paper:
        flash('试卷不存在！', 'error')
        return redirect(url_for('student.quiz'))
    
    # 确保试卷已发布
    if paper.status != 'published':
        flash('该试卷未发布，无法提交答案。', 'error')
        return redirect(url_for('student.quiz'))

    try:
        # 获取试卷中的所有题目
        paper_quizzes = PaperQuiz.get_paper_quizzes(paper_id)
        
        # 从session中获取学生ID
        student_id = session['student_id']
        
        # 遍历每个题目，获取学生答案并保存
        total_submitted = 0
        total_correct = 0
        total_score = 0.0
        answer_details = []
        
        for pq in paper_quizzes:
            answer_key = f"answer_{pq.quiz_id}"
            student_answer = request.form.get(answer_key, '').strip()
            
            if student_answer:  # 只保存非空答案
                # 获取题目信息
                quiz = Quiz.get_quiz_by_id(pq.quiz_id)
                
                # 自动判题：比较学生答案与正确答案
                is_correct = False
                score = 0.0
                
                if quiz and quiz.answer:
                    # 简单的文本比较判题（忽略大小写和首尾空格）
                    correct_answer = quiz.answer.strip().lower()
                    student_answer_normalized = student_answer.strip().lower()
                    
                    if correct_answer == student_answer_normalized:
                        is_correct = True
                        score = pq.score  # 使用试卷中设定的分值
                        total_correct += 1
                
                total_score += score
                
                # 创建答题记录
                Answer.add_answer(
                    student_id=student_id,
                    paper_id=paper_id,
                    quiz_id=pq.quiz_id,
                    student_answer=student_answer,
                    is_correct=is_correct,
                    score=score
                )
                
                # 收集答题详情用于显示
                answer_details.append({
                    'question_order': pq.question_order,
                    'question_content': quiz.content if quiz else '',
                    'student_answer': student_answer,
                    'correct_answer': quiz.answer if quiz else '',
                    'is_correct': is_correct,
                    'score': score
                })
                
                total_submitted += 1
        
        if total_submitted > 0:
            # 计算满分
            max_score = sum(pq.score for pq in paper_quizzes)
            
            # 创建考试记录
            exam_record = ExamRecord.add_exam_record(
                student_id=student_id,
                paper_id=paper_id,
                total_questions=len(paper_quizzes),
                answered_questions=total_submitted,
                correct_answers=total_correct,
                total_score=total_score,
                max_score=max_score
            )
            
            # 准备结果数据
            result_data = {
                'total_submitted': total_submitted,
                'total_correct': total_correct,
                'total_score': total_score,
                'max_score': max_score,
                'answer_details': answer_details,
                'exam_record_id': exam_record.id
            }
            
            # 将结果数据存储在session中，用于结果页面显示
            session['quiz_result'] = result_data
            session['quiz_result_paper_id'] = paper_id
            
            return redirect(url_for('student.quiz_result'))
        else:
            flash('没有检测到有效答案，请确保至少回答一道题目。', 'error')
            return redirect(url_for('student.take_quiz', paper_id=paper_id))
            
    except Exception as e:
        flash(f'提交失败：{str(e)}', 'error')
        return redirect(url_for('student.take_quiz', paper_id=paper_id))

@student_bp.route('/quiz_result')
def quiz_result():
    """显示答题结果页面"""
    # 检查是否已登录
    if 'student_id' not in session:
        flash('请先登录！', 'error')
        return redirect(url_for('student.login'))
    
    # 检查是否有结果数据
    if 'quiz_result' not in session or 'quiz_result_paper_id' not in session:
        flash('没有找到答题结果，请重新答题。', 'error')
        return redirect(url_for('student.quiz'))
    
    # 获取试卷信息
    paper_id = session['quiz_result_paper_id']
    paper = Paper.get_paper_by_id(paper_id)
    if not paper:
        flash('试卷不存在！', 'error')
        return redirect(url_for('student.quiz'))
    
    # 获取结果数据
    result = session['quiz_result']
    
    # 清除session中的结果数据（避免重复访问）
    session.pop('quiz_result', None)
    session.pop('quiz_result_paper_id', None)
    
    return render_template('student/quiz_result.html', paper=paper, result=result)

@student_bp.route('/exam_management')
def exam_management():
    """考试管理页面 - 查看考试记录"""
    # 检查是否已登录
    if 'student_id' not in session:
        flash('请先登录！', 'error')
        return redirect(url_for('student.login'))
    
    student_id = session['student_id']
    
    # 获取学生的考试记录
    exam_records = ExamRecord.get_student_exam_records(student_id)
    
    # 为每个记录添加试卷信息
    records_with_papers = []
    for record in exam_records:
        paper = Paper.get_paper_by_id(record.paper_id)
        records_with_papers.append({
            'record': record,
            'paper': paper
        })
    
    # 计算统计信息
    total_exams = len(exam_records)
    average_score = ExamRecord.get_student_average_score(student_id) if total_exams > 0 else 0
    total_score = sum(record.total_score for record in exam_records)
    
    statistics = {
        'total_exams': total_exams,
        'average_score': round(average_score, 1),
        'total_score': round(total_score, 1),
        'best_score': round(max(record.total_score for record in exam_records), 1) if exam_records else 0
    }
    
    return render_template('student/exam_management.html', 
                         records=records_with_papers, 
                         statistics=statistics)

@student_bp.route('/exam_detail/<int:record_id>')
def exam_detail(record_id):
    """查看考试详情"""
    # 检查是否已登录
    if 'student_id' not in session:
        flash('请先登录！', 'error')
        return redirect(url_for('student.login'))
    
    student_id = session['student_id']
    
    # 获取考试记录
    exam_record = ExamRecord.get_exam_record_by_id(record_id)
    if not exam_record or exam_record.student_id != student_id:
        flash('考试记录不存在或无权访问！', 'error')
        return redirect(url_for('student.exam_management'))
    
    # 获取试卷信息
    paper = Paper.get_paper_by_id(exam_record.paper_id)
    if not paper:
        flash('试卷不存在！', 'error')
        return redirect(url_for('student.exam_management'))
    
    # 获取该次考试的答题详情
    answers = Answer.get_student_answers(student_id, exam_record.paper_id)
    
    # 获取试卷题目信息
    paper_quizzes = PaperQuiz.get_paper_quizzes(exam_record.paper_id)
    
    # 构建答题详情
    answer_details = []
    for pq in paper_quizzes:
        quiz = Quiz.get_quiz_by_id(pq.quiz_id)
        # 找到对应的答案记录
        answer = next((ans for ans in answers if ans.quiz_id == pq.quiz_id), None)
        
        if answer and quiz:
            answer_details.append({
                'question_order': pq.question_order,
                'question_content': quiz.content,
                'student_answer': answer.student_answer,
                'correct_answer': quiz.answer,
                'is_correct': answer.is_correct,
                'score': answer.score,
                'max_score': pq.score
            })
    
    return render_template('student/exam_detail.html', 
                         exam_record=exam_record, 
                         paper=paper, 
                         answer_details=answer_details)

@student_bp.route('/logout')
def logout():
    """学生退出登录"""
    session.clear()
    flash('已退出登录！', 'info')
    return redirect(url_for('main.index'))

@student_bp.route('/toolbox')
def toolbox():
    """学生工具箱页面"""
    # 检查登录状态
    if 'student_id' not in session:
        flash('请先登录！', 'error')
        return redirect(url_for('student.login'))
    
    # 获取已上线的工具
    online_tools = Tool.get_online_tools()
    
    return render_template('student/toolbox.html', tools=online_tools)

@student_bp.route('/toolbox/tool/<int:tool_id>')
def use_tool(tool_id):
    """使用工具"""
    # 检查登录状态
    if 'student_id' not in session:
        flash('请先登录！', 'error')
        return redirect(url_for('student.login'))
    
    # 获取工具信息
    tool = Tool.get_tool_by_id(tool_id)
    if not tool:
        flash('工具不存在！', 'error')
        return redirect(url_for('student.toolbox'))
    
    # 检查工具是否已上线
    if tool.status != 'online':
        flash('该工具暂时不可用！', 'error')
        return redirect(url_for('student.toolbox'))
    
    # 增加浏览次数
    tool.increment_views()
    
    try:
        # 如果是URL链接占位文件：读取并重定向到目标链接
        if tool.file_name.lower().startswith(URL_LINK_PREFIX):
            with open(tool.file_path, 'r', encoding='utf-8') as f:
                content_all = f.read()
            # 优先从全文提取第一个 http(s) 链接
            url_match = re.search(r"https?://[^\s\"'<>]+", content_all, re.IGNORECASE)
            if url_match:
                return redirect(url_match.group(0))
            # 回退：首个非空行，清理BOM/引号并补全协议
            first_non_empty_line = ''
            for line in content_all.splitlines():
                stripped = line.strip().lstrip('\ufeff')
                if stripped:
                    first_non_empty_line = stripped
                    break
            if not first_non_empty_line:
                flash('跳转地址为空！', 'error')
                return redirect(url_for('student.toolbox'))
            target_url = first_non_empty_line
            if (target_url.startswith('"') and target_url.endswith('"')) or (target_url.startswith("'") and target_url.endswith("'")):
                target_url = target_url[1:-1].strip()
            if target_url.lower().startswith('www.'):
                target_url = 'http://' + target_url
            if not (target_url.lower().startswith('http://') or target_url.lower().startswith('https://')):
                target_url = 'http://' + target_url
            return redirect(target_url)

        # 常规HTML：读取并返回内容
        with open(tool.file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return content
    
    except Exception as e:
        current_app.logger.error(f"加载工具失败: {str(e)}")
        flash(f'工具加载失败: {str(e)}', 'error')
        return redirect(url_for('student.toolbox')) 