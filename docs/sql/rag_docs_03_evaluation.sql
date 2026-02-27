-- ============================================================
-- RAG 문서 데이터 - Part 03: 성과평가/KPI/승진 제도
-- 총 문서 수: 20개 (논리적 문서), 멀티청크 포함 총 28행
-- 생성일: 2026-02-27
-- 용도: RAG 검색 테스트 (RAGAS 평가용)
-- ============================================================

-- [문서 1] 연간 성과평가 프로세스 (멀티청크 3개)
DO $$
DECLARE parent_id BIGINT;
BEGIN
    INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
    VALUES (
        1,
        '연간 성과평가 프로세스',
        'policy',
        'ko',
        '제1조(목적) 본 규정은 공정하고 투명한 성과 관리를 통해 직원의 역량 개발과 조직 성과 극대화를 도모함을 목적으로 한다. 제2조(평가 주기) 성과평가는 연 1회 실시하며, 평가 기간은 매년 1월 1일~12월 31일이다. 제3조(평가 일정) (1) 1월: 목표 설정(MBO) 및 등록. (2) 4월/7월/10월: 분기별 중간 점검(Progress Review). (3) 12월 1일~20일: 자기 평가 및 1차 평가(팀장). (4) 12월 21일~31일: 2차 평가(부서장) 및 평가 조정 회의. (5) 익년 1월 1일~15일: 최종 등급 확정 및 피드백 면담. (6) 익년 2월: 성과급 반영 및 연봉 조정.',
        '{"tags":["성과평가","프로세스","MBO","평가일정","목표설정","중간점검"],"category":"성과관리","doc_category":"성과관리","importance":"critical"}',
        NULL, 'text-embedding-3-small', false, 0, 3, NULL, 'sql_import', 'rag_knowledge',
        NULL
    ) RETURNING id INTO parent_id;

    INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
    VALUES (
        1,
        '연간 성과평가 프로세스',
        'policy',
        'ko',
        '제4조(평가 체계) (1) 업적 평가(70%): MBO 기반 목표 달성률 평가. 목표 개수 3~5개, 목표별 가중치 합계 100%. (2) 역량 평가(30%): 직급별 핵심 역량(리더십, 전문성, 협업, 혁신) 행동 지표 기반 평가. (3) 팀장급 이상: 업적 평가 60% + 역량 평가 20% + 리더십 평가 20%. 제5조(평가자·피평가자) (1) 1차 평가자: 직속 상사(팀장). (2) 2차 평가자: 차상위 상사(부서장/본부장). (3) 다면평가: 동료 평가(참고 자료, 등급 결정에 직접 반영하지 않음). (4) 1차·2차 평가자 간 의견 차이가 2등급 이상일 경우 인사위원회 조정.',
        '{"tags":["평가체계","업적평가","역량평가","리더십평가","다면평가","평가자"],"category":"성과관리","doc_category":"성과관리","importance":"critical"}',
        NULL, 'text-embedding-3-small', false, 1, 3, parent_id, 'sql_import', 'rag_knowledge', NULL
    );

    INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
    VALUES (
        1,
        '연간 성과평가 프로세스',
        'policy',
        'ko',
        '제6조(피드백 면담) (1) 평가 결과 확정 후 15일 이내에 1차 평가자와 피평가자 간 1:1 피드백 면담을 실시한다. (2) 면담 내용: 평가 결과 공유, 강점·개선점 피드백, 익년도 목표 방향 논의. (3) 면담 기록은 성과관리 시스템에 저장하며, 양자가 확인 서명한다. 제7조(평가 결과 공개) (1) 피평가자에게 본인의 최종 등급, 평가 점수, 평가자 코멘트를 공개한다. (2) 타인의 평가 결과는 공개하지 않으며, 등급별 인원 분포만 전사 공지한다. 제8조(평가 결과 활용) (1) 성과급: 등급별 차등 지급(별도 규정). (2) 연봉 조정: 등급별 인상률 차등 적용. (3) 승진 심사: 최근 3년 평가 등급 반영. (4) 교육 계획: 역량 평가 결과에 따른 맞춤형 교육 설계. (5) 인사 배치: 저성과자 PIP, 고성과자 Fast Track.',
        '{"tags":["피드백면담","평가결과","성과급","연봉조정","승진","교육계획"],"category":"성과관리","doc_category":"성과관리","importance":"critical"}',
        NULL, 'text-embedding-3-small', false, 2, 3, parent_id, 'sql_import', 'rag_knowledge', NULL
    );
END $$;

