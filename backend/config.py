import os

# 数据库配置
DB_HOST = os.environ.get('DB_HOST', '101.42.35.88')
DB_USER = os.environ.get('DB_USER', 'xiaoshouxitong')
DB_PASSWORD = os.environ.get('DB_PASSWORD', '55p3knrBYPs8XJew')
DB_NAME = os.environ.get('DB_NAME', 'xiaoshouxitong')

# 应用配置
SECRET_KEY = os.environ.get('SECRET_KEY', 'dev_key')

# 应用运行配置
HOST = os.environ.get('HOST', '0.0.0.0')
PORT = int(os.environ.get('PORT', '5000'))
