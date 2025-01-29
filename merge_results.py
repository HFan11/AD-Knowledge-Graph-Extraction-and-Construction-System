import os
import csv
import re

def clean_triple(triple):
    """清理三元组数据"""
    # 移除 < > 符号
    triple = [re.sub(r'[<>]', '', item.strip()) for item in triple]
    
    # 标准化关系名称(保持小写)
    triple[2] = triple[2].lower()
    
    return triple

def merge_results(input_dir, output_file):
    """合并并清理所有结果文件"""
    all_triples = set()  # 使用集合去重
    entity_types = set()  # 收集所有出现的实体类型
    
    # 遍历results目录下的所有csv文件
    for filename in os.listdir(input_dir):
        if filename.endswith('_triples.csv'):
            file_path = os.path.join(input_dir, filename)
            print(f"处理文件: {filename}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader)  # 跳过标题行
                
                for row in reader:
                    if len(row) >= 6:  # 确保是有效的三元组（包含描述）
                        cleaned_triple = clean_triple(row)
                        if cleaned_triple:
                            # 收集实体类型
                            entity_types.add(cleaned_triple[0])
                            entity_types.add(cleaned_triple[3])
                            # 转换为元组以便存入集合
                            all_triples.add(tuple(cleaned_triple))
    
    # 将结果写入新的CSV文件
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Head_Type', 'Head_Entity', 'Relation', 'Tail_Type', 'Tail_Entity', 'Description'])
        
        # 将集合转换回列表并排序，以保证输出的一致性
        sorted_triples = sorted(list(all_triples))
        writer.writerows(sorted_triples)
    
    print(f"\n处理完成:")
    print(f"发现的实体类型: {sorted(list(entity_types))}")
    print(f"实体类型总数: {len(entity_types)}")
    print(f"合并前总三元组数: {sum(1 for triple in all_triples)}")
    print(f"去重后三元组数: {len(all_triples)}")
    print(f"结果已保存至: {output_file}")

def main():
    input_dir = 'results'
    output_file = 'results/merged_knowledge_triples.csv'
    merge_results(input_dir, output_file)

if __name__ == '__main__':
    main()
