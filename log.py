import os
from datetime import datetime

def log_message(message):
    """将日志消息写入log.txt文件
    
    Args:
        message: 要记录的日志消息
    """
    # 确保log目录存在
    os.makedirs('log', exist_ok=True)
    
    # 获取当前时间
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # 将日志写入文件
    with open(os.path.join('log', 'log.txt'), 'a', encoding='utf-8') as f:
        f.write(f'[{current_time}] {message}\n')

def log_error(error):
    """记录错误信息到log.txt
    
    Args:
        error: 错误信息或异常对象
    """
    log_message(f'ERROR: {str(error)}')

def log_warning(warning):
    """记录警告信息到log.txt
    
    Args:
        warning: 警告信息
    """
    log_message(f'WARNING: {warning}')

def log_info(info):
    """记录一般信息到log.txt
    
    Args:
        info: 一般信息
    """
    log_message(f'INFO: {info}')