-- [문서 2] MBO 목표 설정 방법
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    'MBO 목표 설정 방법',
    'manual',
    'ko',
    '제1조(SMART 기준) 모든 목표는 SMART 기준을 충족하여야 한다: Specific(구체적), Measurable(측정 가능), Achievable(달성 가능), Relevant(조직 목표 연계), Time-bound(기한 명시). 제2조(목표 개수 및 가중치) (1) 개인별 3~5개의 목표를 설정한다. (2) 각 목표에 가중치를 부여하며, 합계는 100%여야 한다. (3) 단일 목표의 가중치는 최소 10%, 최대 40%로 제한한다. 제3조(상위 목표 연계) (1) 개인 목표는 팀 목표 → 부서 목표 → 전사 경영 목표와 연계되어야 한다. (2) 목표 등록 시 연계되는 상위 목표를 성과관리 시스템에 매핑한다. 제4조(목표 유형) (1) 업무 목표: 핵심 업무 성과 지표(매출, 프로젝트 완료, 고객 만족도 등). (2) 개선 목표: 업무 프로세스 개선, 효율화, 비용 절감. (3) 개발 목표: 역량 개발, 자격증 취득, 신기술 습득. 제5조(목표 수정) 사업 환경 변화, 조직 개편, 직무 변경 등 불가피한 경우 분기 중간 점검 시 목표를 수정할 수 있으며, 1차 평가자 승인이 필요하다. 수정 이력은 시스템에 기록된다.',
    '{"tags":["MBO","목표설정","SMART","가중치","상위목표","목표수정"],"category":"성과관리","doc_category":"성과관리","importance":"high"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- [문서 3] 성과등급 체계
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '성과등급 체계',
    'policy',
    'ko',
    '제1조(등급 구분) 성과평가 결과는 5개 등급으로 구분한다: S(탁월), A(우수), B(양호), C(보통), D(미흡). 제2조(등급별 기준) (1) S등급: 모든 목표를 초과 달성하고, 조직에 탁월한 기여. 목표 달성률 120% 이상. (2) A등급: 대부분의 목표를 달성하고, 우수한 성과. 달성률 100~119%. (3) B등급: 주요 목표를 달성하고, 양호한 수준. 달성률 80~99%. (4) C등급: 일부 목표 미달, 개선 필요. 달성률 60~79%. (5) D등급: 주요 목표 대부분 미달, 즉각적 개선 필요. 달성률 60% 미만. 제3조(강제배분) (1) 전사 기준 등급별 배분 비율: S 10%, A 20%, B 40%, C 20%, D 10%. (2) 부서 규모가 10인 미만인 경우 부서 간 통합 조정이 가능하다. (3) 배분 비율은 경영 상황에 따라 인사위원회가 조정할 수 있다. 제4조(특수 상황) (1) 중도 입사자(6개월 미만 재직): B등급 자동 부여(평가 면제). (2) 육아휴직·병가 등으로 실 근무 6개월 미만: 평가 면제, 전년도 등급 유지. (3) 부서 이동 시: 이동 전·후 부서에서 재직 기간 비례로 각각 평가.',
    '{"tags":["성과등급","S등급","강제배분","등급기준","달성률","특수상황"],"category":"성과관리","doc_category":"성과관리","importance":"critical"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- [문서 4] 다면평가 제도
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '다면평가 제도',
    'policy',
    'ko',
    '제1조(목적) 상사 평가의 단면성을 보완하고 다양한 관점에서 역량을 평가하기 위해 다면평가를 실시한다. 제2조(평가 유형 및 비율) (1) 상향 평가: 부하 직원이 상사를 평가(팀장급 이상 대상). 리더십, 소통, 지원 등 5개 항목, 5점 척도. (2) 동료 평가: 같은 팀 또는 협업 부서 동료가 평가. 협업, 전문성, 책임감 등 5개 항목. (3) 하향 평가: 상사가 부하를 평가(기존 업적·역량 평가와 통합). 제3조(익명성 보장) (1) 다면평가는 전수 익명으로 실시하며, 평가자 정보는 시스템에서 블라인드 처리한다. (2) 평가 대상자에게 개별 평가자의 점수를 공개하지 않고, 항목별 평균 점수만 제공한다. (3) 평가자가 3인 미만인 항목은 익명성 보호를 위해 결과를 제공하지 않는다. 제4조(결과 활용) (1) 다면평가 결과는 최종 성과등급 결정에 직접 반영하지 않으며, 참고 자료로 활용한다. (2) 단, 팀장급 이상의 리더십 평가 결과가 3.0 미만(5점 만점)인 경우 리더십 개선 프로그램(코칭, 교육) 참여를 권고한다. (3) 2년 연속 3.0 미만 시 보직 해임 심의 대상이 된다.',
    '{"tags":["다면평가","상향평가","동료평가","익명성","리더십","360도"],"category":"성과관리","doc_category":"성과관리","importance":"high"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- [문서 5] 역량평가 기준 (멀티청크 2개)
