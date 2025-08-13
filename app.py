from flask import Flask
from routes.main import main_bp
from routes.student import student_bp
from routes.teacher import teacher_bp
from models import db

app = Flask(__name__)

# 数据库配置
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quiz.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key-here'

# 初始化数据库
db.init_app(app)

# 注册蓝图
app.register_blueprint(main_bp)
app.register_blueprint(student_bp)
app.register_blueprint(teacher_bp)

# 创建数据库表
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)