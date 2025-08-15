from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify, current_app
from models.paper import Paper
from models.paper_quiz import PaperQuiz
from models.quiz import Quiz
from models.answer import Answer
from models.exam_record import ExamRecord
from models import db
import os
from openai import OpenAI
import json
import logging
from config import Config
from collections import defaultdict
from datetime import datetime, timedelta

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

        if not Config.DEEPSEEK_API_KEY:
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
            client = OpenAI(api_key=Config.DEEPSEEK_API_KEY, base_url=Config.DEEPSEEK_BASE_URL)
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
    # 获取所有学生的考试记录，按学生ID分组
    all_exam_records = ExamRecord.query.all()
    students_data = {}
    
    for record in all_exam_records:
        if record.student_id not in students_data:
            students_data[record.student_id] = {
                'student_id': record.student_id,
                'total_exams': 0,
                'total_score': 0,
                'total_max_score': 0,
                'latest_exam': None
            }
        
        student_data = students_data[record.student_id]
        student_data['total_exams'] += 1
        student_data['total_score'] += record.total_score
        student_data['total_max_score'] += record.max_score
        
        if not student_data['latest_exam'] or record.submit_time > student_data['latest_exam']:
            student_data['latest_exam'] = record.submit_time
    
    # 计算每个学生的平均分和成绩率
    for student_id, data in students_data.items():
        if data['total_max_score'] > 0:
            data['average_rate'] = (data['total_score'] / data['total_max_score']) * 100
        else:
            data['average_rate'] = 0
        
        if data['total_exams'] > 0:
            data['average_score'] = data['total_score'] / data['total_exams']
        else:
            data['average_score'] = 0
    
    # 转换为列表并排序
    students_list = list(students_data.values())
    students_list.sort(key=lambda x: x['average_rate'], reverse=True)
    
    return render_template('teacher/statistics.html', students=students_list)

@teacher_bp.route('/statistics/student/<student_id>')
def student_analysis(student_id):
    """学生详细分析页面"""
    # 获取学生的所有考试记录
    exam_records = ExamRecord.get_student_exam_records(student_id)
    
    if not exam_records:
        flash('该学生没有考试记录！', 'error')
        return redirect(url_for('teacher.statistics'))
    
    # 获取学生的所有答题记录
    all_answers = Answer.get_student_answers(student_id)
    
    # 准备分析数据
    analysis_data = prepare_student_analysis_data(student_id, exam_records, all_answers)
    
    return render_template('teacher/student_analysis.html', 
                         student_id=student_id,
                         analysis_data=analysis_data)

@teacher_bp.route('/api/generate_student_analysis', methods=['POST'])
def generate_student_analysis():
    """使用AI生成学生学习分析报告"""
    try:
        data = request.get_json()
        student_id = data.get('student_id')
        
        if not student_id:
            return jsonify({'success': False, 'error': '学生ID不能为空'})
        
        # 获取学生数据
        exam_records = ExamRecord.get_student_exam_records(student_id)
        all_answers = Answer.get_student_answers(student_id)
        
        if not exam_records:
            return jsonify({'success': False, 'error': '该学生没有考试记录'})
        
        # 准备AI分析的数据
        analysis_prompt = prepare_ai_analysis_prompt(student_id, exam_records, all_answers)
        
        # 调用AI生成分析报告
        if Config.is_ai_enabled():
            ai_analysis = call_ai_for_analysis(analysis_prompt)
        else:
            ai_analysis = generate_mock_analysis(student_id, exam_records)
        
        return jsonify({
            'success': True,
            'analysis': ai_analysis
        })
        
    except Exception as e:
        current_app.logger.error(f"AI分析错误: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'分析生成失败: {str(e)}'
        })

def prepare_student_analysis_data(student_id, exam_records, all_answers):
    """准备学生分析数据"""
    # 基础统计
    total_exams = len(exam_records)
    total_score = sum(record.total_score for record in exam_records)
    total_max_score = sum(record.max_score for record in exam_records)
    average_score = total_score / total_exams if total_exams > 0 else 0
    success_rate = (total_score / total_max_score * 100) if total_max_score > 0 else 0
    
    # 考试时间趋势
    exam_trends = []
    for record in sorted(exam_records, key=lambda x: x.submit_time):
        rate = (record.total_score / record.max_score * 100) if record.max_score > 0 else 0
        exam_trends.append({
            'date': record.submit_time.strftime('%Y-%m-%d'),
            'score': record.total_score,
            'max_score': record.max_score,
            'rate': round(rate, 1)
        })
    
    # 题目分析 - 按试卷分组
    papers_analysis = defaultdict(list)
    for answer in all_answers:
        paper_id = answer.paper_id
        quiz = Quiz.get_quiz_by_id(answer.quiz_id)
        paper = Paper.get_paper_by_id(paper_id)
        
        if quiz and paper:
            papers_analysis[paper_id].append({
                'paper_name': paper.name,
                'question_content': quiz.content[:100] + '...' if len(quiz.content) > 100 else quiz.content,
                'student_answer': answer.student_answer,
                'correct_answer': quiz.answer,
                'is_correct': answer.is_correct,
                'score': answer.score
            })
    
    # 错误题目分析
    wrong_answers = [answer for answer in all_answers if not answer.is_correct]
    error_patterns = analyze_error_patterns(wrong_answers)
    
    return {
        'basic_stats': {
            'total_exams': total_exams,
            'average_score': round(average_score, 2),
            'success_rate': round(success_rate, 1),
            'total_score': total_score,
            'total_max_score': total_max_score
        },
        'exam_trends': exam_trends,
        'papers_analysis': dict(papers_analysis),
        'error_patterns': error_patterns,
        'latest_exam': exam_records[0] if exam_records else None
    }