DO $$
DECLARE parent_id BIGINT;
BEGIN
    INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
    VALUES (
        1,
        '역량평가 기준',
        'policy',
        'ko',
        '제1조(역량 체계) 전사 공통 역량 4개와 직군별 전문 역량 2~3개로 구성된다. 제2조(공통 역량) (1) 리더십(팀장급 이상): ①방향 제시 ②의사결정 ③구성원 육성 ④변화 주도. (2) 전문성: ①직무 지식 수준 ②문제 해결 능력 ③업무 품질 ④지속적 학습. (3) 협업: ①팀워크 ②커뮤니케이션 ③갈등 관리 ④타 부서 협력. (4) 혁신: ①창의적 사고 ②프로세스 개선 ③디지털 활용 ④도전 정신. 제3조(행동 지표) 각 역량별 5단계 행동 지표(BOS: Behavioral Observation Scale)를 정의한다. Level 1(초보): 기본 수준의 역량 발휘. Level 2(적용): 주어진 상황에서 역량 활용. Level 3(숙련): 복잡한 상황에서 자율적 역량 발휘. Level 4(전문): 타인을 지도하고 조직 차원의 기여. Level 5(최고): 산업 수준의 전문성 보유, 혁신 선도.',
        '{"tags":["역량평가","공통역량","리더십","전문성","협업","혁신","행동지표"],"category":"성과관리","doc_category":"성과관리","importance":"high"}',
        NULL, 'text-embedding-3-small', false, 0, 2, NULL, 'sql_import', 'rag_knowledge',
        NULL
    ) RETURNING id INTO parent_id;

    INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
    VALUES (
        1,
        '역량평가 기준',
        'policy',
        'ko',
        '제4조(직급별 기대 수준) (1) 사원: Level 1~2, 기본 역량 발휘 및 학습 자세. (2) 대리: Level 2~3, 독립적 업무 수행 및 후배 지원. (3) 과장: Level 3~4, 프로젝트 리딩 및 팀 내 전문가 역할. (4) 차장: Level 4, 부서 내 핵심 역할 및 부서 간 협업 주도. (5) 부장: Level 4~5, 부서 운영 및 전략적 의사결정. (6) 임원: Level 5, 조직 방향 설정 및 경영 참여. 제5조(평가 방법) (1) 자기 평가: 각 역량별 구체적 행동 사례를 기술. (2) 1차 평가자: 행동 지표에 대한 관찰 결과를 5점 척도로 평가. (3) 평가 점수 = Σ(역량별 점수 × 가중치). 공통 역량 가중치: 리더십 30%(팀장급), 전문성 30%, 협업 20%, 혁신 20%. 사원~대리급: 전문성 40%, 협업 30%, 혁신 30%. 제6조(역량 개발 계획) 역량 평가 결과 기대 수준 미달 항목이 있는 경우, 1차 평가자와 협의하여 「개인 역량 개발 계획서(IDP)」를 수립하고, 분기별로 이행 상황을 점검한다.',
        '{"tags":["직급별기대","평가방법","역량개발","IDP","가중치","자기평가"],"category":"성과관리","doc_category":"성과관리","importance":"high"}',
        NULL, 'text-embedding-3-small', false, 1, 2, parent_id, 'sql_import', 'rag_knowledge', NULL
    );
END $$;

