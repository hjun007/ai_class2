# 试题数据库使用说明

## 数据库结构

### Quiz表（题目表）
- `id`: 题目ID，主键，自动递增
- `content`: 题目内容，必填字段
- `answer`: 题目答案，必填字段  
- `analysis`: 题目分析，可选字段
- `created_at`: 创建时间，自动生成
- `updated_at`: 更新时间，自动更新

### Paper表（试卷表）
- `id`: 试卷ID，主键，自动递增
- `name`: 试卷名称，必填字段
- `status`: 试卷状态，默认'draft'，可选值：'draft'-草稿, 'published'-已发布, 'archived'-已归档
- `created_at`: 创建时间，自动生成
- `updated_at`: 更新时间，自动更新

### PaperQuiz表（试卷题目关联表）
- `id`: 关联ID，主键，自动递增
- `paper_id`: 试卷ID，外键关联Paper表
- `quiz_id`: 题目ID，外键关联Quiz表
- `question_order`: 题目顺序，必填字段
- `score`: 题目分值，默认1.0
- `created_at`: 创建时间，自动生成

### Answer表（答题记录表）
- `id`: 答题记录ID，主键，自动递增
- `student_id`: 学生ID，必填字段
- `paper_id`: 试卷ID，外键关联Paper表
- `quiz_id`: 题目ID，外键关联Quiz表
- `student_answer`: 学生答案，必填字段
- `is_correct`: 是否正确，默认False
- `score`: 得分，默认0.0
- `answered_at`: 答题时间，自动生成

## 使用方法

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 运行应用
```bash
python app.py
```
应用启动时会自动创建数据库文件

### 3. 测试数据库操作
```bash
python manage_db.py
```

## 数据库操作方法

### 题目操作
```python
from models.quiz import Quiz

# 添加题目
quiz = Quiz.add_quiz(
    content="题目内容",
    answer="题目答案",
    analysis="题目分析（可选）"
)

# 获取所有题目
all_quizzes = Quiz.get_all_quizzes()

# 根据ID获取题目
quiz = Quiz.get_quiz_by_id(1)
```

### 试卷操作
```python
from models.paper import Paper

# 添加试卷
paper = Paper.add_paper(
    name="试卷名称",
    status="draft"  # 可选：draft, published, archived
)

# 获取所有试卷
all_papers = Paper.get_all_papers()

# 根据状态获取试卷
draft_papers = Paper.get_papers_by_status("draft")

# 更新试卷状态
Paper.update_paper_status(1, "published")
```

### 试卷题目关联操作
```python
from models.paper_quiz import PaperQuiz

# 向试卷添加题目
PaperQuiz.add_quiz_to_paper(
    paper_id=1,
    quiz_id=1,
    question_order=1,
    score=2.0
)

# 获取试卷的所有题目
paper_quizzes = PaperQuiz.get_paper_quizzes(1)

# 从试卷中移除题目
PaperQuiz.remove_quiz_from_paper(1, 1)
```

### 答题记录操作
```python
from models.answer import Answer

# 添加答题记录
answer = Answer.add_answer(
    student_id="student001",
    paper_id=1,
    quiz_id=1,
    student_answer="学生答案",
    is_correct=True,
    score=2.0
)

# 获取学生的答题记录
student_answers = Answer.get_student_answers("student001")

# 获取学生在某份试卷的答题记录
paper_answers = Answer.get_student_answers("student001", paper_id=1)

# 获取试卷的所有答题记录
all_paper_answers = Answer.get_paper_answers(1)

# 获取学生试卷总分
total_score = Answer.get_student_paper_score("student001", 1)

# 获取试卷统计信息
stats = Answer.get_paper_statistics(1)
print(f"正确率: {stats['accuracy_rate']}%")
print(f"平均分: {stats['average_score']}")
```

## 数据库文件

- **数据库文件**: `quiz.db`（SQLite文件数据库）
- **位置**: `instance/quiz.db`（Flask实例目录）
- **自动创建**: 首次运行应用时自动生成
- **表结构**: 包含quizzes、papers、paper_quizzes、answers四个表

## 数据关系

- **一对多关系**：一个试卷可以包含多个题目（通过PaperQuiz表关联）
- **多对一关系**：一个题目可以被多个试卷使用
- **答题记录关系**：每个答题记录关联学生、试卷和题目
- **外键约束**：确保数据完整性和一致性

## 统计功能

### 学生成绩统计
- 获取学生在某份试卷的总分
- 查看学生的答题历史记录
- 分析学生的答题正确率

### 试卷统计
- 试卷的总答题数
- 正确答题数和正确率
- 平均分统计
- 题目难度分析

## 注意事项

1. 确保已安装Flask-SQLAlchemy
2. 数据库文件会自动创建在`instance`目录中
3. 所有数据库操作都需要在Flask应用上下文中进行
4. 建议使用提供的类方法进行数据库操作，避免直接操作session
5. 删除试卷前请确保已移除所有关联的题目和答题记录
6. 试卷状态变更会影响试卷的可用性
7. 数据库文件位置：`instance/quiz.db`
8. 答题记录包含详细的答题信息，便于后续分析 