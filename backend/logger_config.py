import logging
import os
from datetime import datetime

# 定义日志路径（日志存在项目根目录，不上传 Git）
LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'logs')
os.makedirs(LOG_DIR, exist_ok=True)

# 日志文件路径
LOG_FILE = os.path.join(LOG_DIR, f'app_{datetime.now().strftime("%Y%m%d")}.log')

# 日志格式
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

# 创建日志配置
def setup_logger(name='app', level=logging.INFO):
    """
    设置并返回配置好的日志记录器
    
    Args:
        name: 日志记录器名称
        level: 日志级别
        
    Returns:
        logging.Logger: 配置好的日志记录器
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # 避免重复添加处理器
    if logger.handlers:
        return logger
    
    # 控制台处理器 - 输出到控制台
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # 文件处理器 - 输出到文件
    file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
    file_handler.setLevel(level)
    file_formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    return logger

# 创建默认日志记录器
logger = setup_logger()

def log_request(logger, endpoint, method, data=None, params=None):
    """
    记录请求信息
    
    Args:
        logger: 日志记录器
        endpoint: API 端点
        method: HTTP 方法
        data: 请求体数据
        params: URL 参数
    """
    logger.info(f"【请求】{method} {endpoint}")
    if params:
        logger.info(f"【参数】{params}")
    if data:
        # 过滤敏感信息
        filtered_data = filter_sensitive_data(data)
        logger.info(f"【数据】{filtered_data}")

def log_response(logger, endpoint, success, message=None, data=None):
    """
    记录响应信息
    
    Args:
        logger: 日志记录器
        endpoint: API 端点
        success: 是否成功
        message: 响应消息
        data: 响应数据
    """
    status = "成功" if success else "失败"
    logger.info(f"【响应】{endpoint} - {status}")
    if message:
        logger.info(f"【消息】{message}")
    if data and success:
        logger.debug(f"【数据】{data}")

def log_error(logger, endpoint, error, exc_info=None):
    """
    记录错误信息
    
    Args:
        logger: 日志记录器
        endpoint: API 端点
        error: 错误信息
        exc_info: 异常信息
    """
    logger.error(f"【错误】{endpoint} - {error}", exc_info=exc_info)

def log_db_operation(logger, operation, table, data=None, condition=None):
    """
    记录数据库操作
    
    Args:
        logger: 日志记录器
        operation: 操作类型 (INSERT/UPDATE/DELETE/SELECT)
        table: 表名
        data: 操作数据
        condition: 查询条件
    """
    logger.info(f"【数据库】{operation} {table}")
    if data:
        logger.info(f"【数据】{data}")
    if condition:
        logger.info(f"【条件】{condition}")

def log_price_update(logger, project_name, material, old_price, new_price, update_method='auto'):
    """
    记录价格更新
    
    Args:
        logger: 日志记录器
        project_name: 项目名称
        material: 材质
        old_price: 旧价格
        new_price: 新价格
        update_method: 更新方式
    """
    logger.info(f"【价格更新】{project_name} - {material}")
    logger.info(f"【旧价格】{old_price} -> 【新价格】{new_price}")
    logger.info(f"【更新方式】{update_method}")

def filter_sensitive_data(data):
    """
    过滤敏感信息
    
    Args:
        data: 原始数据
        
    Returns:
        dict: 过滤后的数据
    """
    if not isinstance(data, dict):
        return data
    
    sensitive_fields = ['password', 'token', 'secret', 'key']
    filtered = {}
    for key, value in data.items():
        if any(field in key.lower() for field in sensitive_fields):
            filtered[key] = '***'
        else:
            filtered[key] = value
    return filtered