-- [문서 6] 성과급 연계 방식
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '성과급 연계 방식',
    'policy',
    'ko',
    '제1조(성과급 유형) (1) 개인 성과급: 성과등급에 따라 기본급 대비 차등 지급. (2) 팀 성과급: 팀 목표 달성률에 따라 팀 단위 추가 지급. (3) 경영성과급(PI): 회사 전체 경영 목표(매출, 영업이익) 달성 시 전 직원 대상 지급. 제2조(개인 성과급 지급률) 기본급 대비: S등급 200%, A등급 150%, B등급 100%, C등급 50%, D등급 0%. 제3조(팀 성과급) (1) 팀 목표 달성률 100% 이상: 팀원 1인당 기본급의 50% 추가. (2) 팀 목표 달성률 80~99%: 30% 추가. (3) 80% 미만: 미지급. (4) 팀 성과급은 팀장이 팀원별 기여도를 반영하여 차등 배분할 수 있다(차등 폭 ±20%). 제4조(지급 시기) (1) 개인 성과급: 매년 3월 급여일에 일괄 지급. (2) 팀 성과급: 반기별(7월, 1월) 지급. (3) 경영성과급: 결산 확정 후 3월 지급. 제5조(세금) 성과급은 상여금으로 분류되어 소득세 및 4대보험 산정 기준에 포함된다. 제6조(퇴직자 처리) 평가 기간 중 퇴직한 직원은 재직 기간에 비례하여 성과급을 지급하되, D등급 또는 징계 퇴직은 지급하지 않는다.',
    '{"tags":["성과급","개인성과급","팀성과급","경영성과급","지급률","등급별"],"category":"보상관리","doc_category":"성과관리","importance":"critical"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- [문서 7] 승진 요건 및 심사 기준
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '승진 요건 및 심사 기준',
    'policy',
    'ko',
    '제1조(승진 시기) 정기 승진은 매년 1월 1일자로 실시하며, 특별 승진은 수시로 가능하다. 제2조(직급별 최소 체류 기간) (1) 사원 → 주임: 2년. (2) 주임 → 대리: 2년. (3) 대리 → 과장: 3년. (4) 과장 → 차장: 4년. (5) 차장 → 부장: 4년. (6) 부장 → 임원: 별도 임원 선임 절차. 제3조(승진 요건) (1) 성과 요건: 최근 2년 평가 평균 B등급 이상, 최근 1년 C등급 이하 없음. (2) 역량 요건: 직급별 필수 교육 이수 완료. (3) 자격 요건: 징계 이력 없음(징계 후 2년 경과 시 해소). (4) 어학 요건(해외 사업 관련 직군): TOEIC 700점 이상 또는 동등 수준. 제4조(심사 절차) (1) 1차 심사: 소속 부서장 추천(서류 심사). (2) 2차 심사: 인사위원회 심의(업적·역량·잠재력 종합 평가). (3) 최종 결재: 대표이사 승인. 제5조(특별 승진) 탁월한 성과(S등급 2년 연속), 중대 프로젝트 성공, 특허 취득 등 특별 기여 시 체류 기간을 1년 단축하여 승진할 수 있다.',
    '{"tags":["승진","직급","체류기간","승진요건","심사","특별승진","인사위원회"],"category":"인사관리","doc_category":"성과관리","importance":"critical"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- [문서 8] 직급 체계 및 직무 등급
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '직급 체계 및 직무 등급',
    'policy',
    'ko',
    '제1조(직급 체계) 당사의 직급 체계는 6단계로 구성된다: 사원(G1) → 주임(G2) → 대리(G3) → 과장(G4) → 차장(G5) → 부장(G6). 임원은 상무보, 상무, 전무, 부사장, 사장으로 구분한다. 제2조(호칭) (1) 사내 호칭: 직급 + 님(예: 과장님). (2) 선택적 직급 파괴: IT개발, 디자인 직군은 '프로(Pro)' 단일 호칭 사용 가능(직급은 별도 관리). 제3조(직무 등급) (1) 직무 등급은 직무의 난이도, 책임 범위, 필요 역량 수준에 따라 J1~J7로 구분한다. (2) 직급과 직무 등급의 매핑: 사원 J1~J2, 주임 J2~J3, 대리 J3~J4, 과장 J4~J5, 차장 J5~J6, 부장 J6~J7. (3) 직무 등급이 직급 범위를 초과하는 경우(예: 대리급이 J5 수준 직무 수행) 직무 수당을 별도 지급한다. 제4조(전문직 트랙) 관리직 승진이 아닌 기술/전문직 경력 경로를 선택할 수 있다: 전문위원(과장급), 수석전문위원(차장급), 펠로우(부장급). 직무 등급은 동일하게 적용하되, 관리 책임 대신 기술 기여를 평가한다.',
    '{"tags":["직급","호칭","직무등급","전문직","관리직","펠로우","직급체계"],"category":"인사관리","doc_category":"성과관리","importance":"high"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- [문서 9] 평가 이의 신청 절차
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '평가 이의 신청 절차',
    'policy',
    'ko',
    '제1조(이의 신청 자격) 성과평가 결과에 이의가 있는 모든 직원은 이의 신청을 할 수 있다. 제2조(신청 기간) 평가 결과 통보일로부터 10영업일 이내에 「평가 이의 신청서」를 인사팀에 제출한다. 제3조(신청 사유) (1) 평가 기준 또는 절차의 부당한 적용. (2) 목표 변경 미반영 등 사실 관계 오류. (3) 평가자의 편향·차별적 평가에 대한 합리적 의심. (4) 다면평가 결과와 현저히 괴리되는 등급 부여. 제4조(재심 절차) (1) 인사팀은 이의 신청 접수 후 5영업일 이내에 재심 위원회를 구성한다. (2) 재심 위원회: 인사팀장(위원장), 해당 부서 외 부서장 2인, 노사협의회 근로자 위원 1인. (3) 재심 위원회는 평가 기록, 목표 달성 증빙, 양측 면담 결과를 검토한다. (4) 재심 결과: ①등급 유지 ②등급 조정(상향 또는 하향) ③재평가 명령. (5) 재심 결과는 10영업일 이내에 서면 통보하며, 재심 결정에 대해서는 추가 이의 신청이 불가하다.',
    '{"tags":["이의신청","재심","평가결과","부당평가","재심위원회","등급조정"],"category":"성과관리","doc_category":"성과관리","importance":"high"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- [문서 10] 중간 성과 점검 (멀티청크 2개)
DO $$
DECLARE parent_id BIGINT;
BEGIN
    INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
    VALUES (
        1,
        '중간 성과 점검',
        'manual',
        'ko',
        '제1조(목적) 분기별 중간 점검을 통해 목표 달성 진척도를 확인하고, 필요 시 목표를 수정하며, 적시에 코칭을 제공한다. 제2조(점검 주기) 매 분기 말(4월, 7월, 10월) 1차 평가자와 피평가자 간 30분~1시간의 1:1 면담을 실시한다. 제3조(점검 내용) (1) 목표별 달성률 점검(정량 지표 확인). (2) 주요 성과 및 도전 과제 공유. (3) 목표 수정 필요 여부 논의(사업 환경 변화, 조직 개편 등). (4) 역량 발휘 상황 및 개선 코칭. (5) 상호 기대 사항 조율. 제4조(기록 방법) 성과관리 시스템의 「분기 점검」 메뉴에서 다음 항목을 기록한다: ①점검 일시 ②목표별 진척률(%) ③핵심 성과 요약 ④수정 목표(있을 경우) ⑤코칭 내용 ⑥다음 분기 주요 과제.',
        '{"tags":["중간점검","분기별","코칭","목표수정","1:1면담","진척도"],"category":"성과관리","doc_category":"성과관리","importance":"high"}',
        NULL, 'text-embedding-3-small', false, 0, 2, NULL, 'sql_import', 'rag_knowledge',
        NULL
    ) RETURNING id INTO parent_id;

    INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
    VALUES (
        1,
        '중간 성과 점검',
        'manual',
        'ko',
        '제5조(목표 수정 절차) (1) 사업 환경 변화, 조직 개편, 직무 변경 등으로 기존 목표 유지가 부적절한 경우 수정할 수 있다. (2) 수정 범위: 목표 내용 변경, 가중치 조정, 목표 추가·삭제(최소 3개 유지). (3) 수정 절차: 피평가자가 수정안 작성 → 1차 평가자 승인 → 인사팀 확인. (4) 수정 이력은 연말 최종 평가 시 참고 자료로 활용된다. 제6조(코칭 의무) (1) 1차 평가자는 분기 점검 외에도 월 1회 이상 비공식 코칭(점심 면담, 업무 대화 등)을 실시하도록 권장한다. (2) 피평가자의 성과가 목표 대비 현저히 저조한 경우(분기 달성률 50% 미만), 1차 평가자는 즉시 개선 코칭을 실시하고 그 내용을 기록한다. (3) 코칭 기록은 연말 평가의 참고 자료가 되며, 평가자의 리더십 평가 항목에도 반영된다. 제7조(미실시 제재) 분기 점검을 정당한 사유 없이 미실시한 1차 평가자는 리더십 평가에서 감점 처리된다.',
        '{"tags":["목표수정","코칭의무","비공식코칭","달성률","미실시제재","리더십"],"category":"성과관리","doc_category":"성과관리","importance":"high"}',
        NULL, 'text-embedding-3-small', false, 1, 2, parent_id, 'sql_import', 'rag_knowledge', NULL
    );
