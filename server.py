from flask import Flask, jsonify, request, send_from_directory
import json
import random
import datetime
import os
from log import log_info
import portalocker
from flask_cors import CORS
from flask import render_template
from llm_elo import calculate_elo_ratings
import uuid
import threading
import time
from urllib.parse import unquote
from log import log_info, log_error
import re
# --- DDoS Protection Imports ---
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import redis
# ------------------------------------

app = Flask(__name__)
CORS(app) # Keep CORS enabled

# # --- Rate Limiter Configuration ---
# # Make sure a Redis server is running (e.g., `redis-server`)
# # You might need to configure host/port/password if not default localhost
# # Example: redis://:password@hostname:port/db_number
# redis_url = "redis://localhost:6379/0" # Adjust if your Redis setup is different

# # Initialize Limiter
# # get_remote_address identifies users by their IP address.
# # storage_uri specifies where rate limit data is stored.
# # strategy='fixed-window' or 'moving-window' are common strategies.
# limiter = Limiter(
#     get_remote_address,
#     app=app,
#     default_limits=["200 per day", "50 per hour", "10 per minute"], # General limits for all routes
#     storage_uri=redis_url,
#     strategy="fixed-window" # Choose a strategy (fixed-window is simpler)
# )
# # ---------------------------------

model_files = {
    0: 'dataset/task1/GT.json',
    1: 'dataset/task1/deepseek_v3.json', 
    2: 'dataset/task1/deepseek_r1.json',
    3: 'dataset/task1/gpt_4o.json',
    4: 'dataset/task1/qwen_max.json',
    5: 'dataset/task1/qwen3_reason.json',
    6: 'dataset/task1/doubao_1p5_pro.json'
}


model_names_n = {
    0: 'Ground Truth',
    1: 'Deepseek-v3',
    2: 'Deepseek-r1', 
    3: 'GPT-4o',
    4: 'Qwen Max',
    5: 'Qwen3-Reason',
    6: 'Doubao-1.5-pro'
}

# 模型ID到名称的映射
model_names = {
    "0": 'Ground Truth',
    "1": 'Deepseek-v3',
    "2": 'Deepseek-r1', 
    "3": 'GPT-4o',
    "4": 'Qwen Max',
    "5": 'Qwen3-Reason',
    "6": 'Doubao-1.5-pro'
}

# 存储token和对应的模型信息
token_store = {}
# 用于清理过期token的锁
token_lock = threading.Lock()

def cleanup_expired_tokens():
    """清理过期的token"""
    while True:
        current_time = datetime.datetime.now()
        with token_lock:
            expired_tokens = [
                token for token, data in token_store.items()
                if (current_time - data['timestamp']).total_seconds() > 300  # 10分钟过期
            ]
            for token in expired_tokens:
                del token_store[token]
        time.sleep(60)  # 每分钟检查一次

# 启动清理线程
cleanup_thread = threading.Thread(target=cleanup_expired_tokens, daemon=True)
cleanup_thread.start()

@app.route('/favicon.ico')
def favicon():
    print("获取favicon.ico")
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico')

@app.route('/<path:filename>')
def serve_image(filename):
    """提供图片文件服务"""

    try:
        # 1. 解码URL
        decoded_path = unquote(filename)

        # 2. 解析绝对路径
        base_path = r'C:\Users\98750\Desktop\LLM-PPWB'
        available_path = r'C:\Users\98750\Desktop\LLM-PPWB\PPmd'
        abs_path = os.path.abspath(os.path.join(base_path, decoded_path))
        # 检查路径是否在允许的目录下
        if not abs_path.startswith(available_path):
            return jsonify({'error': '非法的文件访问路径'}), 403

        # 5. 获取实际的目录和文件名
        directory = os.path.dirname(abs_path)
        # print(directory)
        filename = os.path.basename(abs_path)
        # print(filename)
        # print("--------------------------------")

        if not os.path.exists(directory):
            # print("目录不存在")
            return jsonify({'error': '目录不存在'}), 404

        try:
            return send_from_directory(directory, filename)
        except Exception as e:
            log_error(f"发送文件失败: {str(e)}")
            return jsonify({'error': '文件发送失败'}), 500
        
    except Exception as e:
        return jsonify({'error': f'文件访问错误: {str(e)}'}), 404

@app.route('/index.md')
def index_md():
    """
    渲染主页面 index.md。
    """
    return render_template('index.md')

@app.route('/about_us.md')
def about_us_md():
    """
    渲染关于页面 about_us.md。
    """
    return render_template('about_us.md')

@app.route('/')
def index():
    """
    渲染主页面 index.html。
    我们可以在这里传递一些初始数据给模板。
    """
    # initial_question = random.choice(questions_db)
    # render_template 会自动在 templates 文件夹中查找 index.html
    # 并将 initial_question 变量传递给模板使用
    return render_template('index.html')

