from jira import JIRA
from jira.exceptions import JIRAError

def verify_jira_connection(jira_url, username, api_token):
    """
    验证JIRA服务器连接
    
    Args:
        jira_url: JIRA服务器URL
        username: JIRA用户名
        api_token: JIRA API令牌或密码
    
    Returns:
        tuple: (bool, str) - (是否连接成功, 错误信息)
    """
    try:
        # 尝试建立JIRA连接
        JIRA(
            server=jira_url,
            basic_auth=(username, api_token)
        )
        return True, "连接成功"
    except JIRAError as e:
        # 处理JIRA连接错误
        if e.status_code == 401:
            return False, "认证失败：用户名或密码错误"
        elif e.status_code == 404:
            return False, f"无法访问JIRA服务器：{jira_url}"
        else:
            return False, f"连接失败：{str(e)}"
    except Exception as e:
        # 处理其他可能的错误
        return False, f"发生未知错误：{str(e)}"

def search_jira_issues(jira_url, username, api_token, jql_query):
    """
    搜索JIRA issues
    
    Args:
        jira_url: JIRA服务器URL
        username: JIRA用户名
        api_token: JIRA API令牌或密码
        jql_query: JQL查询语句
    
    Returns:
        tuple: (bool, list/str) - (是否查询成功, issues列表或错误信息)
    """
    try:
        # 建立JIRA连接
        jira = JIRA(
            server=jira_url,
            basic_auth=(username, api_token)
        )
        
        # 执行JQL查询，限制返回前n条结果
        issues = jira.search_issues(jql_query, maxResults=3)
        # 格式化查询结果
        results = []
        for issue in issues:
            if hasattr(issue.fields, 'customfield_10411') and hasattr(issue.fields.customfield_10411, 'steps') and len(issue.fields.customfield_10411.steps) > 0:
                issue_dict = {
                'key': issue.key,
                'summary': issue.fields.summary,
                'issuetype': issue.fields.issuetype.name,
                'priority': issue.fields.priority.name,
                'project key': issue.fields.project.key,
                'project name': issue.fields.project.name,
                'Action': issue.fields.customfield_10411.steps[0].fields.Action,
                'Data': issue.fields.customfield_10411.steps[0].fields.Data,
                'Expected Result': getattr(issue.fields.customfield_10411.steps[0].fields, 'Expected Result', None),
                'labels': issue.fields.labels,
                'reporter': issue.fields.reporter.displayName if issue.fields.reporter else 'Unassigned',
                'assignee': issue.fields.assignee.displayName if issue.fields.assignee else 'Unassigned',
                'priority': issue.fields.priority.name
            }   
            else:
                issue_dict = {
                'key': issue.key,
                'summary': issue.fields.summary,
                'issuetype': issue.fields.issuetype.name,
                'priority': issue.fields.priority.name,
                'project key': issue.fields.project.key,
                'project name': issue.fields.project.name,
                'Action': None,
                'Data': None,
                'Expected Result': None,
                'labels': issue.fields.labels,
                'reporter': issue.fields.reporter.displayName if issue.fields.reporter else 'Unassigned',
                'assignee': issue.fields.assignee.displayName if issue.fields.assignee else 'Unassigned',
                'priority': issue.fields.priority.name
            }   
            
            results.append(issue_dict)
        return True, results
        
    except JIRAError as e:
        return False, f"JIRA查询失败：{str(e)}"
    except Exception as e:
        return False, f"发生未知错误：{str(e)}"

# 使用示例
if __name__ == "__main__":
    jira_url = "https://jira.datatist.cn"
    username = "lori.che"
    api_token = "bSN0esNYIbOqrCQMClI0zepH6gYiM4j1kKw"
    
    # success, message = verify_jira_connection(jira_url, username, api_token)
    # if success:
    #     print("JIRA连接测试成功！")
    # else:
    #     print(f"JIRA连接测试失败：{message}")
    
    # 测试查询功能
    jql_query = 'project = "XRAY1" ORDER BY created DESC'
    success, result = search_jira_issues(jira_url, username, api_token, jql_query)
    if success:
        print("\nJIRA查询结果：")
        for issue in result:
            print(f"Issue Key: {issue['key']}")
            print(f"Summary: {issue['summary']}")
            print(f"issuetype: {issue['issuetype']}")
            print(f"priority: {issue['priority']}")
            print(f"project key: {issue['project key']}")
            print(f"project name: {issue['project name']}")
            print(f"reporter: {issue['reporter']}")
            print(f"Assignee: {issue['assignee']}")
            print(f"Action: {issue['Action']}")
            print(f"Data: {issue['Data']}")
            print(f"Expected Result: {issue['Expected Result']}")
            print(f"labels: {issue['labels']}")
            print(f"priority: {issue['priority']}")
            print("-" * 50)
    else:
        print(f"查询失败：{result}")

