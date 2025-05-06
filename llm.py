import toml
import openai
import os
import json
from tqdm import tqdm
# 读取配置文件
with open('config.toml', 'r') as f:
    config = toml.load(f)

def generate_prompt(query, context_before, context_after, gt_length):
    """生成用于补全上下文缺失内容的prompt
    
    Args:
        query: 问题描述和对缺失内容的概括
        context_before: 上文内容
        context_after: 下文内容
        
    Returns:
        str: 生成的prompt
    """
    prompt = f"""
请根据以下上下文补全缺失的内容:

上文:
{context_before}
下文:
{context_after}
内容要求:
{query}

请生成上下文之间缺失的内容,要求:
1. 内容要与上下文自然衔接,保持连贯性
2. 使用自然、专业的中文进行回答
3. 使用与上下文一致的专业术语和表达方式，公式，特殊字符等特殊格式使用markdown格式
4. 生成内容长度应在3-5句话，字符数：{str(int(0.8*gt_length/10)*10)}-{str(int(1.2*gt_length/10)*10)}个字符（包括标点符号，换行符等）
5. 如果上下文包含图片引用，请自行脑补图片内容
6. 不要包含其他说明

请直接输出补全的内容,不要包含任何额外说明。
"""
    return prompt

def call_deepseek_v3(prompt):
    """调用deepseek-v3模型
    
    Args:
        prompt: 输入提示
        
    Returns:
        str: 模型返回的文本
    """
    settings = config["deepseek-v3 setting"]
    openai.api_key = settings["api-key"]
    openai.base_url = settings["api"]
    
    response = openai.chat.completions.create(
        model="deepseek-v3",
        messages=[{"role": "user", "content": prompt}]
    )
    
    return response.choices[0].message.content

def call_gpt_4o(prompt):
    """调用gpt-4o模型
    
    Args:
        prompt: 输入提示
        
    Returns:
        str: 模型返回的文本
    """
    settings = config["gpt-4o setting"]
    openai.api_key = settings["api-key"]
    openai.base_url = settings["api"]
    
    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )
    
    return response.choices[0].message.content

def call_deepseek_r1(prompt):
    """调用deepseek-r1模型
    
    Args:
        prompt: 输入提示
        
    Returns:
        str: 模型返回的文本
        str: 模型返回的推理内容
    """
    settings = config["deepseek-r1 setting"]
    openai.api_key = settings["api-key"]
    openai.base_url = settings["api"]
    
    response = openai.chat.completions.create(
        model="deepseek-r1",
        messages=[{"role": "user", "content": prompt}]
    )
    
    return response.choices[0].message.content, response.choices[0].message.reasoning_content

def call_qwen_max(prompt):
    """调用qwen-max-latest模型
    
    Args:
        prompt: 输入提示
        
    Returns:
        str: 模型返回的文本
    """
    settings = config["qwen-max setting"]
    openai.api_key = settings["api-key"]
    openai.base_url = settings["api"]
    
    response = openai.chat.completions.create(
        model="qwen-max-latest",
        messages=[{"role": "user", "content": prompt}]
    )
    
    return response.choices[0].message.content

def call_doubao_1p5_pro(prompt):
    """调用doubao-1.5-pro模型
    
    Args:
        prompt: 输入提示

    Returns:
        str: 模型返回的文本
    """
    settings = config["Doubao-1.5-pro setting"]
    client = openai.OpenAI(
        base_url=settings["api"],
        api_key=settings["api-key"],
    )
    # print("start")
    completion = client.chat.completions.create(
        model="Doubao-1.5-pro-32k", 
        messages=[
            {
            "role": "user",
            "content": prompt
            }
        ]
    )
    # print("end")
    return completion.choices[0].message.content