END $$;

-- [문서 11] 신입사원 평가 특칙
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '신입사원 평가 특칙',
    'policy',
    'ko',
    '제1조(수습 기간 평가) (1) 신입사원은 입사 후 3개월간 수습 기간을 거치며, 수습 종료 시 별도의 수습 평가를 실시한다. (2) 수습 평가 항목: 직무 적응도(30%), 업무 이해도(30%), 태도·근무 자세(20%), 팀 협업(20%). (3) 수습 평가 등급: 적합/조건부 적합/부적합. 부적합 판정 시 수습 기간을 1개월 연장하거나 계약 해지할 수 있다. 제2조(첫 연도 성과평가) (1) 입사일 기준 6개월 미만 재직 시: 성과평가 면제, B등급 자동 부여. (2) 6개월 이상 재직 시: 정상 평가 대상이나, 목표 설정 시점이 늦은 점을 감안하여 달성률 기준을 10% 하향 조정한다. (3) 강제배분에서 신입사원은 별도 풀(pool)로 관리하며, 기존 직원의 등급 배분에 영향을 주지 않는다. 제3조(온보딩 평가) 입사 1개월, 3개월, 6개월 시점에 멘토(또는 팀장)가 온보딩 체크리스트를 기반으로 적응 상황을 점검하고 인사팀에 보고한다.',
    '{"tags":["신입사원","수습평가","온보딩","첫연도","적응","멘토","체크리스트"],"category":"성과관리","doc_category":"성과관리","importance":"medium"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- [문서 12] 장기 교육 파견 중 평가 처리
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '장기 교육 파견 중 평가 처리',
    'policy',
    'ko',
    '제1조(평가 면제 조건) 3개월 이상의 장기 교육(석·박사 과정, 해외 연수, 사내 MBA 등)에 파견된 직원은 해당 기간의 성과평가를 면제받을 수 있다. 제2조(대체 평가) (1) 교육 파견 기간이 6개월 미만인 경우: 파견 전 재직 기간의 성과를 기반으로 평가하되, 등급은 B등급을 하한으로 보장한다. (2) 6개월 이상인 경우: 평가 면제, 전년도 등급 유지 또는 B등급 중 유리한 것을 적용. (3) 교육 성과(학점, 연구 결과, 자격증 취득)를 복귀 후 첫 번째 평가 시 가산점으로 반영할 수 있다(최대 10%). 제3조(성과급 처리) (1) 평가 면제 기간의 성과급: 적용 등급에 해당하는 금액의 80%를 지급한다. (2) 팀 성과급: 파견 기간 중 소속 팀의 팀 성과급을 비례 지급한다. 제4조(복귀 후 목표) 교육 복귀 후 1개월 이내에 학습 결과를 반영한 업무 목표를 재설정하며, 교육 성과의 현업 적용 계획을 포함하여야 한다.',
    '{"tags":["교육파견","평가면제","대체평가","석박사","해외연수","복귀","성과급"],"category":"성과관리","doc_category":"성과관리","importance":"medium"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- [문서 13] 성과관리 시스템 사용 방법
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '성과관리 시스템 사용 방법',
    'manual',
    'ko',
    '제1조(시스템 접속) (1) URL: https://pms.company.com (사내망) 또는 VPN 접속 후 이용. (2) 로그인: SSO(사번 + 통합 비밀번호). (3) 모바일: 사내 앱 > 성과관리 메뉴에서도 접속 가능. 제2조(목표 등록) (1) 메뉴: 나의 성과 > 목표 설정 > 신규 목표 등록. (2) 입력 항목: 목표명, 목표 설명, KPI(핵심 성과 지표), 측정 방법, 목표 값, 가중치(%), 완료 기한. (3) 상위 목표 매핑: 팀/부서 목표 드롭다운에서 선택. (4) 저장 후 1차 평가자에게 자동 결재 요청. 제3조(중간 점검 기록) 분기 점검 시: 나의 성과 > 분기 점검 > 해당 분기 선택 > 목표별 진척률 입력 + 점검 코멘트 작성. 제4조(자기 평가) 12월 평가 기간: 나의 성과 > 연말 평가 > 자기 평가 탭 > 목표별 달성 결과 기술 + 역량 평가 자기 진단. 제5조(최종 평가 제출) 1차 평가자: 팀원 평가 > 대상자 선택 > 목표별 점수 + 등급 + 코멘트 입력 > 제출. 2차 평가자: 부서 평가 > 조정 > 최종 등급 확정. 제6조(결과 조회) 평가 확정 후: 나의 성과 > 평가 결과에서 등급, 점수, 코멘트, 연봉 반영 내역을 확인할 수 있다.',
    '{"tags":["성과관리시스템","PMS","목표등록","자기평가","중간점검","시스템사용"],"category":"시스템안내","doc_category":"성과관리","importance":"medium"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- [문서 14] 팀장급 이상 리더십 평가
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '팀장급 이상 리더십 평가',
    'policy',
    'ko',
    '제1조(대상) 팀장, 실장, 본부장 등 1인 이상의 부하 직원을 관리하는 직책자를 대상으로 한다. 제2조(리더십 평가 항목) (1) 비전 제시 및 방향 설정(20%): 팀 목표의 명확한 공유, 전략적 의사결정. (2) 구성원 육성(25%): 코칭, 피드백, 경력 개발 지원, 교육 기회 제공. (3) 소통 및 동기부여(25%): 적극적 경청, 투명한 소통, 공정한 업무 배분. (4) 성과 관리(15%): 목표 관리, 적시 피드백, 공정한 평가. (5) 조직 문화(15%): 포용적 환경 조성, 갈등 관리, 워라밸 존중. 제3조(평가 방법) (1) 상향 평가(부하 직원 설문): 60% 반영. (2) 상위 평가(차상위자): 30% 반영. (3) 자기 평가: 10% 반영(참고용). 제4조(결과 활용) (1) 리더십 평가 결과는 전체 성과평가에서 20% 비중으로 반영(업적 60% + 역량 20% + 리더십 20%). (2) 3.5점 이상(5점 만점): 리더십 우수 인정. (3) 3.0~3.4점: 개선 코칭 프로그램 참여 권고. (4) 3.0점 미만: 리더십 개선 프로그램 의무 참여. 2년 연속 시 보직 해임 심의.',
    '{"tags":["리더십평가","팀장","상향평가","구성원육성","소통","보직해임"],"category":"성과관리","doc_category":"성과관리","importance":"high"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- [문서 15] 프로젝트 기반 성과 인정
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '프로젝트 기반 성과 인정',
    'policy',
    'ko',
    '제1조(프로젝트 성과 인정 기준) (1) 전사 전략 프로젝트, 신사업 추진, 대형 고객 수주 등 정규 업무 외 프로젝트에 참여하여 성과를 낸 경우, 해당 기여를 성과평가에 반영한다. (2) 프로젝트 참여 기간이 3개월 이상이고, 프로젝트 리더의 기여도 확인을 받아야 한다. 제2조(기여도 산정) (1) 프로젝트 리더가 참여 인원별 기여도(%)를 산정하여 인사팀에 보고한다. (2) 기여도 수준: 핵심(30% 이상), 주요(15~29%), 보조(15% 미만). 제3조(평가 반영 방법) (1) 프로젝트 성과는 MBO의 '개선 목표' 또는 별도 '프로젝트 목표'로 등록한다. (2) 프로젝트 목표 가중치: 전체 MBO의 10~20% 범위. (3) 초과 성과 가산: 프로젝트가 기대 이상의 성과를 달성한 경우 최종 업적 점수에 최대 5점(100점 만점 기준) 가산. 제4조(포상 연계) 프로젝트 성공 기여자에 대해 별도 포상(포상금 50~200만원, 포상 휴가 1~3일)을 수여할 수 있으며, 이는 정기 평가 포상과 중복 적용 가능하다.',
    '{"tags":["프로젝트","성과인정","기여도","가산점","포상","MBO"],"category":"성과관리","doc_category":"성과관리","importance":"medium"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- [문서 16] 저성과자 관리 제도 (멀티청크 2개)
