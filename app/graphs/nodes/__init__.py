"""
Agent 그래프 노드 모듈

위치: app/graphs/nodes/

각 노드는 상태(state)를 입력받아 처리 후 반환하는 함수형 노드입니다.

모듈:
- agent_nodes: Agent 노드들 (intent_analysis_node)
- rag_nodes: RAG 검색 노드들 (retrieve, generate_answer)
- nl2sql_nodes: NL2SQL 노드들 (generate_sql, validate_sql, execute_sql, generate_answer)

사용법:
    from app.graphs.nodes.agent_nodes import intent_analysis_node
    from app.graphs.nodes.rag_nodes import retrieve_documents_node
    from app.graphs.nodes.nl2sql_nodes import generate_sql_node
"""
