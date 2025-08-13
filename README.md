# Flask + Tailwind CSS + SQLite 项目模板

这是一个标准的Flask Web项目模板，使用Tailwind CSS进行样式设计，并集成了SQLite数据库支持。

## 项目结构

```
ai_class2/
├── app.py              # 主应用文件
├── requirements.txt    # Python依赖文件
├── README.md          # 项目说明文档
├── static/            # 静态文件目录
│   ├── css/          # CSS样式文件
│   ├── js/           # JavaScript文件
│   └── images/       # 图片资源文件
├── templates/         # HTML模板文件目录
├── models/           # 数据模型目录
├── routes/           # 路由文件目录
└── venv/             # Python虚拟环境
```

## 快速开始

### 0. 创建虚拟环境

、、、bash
python -m venv venv
、、、

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 运行项目

```bash
python app.py
```

### 3. 访问应用

打开浏览器访问: http://localhost:8080

## 技术栈

- **后端**: Flask (Python Web框架)
- **前端**: Tailwind CSS (CSS框架)
- **数据库**: SQLite
- **模板引擎**: Jinja2

## 开发说明

- `app.py` - 主应用入口文件
- `templates/` - 存放HTML模板文件
- `static/` - 存放静态资源文件
- `models/` - 存放数据模型定义
- `routes/` - 存放路由处理逻辑

## 许可证

MIT License 