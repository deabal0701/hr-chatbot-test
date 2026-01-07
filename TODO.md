## Todos
1. langgraph.checkpoint.memory(InMemorySaver) 을 통한 메모리(short term memory) 관리와 현재의 방법의 차이는?
2. agent를 생성시 create_agent를 사용하지 않는지? 현재의 방법과 langchain에서 생성하는 방식의 차이는?
create_agent(model, tools, checkpointer=InMemorySaver)
3. middleware를 사용한 섬세하고 디테일한 컨트롤
 -> agent 내부활동 모니터링 및 컨트롤, 출력포맷설정, 가드레일(개인정보, 프롬프트인젝션)
 -> builtin middleware를 통한 카드번호등 마스킹