DO $$
DECLARE parent_id BIGINT;
BEGIN
    INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
    VALUES (
        1,
        '저성과자 관리 제도',
        'policy',
        'ko',
        '제1조(정의) 저성과자란 연간 성과평가에서 D등급을 받은 직원 또는 2년 연속 C등급 이하를 받은 직원을 말한다. 제2조(PIP 프로그램) (1) PIP(Performance Improvement Plan)은 저성과자의 성과 개선을 지원하기 위한 구조화된 프로그램이다. (2) PIP 기간: 3개월(1회 연장 가능, 최대 6개월). (3) PIP 시작 전 1차 평가자와 피평가자 간 면담을 통해 「PIP 계획서」를 공동 작성한다. 제3조(PIP 계획서 내용) (1) 현재 성과 수준 진단: 미달 항목, 원인 분석. (2) 개선 목표: SMART 기준으로 2~3개 설정. (3) 지원 계획: 추가 교육, 멘토링, 업무 조정 등. (4) 점검 일정: 2주마다 1:1 면담. (5) 달성 기준: PIP 종료 시 C등급(보통) 이상 수준.',
        '{"tags":["저성과자","PIP","성과개선","D등급","면담","계획서"],"category":"성과관리","doc_category":"성과관리","importance":"high"}',
        NULL, 'text-embedding-3-small', false, 0, 2, NULL, 'sql_import', 'rag_knowledge',
        NULL
    ) RETURNING id INTO parent_id;

    INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
    VALUES (
        1,
        '저성과자 관리 제도',
        'policy',
        'ko',
        '제4조(PIP 기간 중 지원) (1) 1차 평가자는 2주마다 진척 점검 면담을 실시하고 기록한다. (2) 인사팀은 필요 시 외부 코칭, 직무 교육, 부서 이동 등을 지원한다. (3) PIP 대상자의 업무량은 기존의 80% 수준으로 조정하여 개선에 집중할 수 있도록 한다. 제5조(PIP 종료 후 조치) (1) 개선 성공(C등급 이상 달성): PIP 종료, 정상 평가 체계로 복귀. (2) 부분 개선(D등급이나 이전 대비 향상): PIP 3개월 연장(최대 1회). (3) 미개선(개선 노력 미흡 또는 동일 수준 유지): 전환배치 또는 권고사직을 검토할 수 있다. 제6조(권리 보호) (1) PIP 대상자에게 불이익한 처우(급여 삭감, 격리 배치 등)를 해서는 안 된다. (2) PIP 대상자는 노동조합 또는 근로자 대표에게 조력을 요청할 수 있다. (3) PIP 관련 모든 문서는 인사팀에서 5년간 보관하며, 당사자의 열람 요청 시 즉시 제공한다. 제7조(예방 활동) 연중 2회 이상 성과 부진 조짐이 보이는 직원에 대해 사전 코칭을 실시하며, PIP 전 단계로 관리한다.',
        '{"tags":["PIP종료","전환배치","권고사직","권리보호","노동조합","예방"],"category":"성과관리","doc_category":"성과관리","importance":"high"}',
        NULL, 'text-embedding-3-small', false, 1, 2, parent_id, 'sql_import', 'rag_knowledge', NULL
    );
