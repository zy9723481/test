import requests

# 测试项目列表接口
url = 'http://localhost:5000/api/items?name=水暖'
try:
    response = requests.get(url)
    print('状态码:', response.status_code)
    print('响应内容:', response.json())
except Exception as e:
    print('错误:', str(e))
