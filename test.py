import requests
import json

def test_get_question():
    """测试获取问题接口"""
    response = requests.get('http://localhost:5000/get_question')
    
    # 检查响应状态码
    assert response.status_code == 200
    
    # 检查返回的JSON数据结构
    data = response.json()
    assert 'question' in data
    assert 'answers' in data
    assert 'model_ids' in data
    
    # 检查answers数组长度为2
    assert len(data['answers']) == 2
    
    # 检查每个answer的结构
    for answer in data['answers']:
        assert 'id' in answer
        assert 'answer' in answer
        
    # 将结果写入output.txt
    with open('output_get_question.txt', 'w', encoding='utf-8') as f:
        f.write('问题:\n')
        f.write(data['question']['query'].replace('\\n', '') + '\n\n')
        
        f.write('答案1:\n')
        f.write('上文:\n' + data['question']['context_before'].replace('\\n', '') + '\n\n')
        f.write('中间内容:\n' + data['answers'][0]['answer'].replace('\\n', '') + '\n\n')
        f.write('下文:\n' + data['question']['context_after'].replace('\\n', '') + '\n\n')
        
        f.write('答案2:\n')
        f.write('上文:\n' + data['question']['context_before'].replace('\\n', '') + '\n\n')
        f.write('中间内容:\n' + data['answers'][1]['answer'].replace('\\n', '') + '\n\n')
        f.write('下文:\n' + data['question']['context_after'].replace('\\n', '') + '\n\n')
    print('获取问题接口测试通过')
    return data

def test_submit_choice():
    """测试提交选择接口"""
    # 先获取一个问题
    question_data = test_get_question()
    
    # 询问用户选择
    print("\n请选择答案(0或1):")
    choice = int(input())
    
    # 构造提交数据
    submit_data = {
        'question_id': question_data['question']['question_id'],
        'choice': choice,  # 使用用户输入的选择
        'model_ids': question_data['model_ids'],
        'answers': question_data['answers'],
        'question': question_data['question']
    }
    
    # 发送POST请求
    response = requests.post(
        'http://localhost:5000/submit_choice',
        json=submit_data
    )
    
    # 检查响应状态码
    assert response.status_code == 200
    
    # 检查返回数据
    data = response.json()
    assert 'message' in data
    assert 'model_A' in data 
    assert 'model_B' in data
    
    print('提交选择接口测试通过')
    return data

def qwen3_reason_answer():
    """测试qwen3-reason模型回答问题"""
    # 读取json文件
    with open('dataset/task1/qwen3_reason.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 遍历每个问题
    for item in data:
        # 将answer改为answer[0]
        item['answer'] = item['answer'][0]
    
    # 保存修改后的文件
    with open('dataset/task1/qwen3_reason.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print('qwen3-reason模型答案修改完成')
    return data

if __name__ == '__main__':
    # test_get_question()
    # test_submit_choice()
    qwen3_reason_answer()