END $$;

-- [문서 17] 우수 인재 Fast Track 제도
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '우수 인재 Fast Track 제도',
    'policy',
    'ko',
    '제1조(정의) Fast Track은 탁월한 성과와 잠재력을 보유한 우수 인재의 조기 성장을 지원하기 위한 가속 육성 프로그램이다. 제2조(선발 기준) (1) 최근 2년 연속 S등급 또는 A등급(1회 S 포함). (2) 직급별 기대 역량 수준을 초과하는 역량 평가 결과. (3) 1차·2차 평가자의 공동 추천. (4) 인사위원회 최종 선정(전사 인원의 5% 이내). 제3조(혜택) (1) 조기 승진: 직급 체류 기간 1년 단축. (2) 핵심 프로젝트 우선 배정: 전사 전략 프로젝트, 해외 사업 참여 기회 제공. (3) 경영진 멘토링: 임원급 멘토 1인 배정(분기 1회 멘토링 세션). (4) 특별 교육: MBA 과정, 해외 연수, 리더십 아카데미 우선 선발. (5) 연봉 특별 인상: 정기 인상 외 추가 5~10% 인상. 제4조(유지 조건) (1) Fast Track 선정 후 매년 평가 시 A등급 이상을 유지하여야 한다. (2) B등급 이하 시 Fast Track에서 해제되며, 1년 후 재진입 가능. (3) Fast Track 기간: 최대 3년, 이후 자동 종료.',
    '{"tags":["FastTrack","우수인재","조기승진","멘토링","가속육성","핵심프로젝트"],"category":"인재관리","doc_category":"성과관리","importance":"high"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- [문서 18] 연봉 조정 절차
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '연봉 조정 절차',
    'policy',
    'ko',
    '제1조(조정 시기) 연봉 조정은 매년 2월에 실시하며, 3월 급여부터 적용한다. 제2조(조정 기준) (1) 전사 기본 인상률: 경영 실적, 물가 상승률, 업계 동향을 종합 고려하여 대표이사가 결정(경영회의 심의). (2) 등급별 차등 인상률: S등급 기본인상률 + 5%p, A등급 +3%p, B등급 기본인상률, C등급 기본인상률 -2%p, D등급 동결. (3) 예시(기본 인상률 3% 가정): S 8%, A 6%, B 3%, C 1%, D 0%. 제3조(최저·최고 한도) (1) 연봉 인상률 상한: 15%(특별 승진·Fast Track 포함). (2) 연봉 인하는 원칙적으로 불가하나, 2년 연속 D등급 시 최대 5%까지 조정 가능(노사 합의 필요). 제4조(연봉 계약) (1) 인상 확정 후 3월 15일까지 전자 연봉 계약서에 서명한다. (2) 미서명 시에도 조정된 연봉이 적용되나, 인사 기록상 '미동의'로 표기된다. (3) 연봉 정보는 엄격한 비밀로 관리되며, 타인에게 공개할 수 없다. 제5조(이의 제기) 연봉 조정 결과에 이의가 있는 경우 3월 31일까지 인사팀에 서면으로 이의 제기할 수 있으며, 인사위원회에서 검토 후 결과를 통보한다.',
    '{"tags":["연봉조정","인상률","등급별","연봉계약","비밀","이의제기"],"category":"보상관리","doc_category":"성과관리","importance":"critical"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- [문서 19] 성과평가 FAQ
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '성과평가 FAQ',
    'faq',
    'ko',
    'Q1. 평가 등급에 불만이 있으면 어떻게 하나요? A1. 결과 통보 후 10영업일 이내에 평가 이의 신청서를 인사팀에 제출하면 재심 위원회에서 검토합니다.