@app.route('/judge')
def judge():
    """
    渲染评价页面 judge.html。
    """
    return render_template('judge.html')

@app.route('/about')
def about():
    """
    渲染关于页面 about.html。
    """
    return render_template('about.html')

@app.route('/leaderboard')
def leaderboard():
    """
    渲染排行榜页面 leaderboard.html。
    我们可以在这里传递一些初始数据给模板。
    """
    return render_template('leaderboard.html')

def load_data():
    """加载问题和模型数据"""
    with open('dataset/task1/question.json', 'r', encoding='utf-8') as f:
        questions = json.load(f)

    model_answers = {}

    for model_id, file_path in model_files.items():
        with open(file_path, 'r', encoding='utf-8') as f:
            model_answers[model_id] = json.load(f)
            
    log_info("数据重新加载完成")
    return questions, model_answers

def get_summary(doc_id):
    with open('dataset/task1/document.json', 'r', encoding='utf-8') as f:
        documents = json.load(f)
    for document in documents:
        if document['id'] == doc_id:
            return document['abstract']

def get_title(doc_id):
    with open('dataset/task1/document.json', 'r', encoding='utf-8') as f:
        documents = json.load(f)
    for document in documents:
        if document['id'] == doc_id:
            match = re.search(r'\\([^\\]+)\.pdf',document['document'])
            if match:
                return match.group(1)
            else:
                return os.path.basename(document['document'])

def save_result(result):
    result_file = 'dataset/task1/result.json'
    
    # 如果文件不存在则创建
    if not os.path.exists(result_file):
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump([], f, ensure_ascii=False, indent=2)
    
    with open(result_file, 'r+', encoding='utf-8') as f:
        portalocker.lock(f, portalocker.LOCK_EX)
        try:
            results = json.load(f)
            results.append(result)
            f.seek(0)
            f.truncate()
            json.dump(results, f, ensure_ascii=False, indent=2)
        finally:
            portalocker.unlock(f)

def get_able_ids(domain):
    with open('dataset/task1/document.json', 'r', encoding='utf-8') as f:
        documents = json.load(f)
    return [document['id'] for document in documents if document['domain'] == domain]

@app.route('/get_question', methods=['GET'])
def get_question():
    global questions, model_answers
    questions, model_answers = load_data()
    
    domain = request.args.get('domain', 'all')
    if domain == 'ALL':
        question = random.choice(questions)
    else:
        able_doc = get_able_ids(domain)
        question = random.choice([q for q in questions if q['doc_id'] in able_doc])
    # question = questions[26]
    # 根据total_matches计算权重，匹配次数越少权重越大
    
    with open('dataset/task1/model_ratings.json', 'r', encoding='utf-8') as f:
        total_matches = json.load(f)['total_matches']
        
    weights = [1/total_matches[str(model_id)] for model_id in model_answers.keys()]
    # 归一化权重
    weights = [w/sum(weights) for w in weights]
    # 根据权重随机选择两个不同的模型
    model_ids = random.choices(list(model_answers.keys()), weights=weights, k=2)
    while model_ids[0] == model_ids[1]:  # 确保选择的两个模型不同
        model_ids = random.choices(list(model_answers.keys()), weights=weights, k=2)

    print(weights)
    print(f"选择模型id：{model_ids[0]}，{model_ids[1]}")

    answers = []
    for i, model_id in enumerate(model_ids):
        answer = next(item['answer'] for item in model_answers[model_id] if item['question_id'] == question['question_id'])
        answers.append({
            'id': i,
            'answer': answer
        })
    
    # 生成唯一token
    token = str(uuid.uuid4())
    
    # 存储token对应的信息
    with token_lock:
        token_store[token] = {
            'model_ids': model_ids,
            'timestamp': datetime.datetime.now()
        }
    
    response = jsonify({
        'question': question,
        'answers': answers,
        'summary': get_summary(question['doc_id']),
        'title': get_title(question['doc_id']),
        'token': token
    })
    response.charset = 'utf-8'
    return response

@app.route('/submit_choice', methods=['POST'])
def submit_choice():
    data = request.json
    token = data.get('token')
    
    if not token or token not in token_store:
        return jsonify({'error': '无效的token'}), 400
        
    token_data = token_store[token]
    
    if 'choice' not in data or data['choice'] == -1:
        with token_lock:
            del token_store[token]
        return jsonify({
            'message': '已记录弃权',
            'model_A': model_names_n[token_data['model_ids'][0]],
            'model_B': model_names_n[token_data['model_ids'][1]]
        })
    
    comparison_result = {
        'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'question_id': data['question_id'],
        'winner_model': token_data['model_ids'][data['choice']],
        'loser_model': token_data['model_ids'][1-data['choice']],
        'winner_answer': data['answers'][data['choice']]['answer'],
        'loser_answer': data['answers'][1-data['choice']]['answer'],
        'question_context': data.get('question', {})
    }
    
    save_result(comparison_result)
    
    # 删除已使用的token
    with token_lock:
        del token_store[token]
    
    return jsonify({
        'message': '提交成功',
        'model_A': model_names_n[token_data['model_ids'][0]],
        'model_B': model_names_n[token_data['model_ids'][1]]
    })

