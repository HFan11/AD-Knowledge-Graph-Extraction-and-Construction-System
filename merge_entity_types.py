import csv
import re
from collections import defaultdict
from fuzzywuzzy import fuzz

class EntityMerger:
    def __init__(self):
        # 基础映射关系
        self.base_mapping = {
            'Disease': ['Disease', 'Disorder', 'Condition'],
            'Clinical_Manifestation': ['Clinical_Manifestation', 'Symptom', 'Sign'],
            'Biomarker': ['Biomarker', 'Marker', 'Indicator'],
            'Brain_Region': ['Brain_Region', 'Brain_Area', 'Anatomical_Structure'],
            'Clinical_Test': ['Clinical_Test', 'Test', 'Assessment', 'Examination'],
            'Imaging_Method': ['Imaging_Method', 'Imaging', 'Scan'],
            'Research_Method': ['Research_Method', 'Method', 'Analysis', 'Model'],
            'Pathological_Change': ['Pathological_Change', 'Pathology', 'Change'],
            'Clinical_Stage': ['Clinical_Stage', 'Stage', 'Phase'],
            'Risk_Factor': ['Risk_Factor', 'Risk', 'Factor'],
            'Treatment': ['Treatment', 'Drug', 'Therapy', 'Medication'],
            'Protein': ['Protein', 'Peptide'],
            'Gene': ['Gene', 'Genetic_Factor'],
            'Dataset': ['Dataset', 'Database', 'Data']
        }

    def compute_similarity(self, text1, text2):
        """计算两个文本的相似度"""
        return fuzz.ratio(text1.lower(), text2.lower()) / 100

    def find_similar_entities(self, target, entities, threshold=85):
        """找到相似的实体"""
        similar = []
        for entity in entities:
            if entity != target and self.compute_similarity(target, entity) >= threshold/100:
                similar.append(entity)
        return similar

    def merge_similar_entities(self, entities):
        """合并相似的实体"""
        entity_mapping = {}
        processed = set()
        
        # 首先应用基础映射
        for standard, variants in self.base_mapping.items():
            for variant in variants:
                variant_lower = variant.lower()
                for entity in entities:
                    if entity.lower() == variant_lower:
                        entity_mapping[entity] = standard
                        processed.add(entity)

        # 然后处理剩余的实体
        entities_list = list(entities)
        for entity in entities_list:
            if entity not in processed:
                similar_entities = self.find_similar_entities(entity, entities_list)
                if similar_entities:
                    # 选择最长的作为代表
                    representative = max([entity] + similar_entities, key=len)
                    for similar in similar_entities:
                        entity_mapping[similar] = representative
                    entity_mapping[entity] = representative
                    processed.add(entity)
                    processed.update(similar_entities)
                else:
                    entity_mapping[entity] = entity
                    processed.add(entity)
        
        return entity_mapping

    def merge_triples(self, input_file, output_file):
        """合并三元组中的实体"""
        # 读取所有三元组
        triples = []
        entity_types = set()
        entities = set()
        
        with open(input_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                triples.append(row)
                entity_types.add(row['Head_Type'])
                entity_types.add(row['Tail_Type'])
                entities.add(row['Head_Entity'])
                entities.add(row['Tail_Entity'])

        # 合并相似的实体类型
        type_mapping = self.merge_similar_entities(list(entity_types))
        
        # 合并相似的实体
        entity_mapping = self.merge_similar_entities(list(entities))
        
        # 应用映射生成新的三元组
        merged_triples = set()
        for triple in triples:
            merged_triple = (
                type_mapping.get(triple['Head_Type'], triple['Head_Type']),
                entity_mapping.get(triple['Head_Entity'], triple['Head_Entity']),
                triple['Relation'].lower(),
                type_mapping.get(triple['Tail_Type'], triple['Tail_Type']),
                entity_mapping.get(triple['Tail_Entity'], triple['Tail_Entity']),
                triple.get('Description', '')  # 添加描述字段
            )
            merged_triples.add(merged_triple)

        # 保存结果
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Head_Type', 'Head_Entity', 'Relation', 'Tail_Type', 'Tail_Entity', 'Description'])
            writer.writerows(sorted(merged_triples))

        # 输出统计信息
        print("\n合并统计:")
        print(f"原始实体类型数量: {len(entity_types)}")
        print(f"合并后实体类型数量: {len(set(type_mapping.values()))}")
        print(f"原始实体数量: {len(entities)}")
        print(f"合并后实体数量: {len(set(entity_mapping.values()))}")
        print(f"原始三元组数量: {len(triples)}")
        print(f"合并后三元组数量: {len(merged_triples)}")

        # 输出合并详情
        print("\n实体类型合并详情:")
        self._print_merge_details(entity_types, type_mapping)
        
        print("\n实体合并详情:")
        self._print_merge_details(entities, entity_mapping)

    def _print_merge_details(self, original_items, mapping):
        """打印合并详情"""
        merged_groups = defaultdict(list)
        for orig, merged in mapping.items():
            if orig != merged:
                merged_groups[merged].append(orig)
        
        for merged, originals in merged_groups.items():
            if len(originals) > 1:
                print(f"{merged} <- {', '.join(originals)}")

def main():
    input_file = "results/merged_knowledge_triples.csv"
    output_file = "results/merged_knowledge_triples_smart.csv"
    
    merger = EntityMerger()
    merger.merge_triples(input_file, output_file)

if __name__ == "__main__":
    main() 