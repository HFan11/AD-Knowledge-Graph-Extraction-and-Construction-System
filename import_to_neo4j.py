from neo4j import GraphDatabase
import csv
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Neo4jImporter:
    def __init__(self, uri, user, password):
        """初始化Neo4j连接"""
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        
    def close(self):
        """关闭数据库连接"""
        self.driver.close()
        
    def clear_database(self):
        """清空数据库"""
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
            logger.info("数据库已清空")

    def import_triple(self, head_type, head_entity, relation, tail_type, tail_entity):
        """导入单个三元组"""
        cypher_query = (
            f"MERGE (h:{head_type} {{name: $head_name}}) "
            f"MERGE (t:{tail_type} {{name: $tail_name}}) "
            f"MERGE (h)-[r:{relation.upper().replace(' ', '_')}]->(t)"
        )
        
        with self.driver.session() as session:
            try:
                session.run(
                    cypher_query,
                    head_name=head_entity,
                    tail_name=tail_entity
                )
                return True
            except Exception as e:
                logger.error(f"导入三元组时出错: {str(e)}")
                return False

    def import_from_csv(self, csv_file):
        """从CSV文件导入数据"""
        success_count = 0
        error_count = 0
        
        try:
            # 使用UTF-8编码读取CSV文件
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                # 计算总行数
                total_rows = sum(1 for row in csv.DictReader(open(csv_file, 'r', encoding='utf-8')))
                logger.info(f"开始导入 {total_rows} 条数据...")
                
                # 重置文件指针并跳过标题行
                f.seek(0)
                next(reader)
                
                for row in reader:
                    try:
                        if self.import_triple(
                            row['Head_Type'],
                            row['Head_Entity'],
                            row['Relation'],
                            row['Tail_Type'],
                            row['Tail_Entity']
                        ):
                            success_count += 1
                        else:
                            error_count += 1
                        
                        if success_count % 100 == 0:
                            logger.info(f"已成功导入 {success_count} 条数据...")
                    except Exception as e:
                        logger.error(f"导入行时出错: {str(e)}")
                        error_count += 1
                        continue
            
            logger.info(f"\n导入完成:")
            logger.info(f"成功: {success_count}")
            logger.info(f"失败: {error_count}")
            logger.info(f"总计: {success_count + error_count}")
            
        except Exception as e:
            logger.error(f"读取CSV文件时出错: {str(e)}")
            raise

def main():
    # Neo4j连接配置
    uri = "neo4j://localhost:7687"
    user = "neo4j"
    password = "12345678"
    
    # CSV文件路径
    # csv_file = "results/merged_knowledge_triples.csv"
    csv_file = "results/merged_knowledge_triples_smart.csv"
    
    try:
        # 创建导入器实例
        importer = Neo4jImporter(uri, user, password)
        
        # 清空数据库
        logger.info("清空数据库...")
        importer.clear_database()
        
        # 导入数据
        logger.info("开始导入数据...")
        importer.import_from_csv(csv_file)
        
    except Exception as e:
        logger.error(f"发生错误: {str(e)}")
    
    finally:
        # 关闭连接
        importer.close()
        logger.info("数据库连接已关闭")

if __name__ == "__main__":
    main() 