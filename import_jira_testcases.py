import pandas as pd
from jira import JIRA, JIRAError
from jira.exceptions import JIRAError
import logging
import glob
from flask import Flask, request, render_template, flash, redirect, url_for
from werkzeug.utils import secure_filename
import os
from config import *

# 配置日志，记录错误信息
logging.basicConfig(filename='jira_import.log', level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)
app.secret_key = SECRET_KEY
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH
ALLOWED_EXTENSIONS = {'xlsx', 'xls'}

# 确保上传文件夹存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def read_excel(file_path):
    """读取 Excel 文件并返回 DataFrame"""
    try:
        df = pd.read_excel(file_path, engine='openpyxl')
        required_columns = ['自定义编号', '*用例标题', '前置条件', '*测试步骤', '*预期结果', '*用例属性', '*用例类型', '*用例等级', '功能模块', '作者']
        if not all(col in df.columns for col in required_columns):
            raise ValueError("Excel 缺少必要列！必须包含：自定义编号、用例标题、测试步骤、预期结果、用例属性、用例类型、用例等级、功能模块、作者")
        return df
    except Exception as e:
        logging.error(f"读取 Excel 失败: {e}")
        raise

def connect_jira(jira_url, username, password):
    """连接 Jira 服务器"""
    try:
        jira = JIRA(server=jira_url, basic_auth=(username, password))
        return jira
    except JIRAError as e:
        logging.error(f"连接 Jira 失败: {e.text}")
        raise

def create_test_case(jira, project_key, row):
    """创建单个测试用例"""
    try:
        # 映射字段到 Jira 格式
        # 准备测试步骤字段
        step_fields = {}
        if not pd.isna(row['前置条件']):
            step_fields['Data'] = row['前置条件']
        if not pd.isna(row['*测试步骤']):
            step_fields['Action'] = row['*测试步骤']
        if not pd.isna(row['*预期结果']):
            step_fields['Expected Result'] = row['*预期结果']

        # 准备基本字段
        # 检查必要字段是否存在且非空
        if pd.isna(row['*用例标题']) or pd.isna(row['功能模块']):
            error_msg = f"缺少必要字段: {'用例标题' if pd.isna(row['*用例标题']) else ''} {'功能模块' if pd.isna(row['功能模块']) else ''}"
            logging.error(error_msg)
            raise ValueError(error_msg)
            return None
        # 映射优先级
        
        priority_mapping = {
            'P0': {'name': 'Highest'},
            'P1': {'name': 'High'}, 
            'P2': {'name': 'Medium'},
            'P3': {'name': 'Low'},
            'P4': {'name': 'Lowest'}
        }

        issue_dict = {
            'project': {'key': project_key},
            'summary': row['*用例标题'],
            'issuetype': {'name': 'Test'},
            'labels': [row['功能模块']]
        }
                # 如果存在优先级字段且非空，则添加到issue字典中
        if '*用例等级' in row and not pd.isna(row['*用例等级']):
            priority = priority_mapping.get(row['*用例等级'])
            if priority:
                issue_dict['priority'] = priority
            else:
                logging.warning(f"无效的优先级值: {row['*用例等级']} - {row['*用例标题']}")

        # 只有当存在非空的测试步骤字段时才添加customfield_10411
        
        if step_fields:
            issue_dict['customfield_10411'] = {
                'steps': [
                    {
                        'fields': step_fields
                    }
                ]
            }
        # 创建用例并返回 ID
        issue = jira.create_issue(fields=issue_dict)
        print(f"用例创建成功: {issue.key} - {row['*用例标题']}")
        return issue.key
    except JIRAError as e:
        logging.error(f"创建用例失败: {row['*用例标题']} - {e.text}")
        print(f"创建用例失败: {row['*用例标题']} - {e.text}")
        return None

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('没有选择文件')
            return redirect(request.url)
        
        files = request.files.getlist('file')  # 获取所有上传的文件
        
        if not files or all(file.filename == '' for file in files):
            flash('没有选择文件')
            return redirect(request.url)

        uploaded_files = []
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                uploaded_files.append(filepath)

        if uploaded_files:
            try:
                # 执行导入操作
                created_issues = import_to_jira(uploaded_files, jira_server, project_key)
                flash(f'成功导入 {len(created_issues)} 个测试用例')
            except Exception as e:
                flash(f'导入失败: {str(e)}')
            
            # 清理上传的文件
            for filepath in uploaded_files:
                try:
                    os.remove(filepath)
                except:
                    pass
                    
        return redirect(url_for('upload_file'))
    
    return render_template('upload.html')

def import_to_jira(file_paths, jira_url, project_key):
    """主函数：读取上传的Excel文件并批量导入Jira"""
    try:
        # 读取所有上传的Excel文件并合并
        dfs = []
        for file_path in file_paths:
            try:
                df = read_excel(file_path)
                dfs.append(df)
                print(f"成功读取文件: {file_path}")
            except Exception as e:
                logging.error(f"读取文件 {file_path} 失败: {e}")
                print(f"读取文件 {file_path} 失败: {e}")
                continue
        
        if not dfs:
            raise ValueError("没有成功读取任何Excel文件")
            
        df = pd.concat(dfs, ignore_index=True)
        
        username = JIRA_USERNAME
        password = JIRA_PASSWORD
        
        # 连接 Jira
        jira = connect_jira(jira_url, username, password)
        
        # 遍历每一行并创建用例
        created_issues = []
        failed_issues = []  # 新增：记录失败的用例
        for index, row in df.iterrows():
            try:
                issue_key = create_test_case(jira, project_key, row)
                if issue_key:
                    created_issues.append(issue_key)
            except Exception as e:
                # 记录失败的用例信息
                error_msg = f"行号 {index + 2}: {row.get('*用例标题', 'Unknown')} - 错误: {str(e)}"
                failed_issues.append(error_msg)
                logging.error(error_msg)
                continue  # 继续处理下一个用例
        
        # 打印导入结果统计
        print(f"\n导入结果统计:")
        print(f"成功导入: {len(created_issues)} 个测试用例")
        if failed_issues:
            print(f"失败用例: {len(failed_issues)} 个")
            print("\n失败用例详情:")
            for fail in failed_issues:
                print(f"- {fail}")
        
        return created_issues
    except Exception as e:
        logging.error(f"导入流程异常: {e}")
        return []

def search_test_cases(jira, project_key, search_term=None):
    """在 Jira 中搜索测试用例"""
    jql = f'project = {project_key} AND issuetype = "Test Case"'
    if search_term:
        jql += f' AND summary ~ "{search_term}"'
    try:
        issues = jira.search_issues(jql)
        print(f"找到 {len(issues)} 个匹配的测试用例:")
        for issue in issues:
            print(f"- {issue.key}: {issue.fields.summary}")
        return issues
    except JIRAError as e:
        logging.error(f"搜索失败: {e.text}")
        return []

if __name__ == "__main__":
    # 配置参数
    jira_server = JIRA_SERVER 
    project_key = JIRA_PROJECT_KEY 
    
    # 启动Flask应用
    app.run(debug=True)
