import json
import os
from log import log_info, log_error

def calculate_elo_ratings(result_file, previous_ratings_file=None):
    """计算模型的ELO评分、胜率和对位胜场矩阵
    
    Args:
        result_file: 对战结果文件路径
        previous_ratings_file: 之前的评分文件路径，如果存在则基于之前的评分继续计算
        
    Returns:
        dict: 包含以下信息的字典:
            - ratings: 模型ELO评分
            - win_rates: 模型胜率
            - matchup_matrix: 模型对位胜场矩阵
    """
    try:
        # 读取对战结果
        with open(result_file, 'r', encoding='utf-8') as f:
            results = json.load(f)
            
        # 初始化数据
        model_ratings = {}
        win_counts = {}  # 记录每个模型的胜场数
        total_matches = {}  # 记录每个模型的总场次
        matchup_matrix = {}  # 记录模型对位胜场矩阵
        latest_timestamp = None
        K = 8  # ELO评分系统的K因子
        
        # 如果存在之前的评分文件，则加载之前的评分和最新时间戳
        if previous_ratings_file and os.path.exists(previous_ratings_file):
            with open(previous_ratings_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                model_ratings = dict(data.get('ratings', {}))
                win_counts = dict(data.get('win_counts', {}))
                total_matches = dict(data.get('total_matches', {}))
                matchup_matrix = dict(data.get('matchup_matrix', {}))
                latest_timestamp = data.get('latest_timestamp')
            
            # 过滤掉已处理过的对战结果
            if latest_timestamp:
                results = [r for r in results if r.get('timestamp', '') > latest_timestamp]

        # 处理每场对战
        for result in results:
            winner_model = str(result['winner_model'])
            loser_model = str(result['loser_model'])
            
            # 初始化模型数据(如果不存在)
            for model in [winner_model, loser_model]:
                if model not in model_ratings:
                    model_ratings[model] = 1500
                if model not in win_counts:
                    win_counts[model] = 0
                if model not in total_matches:
                    total_matches[model] = 0
                if model not in matchup_matrix:
                    matchup_matrix[model] = {}
            if loser_model not in matchup_matrix[winner_model]:
                matchup_matrix[winner_model][loser_model] = 0
            if winner_model not in matchup_matrix[loser_model]:
                matchup_matrix[loser_model][winner_model] = 0
                
            # 更新胜场数和总场次
            win_counts[winner_model] += 1
            total_matches[winner_model] += 1
            total_matches[loser_model] += 1
            
            # 更新对位胜场矩阵
            matchup_matrix[winner_model][loser_model] += 1
                
            # 计算期望胜率
            r1 = model_ratings[winner_model]
            r2 = model_ratings[loser_model]
            e1 = 1 / (1 + 10 ** ((r2 - r1) / 400))
            e2 = 1 / (1 + 10 ** ((r1 - r2) / 400))
            
            # 更新评分
            model_ratings[winner_model] = r1 + K * (1 - e1)
            model_ratings[loser_model] = r2 + K * (0 - e2)
            
            # 更新最新时间戳
            if 'timestamp' in result:
                if not latest_timestamp or result['timestamp'] > latest_timestamp:
                    latest_timestamp = result['timestamp']
        
        # print("_ _______________________")

        # 计算胜率
        win_rates = {}
        for model in model_ratings:
            win_rates[model] = win_counts[model] / total_matches[model] if total_matches[model] > 0 else 0
                
        # 保存结果
        ratings_file = os.path.join(os.path.dirname(result_file), 'model_ratings.json')
        with open(ratings_file, 'w', encoding='utf-8') as f:
            json.dump({
                'ratings': model_ratings,
                'win_rates': win_rates,
                'matchup_matrix': matchup_matrix,
                'win_counts': win_counts,
                'total_matches': total_matches,
                'latest_timestamp': latest_timestamp
            }, f, ensure_ascii=False, indent=2)
            
        log_info(f'已更新模型评分数据，结果保存至: {ratings_file}')
        return {
            'ratings': model_ratings,
            'win_rates': win_rates,
            'matchup_matrix': matchup_matrix
        }
        
    except Exception as e:
        log_error(f'计算模型评分数据时出错: {str(e)}')
        return None

if __name__ == '__main__':
    result_file = 'dataset/task1/result.json'
    previous_ratings_file = 'dataset/task1/model_ratings.json'
    ratings = calculate_elo_ratings(result_file, previous_ratings_file)['ratings']
    if ratings:
        print('模型评分:')
        for model, rating in sorted(ratings.items(), key=lambda x: x[1], reverse=True):
            print(f'{model}: {rating:.1f}')