@app.route('/get_rating', methods=['GET'])
def get_rating():
    """获取所有模型的ELO评分
    
    Returns:
        JSON格式的评分结果，包含模型名称和对应的评分
    """
    try:
        # 调用calculate_elo_ratings计算评分
        result_file = 'dataset/task1/result.json'
        previous_ratings_file = 'dataset/task1/model_ratings.json'
        data = calculate_elo_ratings(result_file, previous_ratings_file)
        
        if not data:
            return jsonify({'error': '获取评分失败'}), 500
            
        
        # 构建评分结果
        ratings = []
        for model_id, rating in sorted(data['ratings'].items(), key=lambda x: x[1], reverse=True):
            ratings.append({
                'model': model_names.get(model_id),
                'rating': round(rating, 1)
            })
            
        # 构建胜率结果
        win_rates = []
        for model_id, rate in data['win_rates'].items():
            win_rates.append({
                'model': model_names.get(model_id),
                'rate': round(rate * 100, 1)  # 转换为百分比
            })
            
        # 构建对位矩阵结果
        matchup_matrix = {}
        for model_id, matchups in data['matchup_matrix'].items():
            model_name = model_names.get(model_id)
            matchup_matrix[model_name] = {}
            for opponent_id, wins in matchups.items():
                opponent_name = model_names.get(opponent_id)
                matchup_matrix[model_name][opponent_name] = wins
            
        return jsonify(ratings)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/get_winrates', methods=['GET'])
def get_winrates():
    """获取所有模型的胜率
    
    Returns:
        JSON格式的胜率结果，包含模型名称和对应的胜率
    """
    try:
        # 调用calculate_elo_ratings计算胜率
        result_file = 'dataset/task1/result.json'
        previous_ratings_file = 'dataset/task1/model_ratings.json'
        data = calculate_elo_ratings(result_file, previous_ratings_file)
        
        if not data:
            return jsonify({'error': '获取胜率失败'}), 500
        
        # 构建评分结果
        ratings = []
        for model_id, rating in sorted(data['ratings'].items(), key=lambda x: x[1], reverse=True):
            ratings.append({
                'model': model_names.get(model_id),
                'rating': round(rating, 1)
            })
            
        # 构建胜率结果
        win_rates = []
        for model_id, rate in data['win_rates'].items():
            win_rates.append({
                'model': model_names.get(model_id),
                'rate': round(rate * 100, 1)  # 转换为百分比
            })
            
        # 构建对位矩阵结果
        matchup_matrix = {}
        for model_id, matchups in data['matchup_matrix'].items():
            model_name = model_names.get(model_id)
            matchup_matrix[model_name] = {}
            for opponent_id, wins in matchups.items():
                opponent_name = model_names.get(opponent_id)
                matchup_matrix[model_name][opponent_name] = wins
            
        return jsonify(win_rates)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/get_matrix', methods=['GET'])
def get_matrix():
    """获取所有模型的对位矩阵
    
    Returns:
        JSON格式的对位矩阵结果，包含模型名称和对应的胜率
    """
    try:
        # 调用calculate_elo_ratings计算胜率
        result_file = 'dataset/task1/result.json'
        previous_ratings_file = 'dataset/task1/model_ratings.json'
        data = calculate_elo_ratings(result_file, previous_ratings_file)
        
        if not data:
            return jsonify({'error': '获取对位矩阵失败'}), 500
        
        # 构建评分结果
        ratings = []
        for model_id, rating in sorted(data['ratings'].items(), key=lambda x: x[1], reverse=True):
            ratings.append({
                'model': model_names.get(model_id),
                'rating': round(rating, 1)
            })
            
        # 构建胜率结果
        win_rates = []
        for model_id, rate in data['win_rates'].items():
            win_rates.append({
                'model': model_names.get(model_id),
                'rate': round(rate * 100, 1)  # 转换为百分比
            })
            
        # 构建对位矩阵结果
        matchup_matrix = {}
        for model_id, matchups in data['matchup_matrix'].items():
            model_name = model_names.get(model_id)
            matchup_matrix[model_name] = {}
            for opponent_id, wins in matchups.items():
                opponent_name = model_names.get(opponent_id)
                matchup_matrix[model_name][opponent_name] = wins
            
        return jsonify(matchup_matrix)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
