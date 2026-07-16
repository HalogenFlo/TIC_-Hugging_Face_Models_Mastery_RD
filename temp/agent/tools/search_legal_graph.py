# Chức năng: Duyệt đồ thị tri thức Neo4j GraphRAG để tìm mối quan hệ liên kết chéo giữa các văn bản và điều luật.

from typing import List, Dict, Any
from config import get_neo4j_driver

def get_norm_relations(code: str) -> List[Dict[str, Any]]:
    """Lấy danh sách các văn bản luật liên quan (hướng dẫn, tham chiếu...) của một văn bản cụ thể."""
    try:
        driver = get_neo4j_driver()
        
        # 1. Quan hệ từ văn bản này hướng tới văn bản khác (Xuôi)
        query_out = """
        MATCH (n:Norm) WHERE n.norm_number = $code
        MATCH (n)-[r:CITES|IMPLEMENTS|SUPPLEMENTS|AMENDS|PARTIALLY_TERMINATES|TERMINATES|REFERS_TO|RELATED_TO]->(target:Norm)
        RETURN type(r) AS rel_type, target.norm_number AS code, target.norm_type AS type, 'outgoing' AS direction
        """
        
        # 2. Quan hệ từ văn bản khác tác động lên văn bản này (Ngược)
        query_in = """
        MATCH (n:Norm) WHERE n.norm_number = $code
        MATCH (source:Norm)-[r:CITES|IMPLEMENTS|SUPPLEMENTS|AMENDS|PARTIALLY_TERMINATES|TERMINATES|REFERS_TO|RELATED_TO]->(n)
        RETURN type(r) AS rel_type, source.norm_number AS code, source.norm_type AS type, 'incoming' AS direction
        """
        
        relations = []
        with driver.session() as session:
            # Chạy truy vấn xuôi
            res_out = session.run(query_out, code=code)
            for record in res_out:
                relations.append(dict(record))
                
            # Chạy truy vấn ngược
            res_in = session.run(query_in, code=code)
            for record in res_in:
                relations.append(dict(record))
                
        return relations
    except Exception as e:
        print(f"[ERROR] get_norm_relations failed: {e}")
        return []

def get_component_actions(comp_id: str) -> List[Dict[str, Any]]:
    """Lấy danh sách các hành động sửa đổi hoặc dẫn chiếu chéo của một điều luật (Component).
    Duyệt đệ quy chuỗi sửa đổi bắc cầu qua đường đi: Action -[:APPLY_TO|HAS_ACTION*1..6]-> Component.
    Fallback về cấu trúc phẳng (Component -[:REFERS_TO]-> Component) nếu không tìm thấy Action.
    """
    try:
        driver = get_neo4j_driver()
        
        # --- CÁCH 1: Duyệt đệ quy qua Action Node ---
        query_advanced = """
        MATCH path = (a:Action)-[:APPLY_TO|HAS_ACTION*1..6]->(c:Component {comp_id: $comp_id})
        OPTIONAL MATCH (a)-[:HAS_TEXTUNIT]->(t:TextUnit)
        RETURN a.amending_doc_number AS amending_doc, 
               a.relation_type AS action_type, 
               t.accumulated_text AS action_text,
               t.unit_id AS unit_id,
               length(path) AS depth
        ORDER BY depth ASC
        """
        
        actions = []
        with driver.session() as session:
            # Thử chạy theo cấu trúc nâng cao trước
            res_adv = session.run(query_advanced, comp_id=comp_id)
            for record in res_adv:
                actions.append(dict(record))
                
            # --- CÁCH 2: Fallback cấu trúc phẳng (REFERS_TO) ---
            if not actions:
                query_flat = """
                MATCH (c:Component {comp_id: $comp_id})-[r:REFERS_TO]->(target:Component)
                OPTIONAL MATCH (target)-[:HAS_TEXTUNIT]->(t:TextUnit)
                RETURN target.comp_id AS target_comp_id, 
                       target.citation AS citation, 
                       t.accumulated_text AS text
                """
                res_flat = session.run(query_flat, comp_id=comp_id)
                for record in res_flat:
                    actions.append({
                        "amending_doc": "Dẫn chiếu chéo",
                        "action_type": "REFERS_TO",
                        "action_text": record["text"],
                        "unit_id": record["target_comp_id"]
                    })
                    
        return actions
    except Exception as e:
        print(f"[ERROR] get_component_actions failed: {e}")
        return []

def get_component_context(comp_id: str) -> Dict[str, Any]:
    """
    Lấy thông tin ngữ cảnh của một điều luật bao gồm văn bản luật gốc (Norm) chứa nó.
    """
    try:
        driver = get_neo4j_driver()
        
        # 1. Lấy văn bản luật gốc chứa Component (dùng chung cho cả 2 cấu trúc)
        query_norm = """
        MATCH (n:Norm)-[:CONTAINS]->(c:Component {comp_id: $comp_id})
        RETURN n.norm_number AS code, n.norm_type AS type LIMIT 1
        """
        
        # 2. Lấy tiêu đề và thông tin chi tiết Component (Thử nâng cao qua Version trước, sau đó fallback phẳng)
        query_comp_adv = """
        MATCH (c:Component {comp_id: $comp_id})-[:HAS_VERSION]->(v:Version)
        RETURN c.title_text AS title, c.citation AS citation, c.level AS level, v.version_id AS version_id LIMIT 1
        """
        
        query_comp_flat = """
        MATCH (c:Component {comp_id: $comp_id})
        RETURN c.title_text AS title, c.citation AS citation, c.level AS level LIMIT 1
        """
        
        context = {"norm": {}, "component": {}}
        with driver.session() as session:
            # Lấy Norm gốc
            res_norm = session.run(query_norm, comp_id=comp_id)
            norm_record = res_norm.single()
            if norm_record:
                context["norm"] = dict(norm_record)
                
            # Thử lấy chi tiết Component qua cấu trúc nâng cao (Version)
            res_comp = session.run(query_comp_adv, comp_id=comp_id)
            comp_record = res_comp.single()
            if comp_record:
                context["component"] = dict(comp_record)
            else:
                # Fallback lấy cấu trúc phẳng
                res_comp_flat = session.run(query_comp_flat, comp_id=comp_id)
                comp_record_flat = res_comp_flat.single()
                if comp_record_flat:
                    context["component"] = dict(comp_record_flat)
                    
        return context
    except Exception as e:
        print(f"[ERROR] get_component_context failed: {e}")
        return {"norm": {}, "component": {}}