def analyze_error_patterns(wrong_answers):
    """分析错误模式"""
    if not wrong_answers:
        return []
    
    # 简单的错误分析
    patterns = []
    
    # 按题目内容关键词分类错误
    keyword_errors = defaultdict(int)
    for answer in wrong_answers:
        quiz = Quiz.get_quiz_by_id(answer.quiz_id)
        if quiz:
            # 简单提取关键词（实际应用中可以更复杂）
            content_lower = quiz.content.lower()
            if '算法' in content_lower:
                keyword_errors['算法类题目'] += 1
            elif 'python' in content_lower:
                keyword_errors['Python编程'] += 1
            elif '数学' in content_lower or '计算' in content_lower:
                keyword_errors['数学计算'] += 1
            elif '概念' in content_lower or '定义' in content_lower:
                keyword_errors['概念理解'] += 1
            else:
                keyword_errors['其他类型'] += 1
    
    for category, count in keyword_errors.items():
        if count > 0:
            patterns.append({
                'category': category,
                'error_count': count,
                'percentage': round(count / len(wrong_answers) * 100, 1)
            })
    
    return sorted(patterns, key=lambda x: x['error_count'], reverse=True)

def prepare_ai_analysis_prompt(student_id, exam_records, all_answers):
    """准备AI分析的提示词"""
    # 统计数据
    total_exams = len(exam_records)
    total_score = sum(record.total_score for record in exam_records)
    total_max_score = sum(record.max_score for record in exam_records)
    success_rate = (total_score / total_max_score * 100) if total_max_score > 0 else 0
    
    # 错误答案分析
    wrong_answers = [answer for answer in all_answers if not answer.is_correct]
    error_rate = (len(wrong_answers) / len(all_answers) * 100) if all_answers else 0
    
    # 考试表现趋势
    recent_records = sorted(exam_records, key=lambda x: x.submit_time)[-5:]  # 最近5次考试
    trends = []
    for record in recent_records:
        rate = (record.total_score / record.max_score * 100) if record.max_score > 0 else 0
        trends.append(f"{record.submit_time.strftime('%m-%d')}: {rate:.1f}%")
    
    prompt = f"""请分析学生ID为{student_id}的学习情况，并提供专业的学习建议。

学生基本数据：
- 总考试次数：{total_exams}次
- 总体正确率：{success_rate:.1f}%
- 错误率：{error_rate:.1f}%
- 平均分：{total_score/total_exams if total_exams > 0 else 0:.1f}分

最近考试表现趋势：
{', '.join(trends)}

请从以下几个方面进行分析：
1. 学习表现总体评价
2. 强项和弱项分析
3. 学习趋势分析（是否有进步或退步）
4. 具体学习建议和改进方向
5. 老师关注重点

请用专业、客观、建设性的语言进行分析，字数控制在500字以内。"""

    return prompt

def call_ai_for_analysis(prompt):
    """调用AI生成分析报告"""
    try:
        client = OpenAI(
            api_key=Config.DEEPSEEK_API_KEY,
            base_url=Config.DEEPSEEK_BASE_URL
        )
        
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {
                    "role": "system",
                    "content": "你是一位专业的教育分析师，擅长根据学生的学习数据进行深入分析并提供有价值的教学建议。请用专业、客观、建设性的语言进行分析。"
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=800,
            temperature=0.7
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        current_app.logger.error(f"AI分析调用失败: {str(e)}")
        raise e

def generate_mock_analysis(student_id, exam_records):
    """生成模拟分析报告（演示模式）"""
    total_exams = len(exam_records)
    avg_score = sum(record.total_score for record in exam_records) / total_exams if total_exams > 0 else 0
    
    return f"""**学习表现分析报告**（演示模式）

**总体评价：**
学生{student_id}共参加了{total_exams}次考试，平均分为{avg_score:.1f}分。从整体表现来看，该学生学习态度较为积极，参与度较高。

**强项分析：**
- 考试参与度高，说明学习积极性较好
- 持续性学习表现良好

**改进建议：**
1. 建议针对错误较多的题型进行专项练习
2. 加强基础概念的理解和掌握
3. 定期复习已学知识，形成知识体系
4. 可以尝试做更多的综合性练习题

**老师关注重点：**
- 关注学生的学习方法是否得当
- 及时反馈和鼓励，保持学习积极性
- 个性化辅导，针对薄弱环节加强指导

*注：当前为演示模式，配置DEEPSEEK_API_KEY后可获得更详细的AI分析报告。*""" 