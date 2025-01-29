import csv
from collections import defaultdict

def collect_descriptions(input_file):
    """收集并整理三元组描述"""
    # 使用三元组作为键，收集所有相关描述
    descriptions = defaultdict(set)
    
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        headers = next(reader)  # 跳过标题行
        
        for row in reader:
            if len(row) >= 6:  # 确保有描述列
                # 使用前5列作为键（实体类型、实体名称和关系）
                key = tuple(row[:5])
                # 添加描述到集合中（自动去重）
                if row[5].strip():  # 只添加非空描述
                    descriptions[key].add(row[5].strip())
    
    return descriptions

def merge_descriptions(input_files, output_file):
    """合并多个文件中的描述信息，只保留最佳描述"""
    all_descriptions = defaultdict(set)
    
    # 收集所有文件中的描述
    for file in input_files:
        file_descriptions = collect_descriptions(file)
        for key, descs in file_descriptions.items():
            all_descriptions[key].update(descs)
    
    # 选择最佳描述并写入结果
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Head_Type', 'Head_Entity', 'Relation', 'Tail_Type', 'Tail_Entity', 'Description'])
        
        for key, descs in sorted(all_descriptions.items()):
            # 选择最佳描述（这里选择最长的中文描述）
            best_desc = max(descs, key=lambda x: len([c for c in x if '\u4e00' <= c <= '\u9fff']))
            writer.writerow(list(key) + [best_desc])

def print_unique_descriptions(descriptions):
    """打印所有不重复的描述"""
    unique_descs = set()
    for descs in descriptions.values():
        unique_descs.update(descs)
    
    print("\n所有不重复的描述:")
    for desc in sorted(unique_descs):
        print(f"- {desc}")
    return len(unique_descs)

def main():
    # 处理results目录下的所有三元组文件
    import os
    input_dir = 'results'
    input_files = [
        os.path.join(input_dir, f) 
        for f in os.listdir(input_dir) 
        if f.endswith('_triples.csv')
    ]
    
    output_file = 'results/knowledge_triples_with_descriptions.csv'
    
    # 合并所有描述
    all_descriptions = defaultdict(set)
    for file in input_files:
        file_descriptions = collect_descriptions(file)
        for key, descs in file_descriptions.items():
            all_descriptions[key].update(descs)
    
    # 打印统计信息
    total_triples = len(all_descriptions)
    total_unique_descs = print_unique_descriptions(all_descriptions)
    
    # 合并并保存结果
    merge_descriptions(input_files, output_file)
    
    print(f"\n处理完成:")
    print(f"总三元组数量: {total_triples}")
    print(f"不重复描述数量: {total_unique_descs}")
    print(f"结果已保存至: {output_file}")

if __name__ == "__main__":
    main() 