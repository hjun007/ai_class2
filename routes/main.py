from flask import Blueprint, render_template

# 创建蓝图
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """主页面路由"""
    return render_template('index.html') 