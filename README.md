# JIRA Test Case Import Tool

一个用于将 Excel 格式的测试用例批量导入到 JIRA 的 Web 工具。

## 功能特点

- 支持通过 Web 界面上传 Excel 文件
- 自动将 Excel 中的测试用例转换为 JIRA Test Case
- 支持批量导入多个测试用例
- 实时显示导入进度和结果

## 安装说明

1. 克隆项目到本地： 
```
git clone [你的仓库地址]
```

2. 创建并激活虚拟环境（可跳过）：
```
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. 安装依赖：
```
pip install -r requirements.txt
```

## 配置说明

1. 创建配置文件 `config.py`，包含以下内容：
```
# JIRA服务器配置
JIRA_SERVER = "你的JIRA服务器地址"
JIRA_USERNAME = "你的JIRA用户名"
JIRA_PASSWORD = "你的JIRA密码"
JIRA_PROJECT_KEY = "项目KEY"

# Flask应用配置
SECRET_KEY = 'your_secret_key_here'
UPLOAD_FOLDER = 'uploads'
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB 
```

## Excel 文件格式要求

Excel 文件需要包含以下列：
- Test Case Name（测试用例名称）
- Description（描述）
- Steps（步骤）
- Expected Results（预期结果）

## 使用说明

1. 运行应用：
```
python import_jira_testcases.py
```

2. 在浏览器中访问：`http://localhost:5000`

3. 上传符合格式要求的 Excel 文件

4. 点击提交，等待导入完成

## 注意事项

- 确保 JIRA 服务器可以访问
- Excel 文件格式必须符合要求
- JIRA 账号需要有创建测试用例的权限

## 贡献指南

欢迎提交 Pull Request 或提出 Issue。