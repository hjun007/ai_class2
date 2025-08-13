from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify, current_app
from models.paper import Paper
from models.paper_quiz import PaperQuiz
from models.quiz import Quiz
from models import db
import os
from openai import OpenAI
import json
import logging

# 创建老师蓝图
teacher_bp = Blueprint('teacher', __name__, url_prefix='/teacher')

# 配置OpenAI API
# openai.api_key = os.environ.get('OPENAI_API_KEY')

@teacher_bp.route('/login')
def login():
    """老师登录页面"""
    return render_template('teacher/login.html')

@teacher_bp.route('/dashboard')
def dashboard():
    """老师仪表板页面"""
    return render_template('teacher/dashboard.html')

@teacher_bp.route('/paper-management')
def paper_management():
    """试卷管理页面"""
    # 获取所有试卷
    all_papers = Paper.get_all_papers()
    return render_template('teacher/paper_management.html', papers=all_papers)

@teacher_bp.route('/paper/<int:paper_id>/view')
def view_paper(paper_id):
    """查看试卷详情页面"""
    paper = Paper.get_paper_by_id(paper_id)
    if not paper:
        flash('试卷不存在！', 'error')
        return redirect(url_for('teacher.paper_management'))
    
    # 获取试卷中的所有题目
    paper_quizzes = PaperQuiz.get_paper_quizzes(paper_id)
    quizzes_with_info = []
    
    for pq in paper_quizzes:
        quiz = Quiz.get_quiz_by_id(pq.quiz_id)
        if quiz:
            quizzes_with_info.append({
                'paper_quiz': pq,
                'quiz': quiz
            })
    
    # 计算试卷统计信息
    total_questions = len(quizzes_with_info)
    total_score = sum(pq['paper_quiz'].score for pq in quizzes_with_info)
    
    return render_template('teacher/view_paper.html', 
                         paper=paper, 
                         quizzes=quizzes_with_info,
                         total_questions=total_questions,
                         total_score=total_score)

@teacher_bp.route('/paper/create', methods=['GET', 'POST'])
def create_paper():
    """创建试卷"""
    if request.method == 'POST':
        name = request.form.get('name')
        if name:
            paper = Paper.add_paper(name=name, status='draft')
            flash('试卷创建成功！', 'success')
            return redirect(url_for('teacher.paper_management'))
        else:
            flash('请输入试卷名称！', 'error')
    
    return render_template('teacher/create_paper.html')

