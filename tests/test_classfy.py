from app.api.routes.search import _classify_query_intent 


# 분류 검색 테스트 
response = _classify_query_intent("2024년도 직원중 가장 우수하다고 판단되는 사원은 누구인가?")
print(f"요청 분류 결과 (RAG or NL2SQL)  =>  {response}")
response = _classify_query_intent("회사의 휴가 정책에 대해 알려줘")
print(f"요청 분류 결과 (RAG or NL2SQL) =>  {response}")
