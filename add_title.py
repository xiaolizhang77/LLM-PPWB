import json
import re

def get_title_from_md(md_content, question_text):
    # print(md_content)
    # print(question_text)

    # 获取问题文本的标题级别
    question_level = len(re.match(r'^#+', question_text).group()) if re.match(r'^#+', question_text) else 10
    # print(question_level)
    # 在md文件中找到问题文本的位置
    
    question_text = question_text.split('。')[0]

    question_pos = md_content.find(question_text)
    # print(question_pos)
        
    # 从问题位置往前找所有更大级别的标题
    titles = []
    current_pos = question_pos
    
    while current_pos > 0:
        # 找到前一个标题
        prev_title_pos = md_content.rfind('\n#', 0, current_pos)
            
        # 获取标题文本和级别
        title_lines = md_content[prev_title_pos:].split('\n')
        if len(title_lines) <= 1:
            break
        title_line = title_lines[1]
        title_level = len(re.match(r'^#+', title_line).group()) if re.match(r'^#+', title_line) else 10
        
        # 如果标题级别小于问题级别，则添加到结果中
        if title_level < question_level:
            title_text = title_line.lstrip('#').strip()
            print(title_line)
            titles.insert(0, title_text)
            break
            
        current_pos = prev_title_pos
        
    return ' > '.join(titles)

def add_titles():
    # 读取问题数据
    with open('dataset/task1/question.json', 'r', encoding='utf-8') as f:
        questions = json.load(f)
        
    # 读取文档数据
    with open('dataset/task1/document.json', 'r', encoding='utf-8') as f:
        documents = json.load(f)
        
    # 读取ground truth数据
    with open('dataset/task1/GT.json', 'r', encoding='utf-8') as f:
        ground_truths = json.load(f)
        
    # 为每个问题添加title
   
    for question in questions:
        # 找到对应的文档
        doc = next((d for d in documents if d['id'] == question['doc_id']), None)
        if not doc:
            continue
            
        # 找到对应的ground truth
        gt = next((g for g in ground_truths if g['question_id'] == question['question_id']), None)
        if not gt:
            continue
            
        # 读取md文件
        try:
            with open(doc['document'], 'r', encoding='utf-8') as f:
                md_content = f.read()
        except:
            continue
        
        # 获取title
        
        title = get_title_from_md(md_content, gt['ground_truth'])
        question['title'] = title

        
    # 保存更新后的问题数据
    with open('dataset/task1/question.json', 'w', encoding='utf-8') as f:
        json.dump(questions, f, ensure_ascii=False, indent=2)

if __name__ == '__main__':
    add_titles()