@teacher_bp.route('/paper/<int:paper_id>/edit', methods=['GET', 'POST'])
def edit_paper(paper_id):
    """编辑试卷"""
    paper = Paper.get_paper_by_id(paper_id)
    if not paper:
        flash('试卷不存在！', 'error')
        return redirect(url_for('teacher.paper_management'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        status = request.form.get('status')
        if name:
            paper.name = name
            paper.status = status
            db.session.commit()
            flash('试卷更新成功！', 'success')
            return redirect(url_for('teacher.paper_management'))
        else:
            flash('请输入试卷名称！', 'error')

    # 获取当前试卷中的题目
    paper_quizzes_raw = PaperQuiz.get_paper_quizzes(paper_id)
    paper_quizzes = []
    paper_quiz_ids = set()
    for pq in paper_quizzes_raw:
        quiz = Quiz.get_quiz_by_id(pq.quiz_id)
        if quiz:
            paper_quizzes.append({'paper_quiz': pq, 'quiz': quiz})
            paper_quiz_ids.add(quiz.id)

    # 获取题库中所有题目
    all_quizzes = Quiz.get_all_quizzes()
    # 筛选出不在当前试卷中的题目
    available_quizzes = [q for q in all_quizzes if q.id not in paper_quiz_ids]

    # 计算当前试卷的总分
    paper_total_score = sum(pq['paper_quiz'].score for pq in paper_quizzes)
    
    return render_template('teacher/edit_paper.html', 
                           paper=paper,
                           paper_quizzes=paper_quizzes,
                           available_quizzes=available_quizzes,
                           paper_total_score=paper_total_score)

@teacher_bp.route('/paper/<int:paper_id>/add_quiz', methods=['POST'])
def add_quiz_to_paper(paper_id):
    """向试卷添加题目"""
    quiz_id = request.form.get('quiz_id', type=int)
    if not quiz_id:
        flash('请选择要添加的题目！', 'error')
        return redirect(url_for('teacher.edit_paper', paper_id=paper_id))
    
    # 检查题目是否已存在于试卷中
    existing_pq = PaperQuiz.query.filter_by(paper_id=paper_id, quiz_id=quiz_id).first()
    if existing_pq:
        flash('该题目已存在于当前试卷中！', 'warning')
        return redirect(url_for('teacher.edit_paper', paper_id=paper_id))

    # 获取当前试卷中题目数量，作为新题目的顺序
    paper_quizzes_count = PaperQuiz.query.filter_by(paper_id=paper_id).count()
    new_order = paper_quizzes_count + 1

    # 可以设置默认分值，或者从表单获取
    default_score = 2.0 # 假设默认分值是2分

    try:
        PaperQuiz.add_quiz_to_paper(
            paper_id=paper_id,
            quiz_id=quiz_id,
            question_order=new_order,
            score=default_score
        )
        flash('题目添加成功！', 'success')
    except Exception as e:
        flash(f'题目添加失败: {e}', 'error')
    
    return redirect(url_for('teacher.edit_paper', paper_id=paper_id))

@teacher_bp.route('/paper/<int:paper_id>/remove_quiz', methods=['POST'])
def remove_quiz_from_paper(paper_id):
    """从试卷中移除题目"""
    quiz_id = request.form.get('quiz_id', type=int)
    if not quiz_id:
        flash('请选择要移除的题目！', 'error')
        return redirect(url_for('teacher.edit_paper', paper_id=paper_id))
    
    try:
        success = PaperQuiz.remove_quiz_from_paper(paper_id, quiz_id)
        if success:
            flash('题目移除成功！', 'success')
        else:
            flash('题目移除失败！', 'error')
    except Exception as e:
        flash(f'题目移除失败: {e}', 'error')

    return redirect(url_for('teacher.edit_paper', paper_id=paper_id))

@teacher_bp.route('/paper/<int:paper_id>/delete', methods=['POST'])
def delete_paper(paper_id):
    """删除试卷"""
    # 在删除试卷前，先删除所有关联的PaperQuiz和Answer记录
    with db.session.no_autoflush:
        PaperQuiz.query.filter_by(paper_id=paper_id).delete()
        Answer.query.filter_by(paper_id=paper_id).delete()
        
    success = Paper.delete_paper(paper_id)
    if success:
        flash('试卷删除成功！', 'success')
    else:
        flash('试卷删除失败！', 'error')
    return redirect(url_for('teacher.paper_management'))

@teacher_bp.route('/paper/<int:paper_id>/publish', methods=['POST'])
def publish_paper(paper_id):
    """发布试卷"""
    success = Paper.update_paper_status(paper_id, 'published')
    if success:
        flash('试卷发布成功！', 'success')
    else:
        flash('试卷发布失败！', 'error')
    return redirect(url_for('teacher.paper_management'))

@teacher_bp.route('/paper/<int:paper_id>/unpublish', methods=['POST'])
def unpublish_paper(paper_id):
    """取消发布试卷"""
    success = Paper.update_paper_status(paper_id, 'draft')
    if success:
        flash('试卷已取消发布！', 'success')
    else:
        flash('操作失败！', 'error')
    return redirect(url_for('teacher.paper_management'))

@teacher_bp.route('/smart-quiz', methods=['GET', 'POST'])
def smart_quiz():
    """智能出题页面"""
    current_app.logger.debug("[smart_quiz] Entered function. method=%s", request.method)
    generated_quizzes = []
    if request.method == 'POST':
        subject = request.form.get('subject')
        grade = request.form.get('grade')
        question_type = request.form.get('question_type')
        num_questions = int(request.form.get('num_questions', 1))
        knowledge_points = request.form.get('knowledge_points')
        current_app.logger.debug(
            "[smart_quiz] Form params: subject=%s grade=%s type=%s num=%s kp_len=%s",
            subject, grade, question_type, num_questions, len(knowledge_points or "")
        )

        if not all([subject, grade, question_type, num_questions, knowledge_points]):
            current_app.logger.debug("[smart_quiz] Missing required fields.")
            flash('请填写所有必填项！', 'error')
            return render_template('teacher/smart_quiz.html', generated_quizzes=generated_quizzes)

        if not os.environ.get('OPENAI_API_KEY'):
            current_app.logger.error("[smart_quiz] OPENAI_API_KEY is not set.")
            flash('OpenAI API 密钥未配置，请设置 OPENAI_API_KEY 环境变量。' , 'error')
            return render_template('teacher/smart_quiz.html', generated_quizzes=generated_quizzes)

        # 注意：避免在 f-string 中直接包含未转义的大括号，采用首段 f-string + 后续普通字符串拼接
        prompt = (
            f"请生成{num_questions}道关于{subject}{grade}的{question_type}，主要考察{knowledge_points}知识点。\n"
            "每道题目需包含：题目内容(content)、题目答案(answer)、题目分析(analysis)。\n"
            "请严格按照以下JSON格式返回（不要添加任何其他文字）：\n"
            "{\n"
            "  \"quizzes\": [\n"
            "    {\"id\": 1, \"content\": \"题目内容描述。A. 选项1, B. 选项2, C. 选项3, D. 选项4\", \"answer\": \"A\", \"analysis\": \"答案解析\"},\n"
            "    {\"id\": 2, \"content\": \"题目内容描述。A. 选项1, B. 选项2, C. 选项3, D. 选项4\", \"answer\": \"A\", \"analysis\": \"答案解析\"}\n"
            "  ]\n"
            "}\n"
            "请确保JSON格式严格正确，并且所有键都必须是英文小写。\n"
            "确保题型正确，如选择题，填空题，判断题，简答题，计算题，应用题，证明题，论述题，分析题，综合题，开放题，讨论题，辩论题，演讲题，写作题，翻译题，阅读理解题，听力理解题，口语交际题，作文题，其他题型。\n"
            "选择题的题目和选项作为content的值，答案作为answer的值，分析作为analysis的值。"
        )
        current_app.logger.debug("[smart_quiz] Prompt length=%s", len(prompt))

        try:
            # 注意：base_url 和 model 可能由外部修改为 deepseek
            current_app.logger.debug("[smart_quiz] Calling LLM chat.completions.create ...")
            client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'), base_url="https://api.deepseek.com/v1")
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {
                        "role": "system", 
                        "content": "你是一位专业的教师，擅长出题。请严格按照用户要求生成题目，并以JSON格式返回。"
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=4000
            )
            current_app.logger.debug(
                "[smart_quiz] LLM response received. has_choices=%s",
                hasattr(response, 'choices')
            )

            response_content = response.choices[0].message.content if getattr(response, 'choices', None) else ''
            current_app.logger.debug("[smart_quiz] Response content length=%s", len(response_content or ""))
            current_app.logger.debug("[smart_quiz] Response content=%s", response_content)
            data = json.loads(response_content)
            quizzes = data.get("quizzes", [])
            current_app.logger.debug("[smart_quiz] Parsed quizzes count=%s", len(quizzes))

            if quizzes:
                saved = 0
                for q_data in quizzes:
                    content = q_data.get('content')
                    answer = q_data.get('answer')
                    analysis = q_data.get('analysis')
                    if content and answer:
                        new_quiz = Quiz.add_quiz(content=content, answer=answer, analysis=analysis)
                        generated_quizzes.append(new_quiz)
                        saved += 1
                current_app.logger.debug("[smart_quiz] Saved quizzes count=%s", saved)
                flash(f'成功生成并保存 {saved} 道题目！', 'success')
            else:
                current_app.logger.error("[smart_quiz] JSON missing 'quizzes' or empty.")
                flash('AI返回的数据格式不正确，请重试。' , 'error')

        except json.JSONDecodeError as e:
            current_app.logger.exception("[smart_quiz] JSON decode error: %s", e)
            flash('AI返回的响应不是有效的JSON格式，请重试。' , 'error')
        except Exception as e:
            current_app.logger.exception("[smart_quiz] Unexpected error: %s", e)
            flash(f'生成题目时发生未知错误: {e}', 'error')

    else:
        current_app.logger.debug("[smart_quiz] GET request - rendering form only.")

    return render_template('teacher/smart_quiz.html', generated_quizzes=generated_quizzes)

@teacher_bp.route('/statistics')
def statistics():
    """统计分析页面"""
    return render_template('teacher/statistics.html') 