Q2. 중간에 부서를 이동하면 평가는 어떻게 되나요? A2. 이동 전·후 부서에서 재직 기간 비례로 각각 평가하며, 가중 평균으로 최종 등급을 산정합니다.
Q3. 육아휴직 중인데 평가는 어떻게 되나요? A3. 실 근무 6개월 미만 시 평가 면제이며, 전년도 등급을 유지합니다. 성과급도 해당 등급 기준 80%를 수령합니다.
Q4. MBO 목표를 연중에 바꿀 수 있나요? A4. 분기 점검 시 1차 평가자 승인 하에 변경 가능합니다. 단, 최소 3개 목표는 유지해야 합니다.
Q5. 강제배분이 있으면 우리 팀에 S등급을 줄 수 없는 건가요? A5. 부서 규모 10인 미만이면 부서 간 통합 조정이 가능하여, 소규모 팀도 S등급 부여가 가능합니다.
Q6. 다면평가 결과가 나쁘면 등급에 영향을 주나요? A6. 다면평가는 참고 자료이며 등급에 직접 반영되지 않습니다. 단, 팀장의 리더십 평가에서 3.0 미만 시 별도 조치가 있습니다.
Q7. PIP 대상이 되면 해고되나요? A7. PIP는 성과 개선 지원 프로그램이며, 즉시 해고 사유가 아닙니다. 3~6개월간 코칭과 지원을 받으며 개선할 기회가 주어집니다.
Q8. 성과급은 언제 지급되나요? A8. 개인 성과급은 3월, 팀 성과급은 7월·1월, 경영성과급은 3월에 지급됩니다.
Q9. Fast Track에 선정되려면 어떻게 해야 하나요? A9. 2년 연속 S 또는 A등급(1회 S 포함)을 받고, 평가자 추천을 받아야 합니다. 전사 5% 이내로 선정됩니다.
Q10. 프로젝트 참여 성과는 어떻게 인정받나요? A10. 프로젝트 리더의 기여도 확인을 받아 MBO 목표에 등록하면 업적 평가에 반영됩니다.
Q11. 직급 파괴 호칭을 사용하면 승진에 영향이 있나요? A11. 호칭과 직급은 별도 관리되므로, 프로(Pro) 호칭을 사용해도 승진 체계에 영향 없습니다.
Q12. 연봉 정보를 동료와 공유해도 되나요? A12. 연봉 정보는 엄격한 비밀로 관리되며 타인에게 공개할 수 없습니다. 단, 근로기준법상 금지는 아닙니다.',
    '{"tags":["성과평가","FAQ","이의신청","강제배분","PIP","성과급","Fast Track"],"category":"성과관리","doc_category":"FAQ","importance":"high"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- [문서 20] 팀 성과 vs 개인 성과 배분 원칙
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '팀 성과 vs 개인 성과 배분 원칙',
    'policy',
    'ko',
    '제1조(배분 비율) (1) 일반 직원: 개인 성과 80% + 팀 성과 20%. (2) 팀장: 개인 성과 50% + 팀 성과 50%. (3) 부서장: 개인 성과 30% + 팀 성과 40% + 전사 성과 30%. 제2조(팀 성과 지표) (1) 팀 목표 달성률: 팀 MBO 기준 종합 달성률. (2) 팀 협업 지수: 타 부서 협업 만족도 설문 결과. (3) 팀 생산성: 1인당 산출물 또는 매출. 제3조(개인 기여도 차등) (1) 팀 성과급 총액은 팀 성과 등급에 따라 결정되나, 팀원 간 배분은 개인 기여도를 반영한다. (2) 팀장이 기여도 차등 배분안을 작성하며, 차등 폭은 ±20% 이내로 한다. (3) 팀원 전원 동의(서명) 후 인사팀에 제출한다. 제4조(무임승차 방지) (1) 팀 성과에 현저히 기여하지 않은 팀원(기여도 최하위)에 대해 팀장은 사유를 명시하여 팀 성과급을 50%까지 감액할 수 있다. (2) 해당 직원은 감액 사유에 대해 이의 신청할 수 있으며, 인사팀이 중재한다. 제5조(예외) 1인 부서, 신설 팀(6개월 미만)은 팀 성과 비중을 10%로 축소하고, 개인 성과 비중을 확대한다.',
    '{"tags":["팀성과","개인성과","배분비율","기여도","무임승차","차등배분"],"category":"성과관리","doc_category":"성과관리","importance":"high"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- original_content = content 동기화 (INSERT 후 실행)
UPDATE tb_docs SET original_content = content
WHERE source_type = 'sql_import' AND usage_type = 'rag_knowledge' AND original_content IS NULL;
