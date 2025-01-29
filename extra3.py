import os
import csv
import re
import openai
import time
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'extraction_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 设置OpenAI API配置
openai.api_base = "https://api.deepseek.com/v1"
openai.api_key = "sk-485de9131d9e45549ed0a90f0a59010f"

def create_prompt(text):
    """创建提取知识图谱的prompt"""
    return f"""请作为一个医疗专家,从以下关于阿尔茨海默病(Alzheimer's Disease)的文本中提取知识图谱的三元组信息。
    
提取要求:
1. 提取格式为: <头实体类型,头实体,关系,尾实体类型,尾实体,描述>
2. 请仅使用以下实体类型:
   - Disease: 疾病(如阿尔茨海默病、MCI等)
   - Symptom: 症状和临床表现
   - Biomarker: 生物标志物
   - Brain_Region: 脑区
   - Clinical_Test: 临床检查和评估
   - Imaging_Method: 影像学方法
   - Treatment: 治疗方法和药物
   - Protein: 蛋白质
   - Gene: 基因
   - Risk_Factor: 风险因素
   - Pathological_Change: 病理改变
   - Clinical_Stage: 疾病分期
   - Research_Method: 研究方法
   - Clinical_Manifestation: 临床表现
3. 关系要准确描述两个实体之间的关联,使用简洁的动词或动词短语
4. 每行输出一个三元组,用逗号分隔六个字段
5. 最后一列描述字段需要简要说明该三元组表达的医学含义
6. 只输出三元组信息，不要其他解释性文字

示例输出:
Disease,Alzheimer's disease,affects,Brain_Region,hippocampus,阿尔茨海默病会导致海马体区域受损
Disease,Alzheimer's disease,has_symptom,Clinical_Manifestation,memory loss,记忆力丧失是阿尔茨海默病的主要症状
Protein,amyloid-beta,accumulates_in,Brain_Region,brain,淀粉样蛋白在大脑中异常堆积
Gene,APOE4,increases_risk_of,Disease,Alzheimer's disease,APOE4基因是阿尔茨海默病的重要风险因素
Clinical_Test,MMSE,evaluates,Clinical_Manifestation,cognitive function,简易精神状态检查用于评估认知功能
Treatment,donepezil,treats,Disease,Alzheimer's disease,多奈哌齐是治疗阿尔茨海默病的药物
Imaging_Method,MRI,detects,Pathological_Change,brain atrophy,核磁共振可以检测到脑萎缩情况

文本内容:
{text}

请提取上述文本中的三元组信息:"""

def extract_triples(text, file_name, chunk_index):
    """使用OpenAI API提取三元组"""
    try:
        prompt = create_prompt(text)
        logger.info(f"正在处理文件 {file_name} 的第 {chunk_index} 个文本块")
        
        response = openai.ChatCompletion.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "You are a medical expert specialized in Alzheimer's disease."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=2000
        )
        
        triples_text = response.choices[0].message.content.strip()
        triples = [line.strip() for line in triples_text.split('\n') if line.strip() 
                  and len(line.split(',')) == 6]
        
        logger.info(f"从文件 {file_name} 的第 {chunk_index} 个文本块中提取到 {len(triples)} 个三元组")
        return triples
        
    except Exception as e:
        logger.error(f"处理文件 {file_name} 的第 {chunk_index} 个文本块时出错: {str(e)}")
        return []

