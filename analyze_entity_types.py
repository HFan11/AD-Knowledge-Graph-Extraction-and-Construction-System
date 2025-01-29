import csv
from collections import Counter

def analyze_entity_types(csv_file):
    head_types = Counter()
    tail_types = Counter()
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            head_types[row['Head_Type']] += 1
            tail_types[row['Tail_Type']] += 1
    
    # 合并头尾实体类型的计数
    all_types = Counter()
    for type_name, count in head_types.items():
        all_types[type_name] += count
    for type_name, count in tail_types.items():
        all_types[type_name] += count
    
    # 输出排序后的结果
    print("\n最常见的实体类型及其出现次数:")
    for type_name, count in all_types.most_common():
        print(f"{type_name}: {count}")

if __name__ == "__main__":
    analyze_entity_types("results/merged_knowledge_triples.csv") 