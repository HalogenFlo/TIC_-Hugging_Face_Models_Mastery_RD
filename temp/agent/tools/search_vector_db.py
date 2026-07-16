# Chức năng: Thực hiện tìm kiếm tương đồng vector (semantic search) trên CSDL Neo4j Vector Index.

from typing import List, Dict, Any, Optional
import os
from config import get_neo4j_driver, get_embedding, DEFAULT_PROVIDER

def search_vector_db(query_text: str, limit: int = 5, provider: str = DEFAULT_PROVIDER) -> List[Dict[str, Any]]:
    """Tìm kiếm các đoạn văn bản luật (TextUnit) tương đồng ngữ nghĩa nhất với query_text.
    Kết quả trả về kèm thông tin trích dẫn nguồn (Component citation, Norm number) để Agent có thể trích dẫn chính xác.
    """
    try:
        # 1. Sinh vector embedding cho câu hỏi
        query_vector = get_embedding(query_text, provider=provider)
        
        # 2. Thực hiện truy vấn trên Neo4j Vector Index kèm JOIN ngược lên Component/Norm
        driver = get_neo4j_driver()
        query = """
        CALL db.index.vector.queryNodes('textunit_embedding_index', $limit, $query_vector)
        YIELD node, score
        OPTIONAL MATCH (c:Component)-[:HAS_TEXTUNIT]->(node)
        OPTIONAL MATCH (n:Norm)-[:CONTAINS*1..6]->(c)
        RETURN node.unit_id AS unit_id, 
               node.accumulated_text AS accumulated_text, 
               c.citation AS citation,
               c.comp_id AS comp_id,
               n.norm_number AS norm_number,
               n.norm_type AS norm_type,
               score
        """
        
        results = []
        with driver.session() as session:
            result = session.run(query, limit=limit, query_vector=query_vector)
            for record in result:
                results.append(dict(record))
                
        return results
    except Exception as e:
        print(f"[ERROR] search_vector_db failed: {e}")
        return []


