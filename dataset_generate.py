import re
import os
import random
import json
from log import log_info,log_warning
import toml
import openai

def get_domain(path):
    """从md文件中提取领域信息
    
    Args:
        md_path: md文件路径
    """
    # print(path)
    # 获取目录部分
    dir_path = os.path.dirname(path)
    # print(dir_path)  # 输出：/PPmd/AI/基于中文知识图谱的胸部主要疾病人工智能筛查多中心研究.pdf-96dd7bd3-9143-427b-a959-68b9f6d481f5

    # 将目录路径按 '/' 分割成列表
    dir_parts = dir_path.replace('\\', '/').split('/')
    # print(dir_parts)  # 输出：['', 'PPmd', 'AI', '基于中文知识图谱的胸部主要疾病人工智能筛查多中心研究.pdf-96dd7bd3-9143-427b-a959-68b9f6d481f5']

    # 获取第二个文件夹名称
    second_folder = dir_parts[1]
    return second_folder

def extract_text_from_md(md_path):
    """从md文件中提取文本并生成训练样本
    
    Args:
        md_path: md文件路径
        
    Returns:
        dict: 包含上文、GT和下文的字典,如果无法提取合适样本则返回None
    """
    n_sample = 10
    gt_min = 3
    gt_max = 5
    
    # 检查document.json文件是否存在,不存在则创建
    doc_json_path = os.path.join('dataset', 'task1', 'document.json')
    os.makedirs(os.path.dirname(doc_json_path), exist_ok=True)
    
    import json
    doc_id = None
    
    # 读取document.json
    if os.path.exists(doc_json_path):
        with open(doc_json_path, 'r', encoding='utf-8') as f:
            try:
                doc_data = json.load(f)
            except json.JSONDecodeError:
                doc_data = []
    else:
        doc_data = []
        
    # 检查文件是否已存在
    for doc in doc_data:
        if doc['document'] == md_path:
            doc_id = doc['id']
            break
            
    # 如果文件不存在,生成新ID
    if doc_id is None:
        existing_ids = set(doc['id'] for doc in doc_data)
        doc_id = 1
        while doc_id in existing_ids:
            doc_id += 1
            
        # 获取领域信息
        domain = get_domain(md_path)
        
        # 读取md文件获取摘要
        with open(md_path, 'r', encoding='utf-8') as f:
            content = f.read()
            # 查找中文摘要部分
            abstract_match = re.search(r'# 中文摘要：\s*\n(.*?)(?=\n#)', content, re.DOTALL)
            abstract = abstract_match.group(1).strip() if abstract_match else ""
            
        # 添加新文档记录    
        doc_data.append({
            'document': md_path,
            'id': doc_id,
            'domain': domain,
            'abstract': abstract
        })
        # 保存更新后的document.json
        with open(doc_json_path, 'w', encoding='utf-8') as f:
            json.dump(doc_data, f, ensure_ascii=False, indent=2)

    # 读取md文件
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 分句
    sentences = re.split(r'[。！？]', content)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 0]
    
    if len(sentences) < n_sample:  # 确保有足够的句子
        return None
        
    # 随机选择一个起始位置,确保能够提取足够的句子
    max_attempts = 50  # 最大尝试次数
    for _ in range(max_attempts):
        start_idx = random.randint(0, len(sentences) - n_sample)
        
        # 提取连续的句子作为样本
        sample_sentences = sentences[start_idx:start_idx + n_sample]
        sample_text = '。'.join(sample_sentences) + '。'
        
        # 检查样本长度区间
        if 300 <= len(sample_text) <= 1000:
            # 随机选择3-5个连续句子作为GT
            gt_length = random.randint(gt_min, gt_max)
            gt_start = random.randint(0, len(sample_sentences) - gt_length)
            gt_sentences = sample_sentences[gt_start:gt_start + gt_length]
            
            # 构建上文、GT和下文
            context_before = '。'.join(sample_sentences[:gt_start]) + '。' if gt_start > 0 else ''
            ground_truth = '。'.join(gt_sentences) + '。'
            context_after = '。'.join(sample_sentences[gt_start + gt_length:]) + '。' if gt_start + gt_length < len(sample_sentences) else ''
            
            # 检查ground_truth是否包含图片
            if '![' in ground_truth or '](' in ground_truth:
                continue
                
            # 处理context_before和context_after中的图片路径
            def process_image_paths(text, md_dir):
                if '![' not in text or '](' not in text:
                    return text
                    
                # 提取图片路径
                pattern = r'!\[.*?\]\((.*?)\)'
                matches = re.finditer(pattern, text)
                
                for match in matches:
                    img_path = match.group(1)
                    # 将相对路径转换为基于项目根目录的路径
                    abs_img_path = os.path.normpath(os.path.join(md_dir, img_path))
                    rel_img_path = os.path.relpath(abs_img_path)
                    # 替换原路径
                    text = text.replace(img_path, rel_img_path)
                    
                return text
            
            md_dir = os.path.dirname(md_path)
            context_before = process_image_paths(context_before, md_dir)
            context_after = process_image_paths(context_after, md_dir)
            
            # 记录样本字符数
            sample_info = {
                'context_before': context_before,
                'ground_truth': ground_truth,
                'context_after': context_after,
                'doc_id': doc_id,
                'answer': ground_truth,
                'char_count': {
                    'context_before': len(context_before),
                    'ground_truth': len(ground_truth),
                    'context_after': len(context_after),
                    'total': len(context_before) + len(ground_truth) + len(context_after)
                }
            }
            
            return sample_info
    
    return None  # 如果多次尝试都未找到合适的样本则返回None

