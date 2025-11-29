# Swagger 테스트용 샘플 데이터

Swagger UI (`http://localhost:8000/docs`)에서 복사하여 사용할 수 있는 샘플 데이터입니다.

---

## 1. 문서 저장 (POST /api/admin/v1/documents)

### 샘플 1: 재택근무 정책 (긴 문서 - 청킹 필요)

```json
{
  "title": "2024년 재택근무 정책",
  "doc_type": "policy",
  "content": "2024년부터 시행되는 새로운 재택근무 정책을 안내드립니다.\n\n1. 재택근무 일수\n- 주 2회 재택근무가 가능합니다\n- 팀 업무 특성에 따라 팀장 승인 하에 조정 가능합니다\n- 재택근무 가능 요일은 화요일과 목요일입니다\n\n2. 신청 방법\n- 재택근무 전날까지 팀장에게 사전 승인 받아야 합니다\n- 그룹웨어 시스템에서 신청서를 작성하세요\n- 긴급한 업무가 있는 경우 유선 승인 후 사후 신청이 가능합니다\n\n3. 근무 수칙\n- 정규 근무 시간(09:00-18:00)을 준수해야 합니다\n- 협업 툴(Slack, Zoom)을 통해 즉시 연락 가능한 상태를 유지하세요\n- 일일 업무 보고를 작성하여 팀 채널에 공유하세요\n- 화상 회의 시 카메라를 켜는 것을 권장합니다\n\n4. 장비 지원\n- 노트북, 모니터 등 필요한 장비를 회사에서 지원합니다\n- IT 팀에 문의하여 신청하세요\n- 재택근무용 의자 구매 시 20만원까지 지원됩니다\n\n5. 보안 수칙\n- VPN을 통해 사내 시스템에 접속하세요\n- 공공 와이파이 사용을 자제하세요\n- 업무 자료는 개인 기기에 저장하지 마세요",
  "language": "ko",
  "metadata": {
    "year": 2024,
    "department": "전사",
    "category": "근무제도"
  },
  "source_type": "ui_input"
}
```

### 샘플 2: 연차 사용 가이드

```json
{
  "title": "연차 휴가 사용 가이드",
  "doc_type": "guide",
  "content": "연차 휴가 사용에 대한 상세 가이드입니다.\n\n1. 연차 발생 기준\n- 입사 1년 차: 15일\n- 2년 차 이상: 15일 + 근속년수별 추가 (최대 25일)\n- 매년 1월 1일 기준으로 발생\n\n2. 사용 방법\n- 그룹웨어에서 최소 1일 전 신청\n- 팀장 승인 후 사용 가능\n- 긴급한 경우 유선 승인 후 사후 신청 가능\n\n3. 미사용 연차\n- 연차는 당해 연도 내 사용이 원칙\n- 미사용 연차는 익년 상반기까지 사용 가능\n- 그 이후 자동 소멸됨\n\n4. 연차 사용 촉진\n- 분기별 5일 이상 사용 권장\n- 연말 집중 사용을 지양하고 계획적으로 사용하세요",
  "language": "ko",
  "metadata": {
    "year": 2024,
    "department": "HR",
    "category": "휴가"
  },
  "source_type": "ui_input"
}
```

### 샘플 3: 백엔드 개발자 채용 공고

```json
{
  "title": "2024년 상반기 백엔드 개발자 채용",
  "doc_type": "job_posting",
  "content": "백엔드 개발자를 모집합니다!\n\n[모집 부문]\n- 직무: 백엔드 개발\n- 경력: 3년 이상\n- 채용 인원: 00명\n\n[자격 요건]\n- Python, Django/FastAPI 프레임워크 실무 경험 3년 이상\n- RESTful API 설계 및 개발 경험\n- PostgreSQL, MySQL 등 RDBMS 활용 경험\n- Git을 활용한 협업 경험\n\n[우대 사항]\n- AWS, GCP 등 클라우드 서비스 경험\n- Docker, Kubernetes 등 컨테이너 기술 활용 경험\n- Redis, Elasticsearch 등 사용 경험\n- 대용량 트래픽 처리 경험\n\n[근무 조건]\n- 근무지: 서울 강남구\n- 근무 시간: 주 5일 (09:00-18:00)\n- 재택근무: 주 2회 가능\n- 급여: 경력에 따라 협의\n\n[전형 절차]\n1. 서류 전형\n2. 코딩 테스트\n3. 1차 면접 (기술)\n4. 2차 면접 (컬처핏)\n5. 최종 합격\n\n[지원 방법]\n- 이메일: recruit@company.com\n- 제출 서류: 이력서, 포트폴리오",
  "language": "ko",
  "metadata": {
    "year": 2024,
    "department": "개발",
    "position": "백엔드개발자",
    "region": "서울"
  },
  "source_type": "ui_input"
}
```