def call_qwen3_reason(prompt):
    """调用qwen3-reason模型
    
    Args:
        prompt: 输入提示
        
    Returns:
        str: 模型返回的文本
        str: 模型返回的推理内容
    """
    settings = config["qwen3-reason setting"]

    # 初始化OpenAI客户端
    client = openai.OpenAI(
        # 如果没有配置环境变量，请用百炼API Key替换：api_key="sk-xxx"
        api_key=settings["api-key"],
        base_url=settings["api"],
    )

    messages = [{"role": "user", "content": prompt}]

    completion = client.chat.completions.create(
        model="qwen3-235b-a22b",  # 您可以按需更换为其它深度思考模型
        messages=messages,
        # enable_thinking 参数开启思考过程，QwQ 与 DeepSeek-R1 模型总会进行思考，不支持该参数
        extra_body={"enable_thinking": True},
        stream=True,
        # stream_options={
        #     "include_usage": True
        # },
    )

    reasoning_content = ""  # 完整思考过程
    answer_content = ""  # 完整回复
    is_answering = False  # 是否进入回复阶段
    print("\n" + "=" * 20 + "思考过程" + "=" * 20 + "\n")

    for chunk in completion:
        if not chunk.choices:
            print("\nUsage:")
            print(chunk.usage)
            continue

        delta = chunk.choices[0].delta

        # 只收集思考内容
        if hasattr(delta, "reasoning_content") and delta.reasoning_content is not None:
            if not is_answering:
                print(delta.reasoning_content, end="", flush=True)
            reasoning_content += delta.reasoning_content

        # 收到content，开始进行回复
        if hasattr(delta, "content") and delta.content:
            if not is_answering:
                print("\n" + "=" * 20 + "完整回复" + "=" * 20 + "\n")
                is_answering = True
            print(delta.content, end="", flush=True)
            answer_content += delta.content

    return answer_content[0], reasoning_content[0]

def answer_questions(model_func, json_path):
    """处理问题集并调用指定模型生成答案
    
    Args:
        model_func: 调用大模型的函数
        json_path: 问题json文件路径
    """
    # 获取模型名称
    model_name = model_func.__name__.replace('call_', '')
    
    # 读取问题json
    with open(json_path, 'r', encoding='utf-8') as f:
        questions = json.load(f)
        
    # 构建结果文件路径
    result_path = os.path.join(os.path.dirname(json_path), f'{model_name}.json')
    
    # 读取已有结果(如果存在)
    existing_results = {}
    if os.path.exists(result_path):
        with open(result_path, 'r', encoding='utf-8') as f:
            existing_results = {item['question_id']: item for item in json.load(f)}
    # 处理每个问题
    results = []
    for q in tqdm(questions, desc=f"{model_name}处理问题中", ncols=100):
        # 如果已经生成过答案则跳过
        
        reasoning_model = ["deepseek_r1", "qwen3_reason"]

        if q['question_id'] in existing_results:
            results.append(existing_results[q['question_id']])
            continue
            
        # 生成prompt并调用模型
        prompt = generate_prompt(
            q['query'],
            q['context_before'],
            q['context_after'],
            q['char_count']['ground_truth']
        )
        

        if model_name in reasoning_model:
            answer, reasoning = model_func(prompt)
            result = {
                'question_id': q['question_id'],
                'doc_id': q['doc_id'], 
                'query': q['query'],
                'context_before': q['context_before'],
                'context_after': q['context_after'],
                'answer': answer,
                'answer_length': len(answer),
                'reasoning': reasoning
            }
        else:# 保存结果
            answer = model_func(prompt)
            result = {
                'question_id': q['question_id'],
                'doc_id': q['doc_id'], 
                'query': q['query'],
                'context_before': q['context_before'],
                'context_after': q['context_after'],
                'answer': answer,
                'answer_length': len(answer)
            }
        results.append(result)
        
    # 保存所有结果
    with open(result_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

if __name__=="__main__":
    # answer_questions(call_deepseek_v3,"dataset\\task1\\question.json")
    # answer_questions(call_deepseek_r1,"dataset\\task1\\question.json")
    # answer_questions(call_qwen_max,"dataset\\task1\\question.json")
    # answer_questions(call_gpt_4o,"dataset\\task1\\question.json")
    # answer_questions(call_qwen3_reason,"dataset\\task1\\question.json")
    # answer_questions(call_doubao_1p5_pro,"dataset\\task1\\question.json")
    answer, reasoning = call_qwen3_reason("你好，很高兴认识你")