def generate_query(context_before, context_after, ground_truth):
    """使用deepseek-v3生成query
    
    Args:
        context_before: 上文
        ground_truth: 原文中间内容
        context_after: 下文
        
    Returns:
        str: 生成的query
    """
    # 读取配置文件
    
    with open('config.toml', 'r', encoding='utf-8') as f:
        config = toml.load(f)
    
    llm_config = config['LLM query generate']
    
    # 构建请求    
    openai.api_key = llm_config["api-key"]
    openai.base_url = llm_config["api"]
    
    try:
        response = openai.chat.completions.create(
            model=llm_config['model'],
            messages=[
                {
                    "role": "user",
                    "content": f'上文:{context_before}\n中间内容:{ground_truth}\n下文:{context_after}\n你是一个prompt工程师，请生成一个问题,能够让其他大模型在只知道上文和下文的情况下补全得出中间内容。'
                }
            ]
        )
        query = response.choices[0].message.content
        return query
    except Exception as e:
        # 如果API调用失败,返回默认query
        log_warning(f"API调用失败: {str(e)}")
        return "请根据上下文补全缺失的内容。"


def generate_dataset(n_per_file=5):
    """遍历PPmd文件夹生成训练数据集
    
    Args:
        n_per_file: 每个文件生成的样本数量
    """
    # 创建输出目录
    os.makedirs(os.path.join('dataset', 'task1'), exist_ok=True)
    
    # 读取已有的question.json和GT.json
    question_json_path = os.path.join('dataset', 'task1', 'question.json')
    gt_json_path = os.path.join('dataset', 'task1', 'GT.json')
    
    questions = []
    ground_truths = []
    
    if os.path.exists(question_json_path):
        with open(question_json_path, 'r', encoding='utf-8') as f:
            try:
                questions = json.load(f)
            except json.JSONDecodeError:
                questions = []
                
    if os.path.exists(gt_json_path):
        with open(gt_json_path, 'r', encoding='utf-8') as f:
            try:
                ground_truths = json.load(f)
            except json.JSONDecodeError:
                ground_truths = []
    
    # 获取已有的question_id
    existing_qids = set(q['question_id'] for q in questions)
    next_qid = max(existing_qids) + 1 if existing_qids else 1
    
    # 遍历PPmd文件夹下所有md文件
    for root, dirs, files in os.walk('PPmd'):
        for file in files:
            if file.endswith('.md'):
                md_path = os.path.join(root, file)
                
                # 检查document.json中是否已存在该文件
                doc_json_path = os.path.join('dataset', 'task1', 'document.json')
                if os.path.exists(doc_json_path):
                    with open(doc_json_path, 'r', encoding='utf-8') as f:
                        doc_data = json.load(f)
                        if any(doc['document'] == md_path for doc in doc_data):
                            log_info(f"文档 {md_path} 已存在于document.json中,跳过处理")
                            continue
                       
                # 对每个文件生成n_per_file个样本
                for _ in range(n_per_file):
                    result = extract_text_from_md(md_path)
                    
                    if result:
                        # 生成query
                        query = generate_query(result['context_before'], result['context_after'],result['ground_truth'])
                        
                        # 构建question记录
                        question = {
                            'question_id': next_qid,
                            'doc_id': result['doc_id'],
                            'context_before': result['context_before'],
                            'context_after': result['context_after'],
                            'char_count': result['char_count'],
                            'query': query
                        }
                        questions.append(question)
                        
                        # 构建GT记录
                        ground_truth = {
                            'question_id': next_qid,
                            'ground_truth': result['ground_truth'],
                            'doc_id': result['doc_id'],
                            'context_before': result['context_before'],
                            'context_after': result['context_after'],
                            'char_count': result['char_count'],
                            'answer': result['answer'],
                            'query': query
                        }
                        ground_truths.append(ground_truth)
                        
                        next_qid += 1
    
    # 保存question.json
    with open(question_json_path, 'w', encoding='utf-8') as f:
        json.dump(questions, f, ensure_ascii=False, indent=2)
        
    # 保存GT.json
    with open(gt_json_path, 'w', encoding='utf-8') as f:
        json.dump(ground_truths, f, ensure_ascii=False, indent=2)


# 测试代码

def run():
    # 测试数据集生成
    generate_dataset(n_per_file=10)
    
    # 检查生成的文件
    question_json_path = os.path.join('dataset', 'task1', 'question.json')
    gt_json_path = os.path.join('dataset', 'task1', 'GT.json')
    
    if os.path.exists(question_json_path) and os.path.exists(gt_json_path):
        print("数据集生成成功!")
        
        # 读取并打印部分内容
        with open(question_json_path, 'r', encoding='utf-8') as f:
            questions = json.load(f)
            print(f"\n共生成问题数: {len(questions)}")
            if questions:
                print("\n示例问题:")
                print(json.dumps(questions[0], ensure_ascii=False, indent=2))
                
        with open(gt_json_path, 'r', encoding='utf-8') as f:
            ground_truths = json.load(f)
            print(f"\n共生成答案数: {len(ground_truths)}")
            if ground_truths:
                print("\n示例答案:")
                print(json.dumps(ground_truths[0], ensure_ascii=False, indent=2))
    else:
        print("数据集生成失败")

if __name__ == "__main__":
    # print(extract_text_from_md('PPmd/AI/基于中文知识图谱的胸部主要疾病人工智能筛查多中心研究.pdf-96dd7bd3-9143-427b-a959-68b9f6d481f5/full.md'))
    run()