def process_file(file_path):
    """处理单个文件"""
    file_name = os.path.basename(file_path)
    logger.info(f"开始处理文件: {file_name}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()
    
    # 计算每个块的大致长度
    total_length = len(text)
    chunk_size = total_length // 3
    
    # 分割文本为三块
    text_chunks = []
    start = 0
    
    for i in range(3):
        if i < 2:
            # 找到最近的段落结束位置
            end = start + chunk_size
            # 向后查找最近的段落结束符
            next_para = text.find('\n\n', end)
            if next_para != -1:
                end = next_para
            else:
                end = len(text)
            
            chunk = text[start:end].strip()
            if chunk:
                text_chunks.append(chunk)
            start = end
        else:
            # 最后一块直接取到结尾
            chunk = text[start:].strip()
            if chunk:
                text_chunks.append(chunk)
    
    logger.info(f"文件 {file_name} 被分割为 {len(text_chunks)} 个文本块")
    
    all_triples = []
    for i, chunk in enumerate(text_chunks, 1):
        if len(chunk.strip()) > 0:
            logger.info(f"处理第 {i}/3 块，长度: {len(chunk)} 字符")
            triples = extract_triples(chunk, file_name, i)
            all_triples.extend(triples)
            time.sleep(1)
    
    logger.info(f"文件 {file_name} 处理完成，共提取 {len(all_triples)} 个三元组")
    return all_triples

def save_triples(triples, output_file):
    """保存三元组到CSV文件"""
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Head_Type', 'Head_Entity', 'Relation', 'Tail_Type', 'Tail_Entity', 'Description'])
        for triple in triples:
            writer.writerow(triple.split(','))
    logger.info(f"保存 {len(triples)} 个三元组到文件: {output_file}")

def get_processed_files(output_dir):
    """获取已经处理过的文件列表"""
    processed_files = set()
    for filename in os.listdir(output_dir):
        if filename.endswith('_triples.csv'):
            original_name = filename.replace('_triples.csv', '.txt')
            processed_files.add(original_name)
    return processed_files

def main():
    data_dir = 'dats'
    output_dir = 'results'
    
    # 创建结果目录
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        logger.info(f"创建输出目录: {output_dir}")
    
    # 获取已处理的文件列表
    processed_files = get_processed_files(output_dir)
    logger.info(f"发现已处理文件数量: {len(processed_files)}")
    
    # 获取所有待处理文件 - 修改这部分以处理大小写问题
    all_files = []
    seen_files = set()  # 用于追踪已经看到的文件名（忽略大小写）
    
    for f in os.listdir(data_dir):
        # 转换为小写进行比较
        f_lower = f.lower()
        if f_lower.endswith('.txt') and f_lower not in seen_files:
            all_files.append(f)
            seen_files.add(f_lower)
    
    remaining_files = [f for f in all_files if f not in processed_files]
    
    logger.info(f"总文件数: {len(all_files)}")
    logger.info(f"待处理文件数: {len(remaining_files)}")
    
    # 遍历所有txt文件
    for i, file_name in enumerate(remaining_files, 1):
        logger.info(f"进度: {i}/{len(remaining_files)} ({i/len(remaining_files)*100:.2f}%)")
        
        if file_name in processed_files:
            logger.info(f"跳过已处理的文件: {file_name}")
            continue
        
        logger.info(f"开始处理文件 {i}/{len(remaining_files)}: {file_name}")
        
        # 构建输入和输出文件路径
        input_file = os.path.join(data_dir, file_name)
        output_file = os.path.join(output_dir, f"{os.path.splitext(file_name)[0]}_triples.csv")
        
        try:
            # 处理文件并保存结果
            triples = process_file(input_file)
            triples = list(set(triples))  # 去重
            save_triples(triples, output_file)
            
            logger.info(f"文件处理完成: {file_name}")
            logger.info(f"提取 {len(triples)} 个三元组并保存到 {output_file}")
            logger.info("-" * 50)
            
        except Exception as e:
            logger.error(f"处理文件 {file_name} 时发生错误: {str(e)}")
            continue

if __name__ == '__main__':
    start_time = datetime.now()
    logger.info("开始处理任务")
    
    try:
        main()
    except Exception as e:
        logger.error(f"程序执行出错: {str(e)}")
    finally:
        end_time = datetime.now()
        duration = end_time - start_time
        logger.info(f"任务结束，总耗时: {duration}")