### 샘플 4: 인사평가 FAQ

```json
{
  "title": "인사평가 제도 FAQ",
  "doc_type": "faq",
  "content": "인사평가 제도에 대해 자주 묻는 질문입니다.\n\nQ1. 인사평가는 언제 실시되나요?\nA1. 연 2회 실시됩니다. 상반기 평가는 7월, 하반기 평가는 1월에 진행됩니다.\n\nQ2. 평가 등급은 어떻게 나뉘나요?\nA2. S, A, B, C, D 총 5단계로 구분됩니다.\n- S등급: 탁월한 성과 (상위 10%)\n- A등급: 우수한 성과 (상위 20%)\n- B등급: 기대 수준 충족 (50%)\n- C등급: 개선 필요 (15%)\n- D등급: 현저히 미흡 (5%)\n\nQ3. 평가 결과는 어떻게 활용되나요?\nA3. 승진, 보상, 교육 등에 활용됩니다.\n- 승진: S, A 등급 누적 시 승진 대상\n- 인센티브: 등급별 차등 지급\n- 교육: C, D 등급자 대상 역량 개발 교육\n\nQ4. 평가에 이의가 있을 경우?\nA4. 평가 결과 공개 후 2주 이내 HR팀에 이의 신청이 가능합니다.\n\nQ5. 신입사원도 평가 대상인가요?\nA5. 입사 6개월 이상 경과 시 평가 대상에 포함됩니다.",
  "language": "ko",
  "metadata": {
    "year": 2024,
    "department": "HR",
    "category": "평가"
  },
  "source_type": "ui_input"
}
```

---

## 2. 임베딩 실행 (POST /api/admin/v1/documents/embedding/execute)

문서 저장 후 반환된 `doc_id`를 사용하여 임베딩을 실행합니다.

### 단일 문서 임베딩

```json
{
  "doc_ids": [1],
  "chunk_size": 1000,
  "chunk_overlap": 100,
  "delete_original": false
}
```

### 여러 문서 일괄 임베딩

```json
{
  "doc_ids": [1, 2, 3, 4],
  "chunk_size": 1000,
  "chunk_overlap": 100,
  "delete_original": false
}
```

---

## 3. RAG 검색 테스트 (POST /api/v1/rag)

임베딩 완료 후 다음 쿼리로 검색을 테스트할 수 있습니다.

### 검색 예시 1: 재택근무 관련

```json
{
  "query": "재택근무는 일주일에 몇 번 가능한가요?",
  "mode": "rag",
  "top_k": 3
}
```

### 검색 예시 2: 연차 관련

```json
{
  "query": "연차 휴가는 어떻게 신청하나요?",
  "mode": "rag",
  "top_k": 3
}
```

### 검색 예시 3: 인사평가 관련

```json
{
  "query": "인사평가 등급은 어떻게 나뉘나요?",
  "mode": "rag",
  "top_k": 3
}
```

### 검색 예시 4: 채용 관련

```json
{
  "query": "백엔드 개발자 채용 자격 요건이 뭔가요?",
  "mode": "rag",
  "top_k": 3
}
```

---

## 4. NL2SQL 검색 테스트 (POST /api/v1/nl2sql)

```json
{
  "query": "2024년에 입사한 직원은 몇 명인가요?",
  "mode": "nl2sql"
}
```

```json
{
  "query": "서울에서 근무하는 개발자는 몇 명인가요?",
  "mode": "nl2sql"
}
```

```json
{
  "query": "부서별 직원 수를 알려주세요",
  "mode": "nl2sql"
}
```

---

## 5. 문서 수정 테스트 (PUT /api/admin/v1/documents/{doc_id})

### 제목만 수정 (임베딩 유지)

```json
{
  "title": "2024년 재택근무 정책 (개정판)"
}
```

### 내용 수정 (재임베딩 필요)

```json
{
  "content": "재택근무 정책이 변경되었습니다. 주 3회로 확대 시행합니다."
}
```

---

## 테스트 순서

1. **DB 초기화**: `python scripts/init_db.py --force`
2. **서버 실행**: `run_server.bat` 또는 `uvicorn app.main:app --reload`
3. **Swagger 접속**: http://localhost:8000/docs
4. **문서 저장**: POST /api/admin/v1/documents (샘플 1~4 입력)
5. **미임베딩 문서 확인**: GET /api/admin/v1/documents?indexed=false
6. **임베딩 실행**: POST /api/admin/v1/documents/embedding/execute
7. **임베딩 완료 확인**: GET /api/admin/v1/documents?indexed=true
8. **RAG 검색 테스트**: POST /api/v1/rag
