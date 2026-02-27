-- ============================================================
-- RAG 문서 데이터 - Part 02: 복지/혜택/지원금 제도
-- 총 문서 수: 20개 (논리적 문서), 멀티청크 포함 총 28행
-- 생성일: 2026-02-27
-- 용도: RAG 검색 테스트 (RAGAS 평가용)
-- ============================================================

-- [문서 1] 건강검진 지원 제도 (멀티청크 2개)
DO $$
DECLARE parent_id BIGINT;
BEGIN
    INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
    VALUES (
        1,
        '건강검진 지원 제도',
        'policy',
        'ko',
        '제1조(대상 및 주기) (1) 전 직원(정규직, 1년 이상 계약직)은 매년 1회 종합건강검진을 받을 수 있다. (2) 만 35세 이상 직원은 정밀 검진(위내시경, 대장내시경 포함)을 실시하며, 만 40세 이상은 암 검진 항목을 추가한다. (3) 검진 주기: 만 34세 이하 격년, 만 35세 이상 매년. 단, 전년도 검진 결과 이상 소견이 있는 경우 연령에 관계없이 매년 실시한다. 제2조(지원 금액) (1) 회사 지정 검진 기관 이용 시: 전액 회사 부담(기본 검진 패키지 한도 내). (2) 비지정 기관 이용 시: 기본 검진 비용 상한(남성 40만원, 여성 50만원) 내에서 사후 정산. (3) 추가 선택 항목(MRI, CT, 유전자 검사 등): 본인 부담. 단, 의사 권고에 의한 추가 검사는 50%까지 회사가 지원한다. 제3조(검진 휴가) 검진 당일 1일 유급 검진 휴가를 부여하며, 정밀 검진(수면내시경 등)의 경우 당일 + 익일 오전 반차를 추가 부여한다.',
        '{"tags":["건강검진","종합검진","정밀검진","암검진","검진기관","검진휴가"],"category":"건강관리","doc_category":"복지제도","importance":"high"}',
        NULL, 'text-embedding-3-small', false, 0, 2, NULL, 'sql_import', 'rag_knowledge',
        NULL
    ) RETURNING id INTO parent_id;

    INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
    VALUES (
        1,
        '건강검진 지원 제도',
        'policy',
        'ko',
        '제4조(가족 검진 지원) (1) 직원의 배우자에게 연 1회 기본 검진비(상한 30만원)를 지원한다. (2) 직원의 직계 존속(부모)에게 격년 1회 기본 검진비(상한 25만원)를 지원한다. (3) 가족 검진은 직원 본인이 HR시스템에서 대리 신청하며, 검진 완료 후 영수증과 가족관계증명서를 제출한다. 제5조(사후 관리) (1) 검진 결과 이상 소견이 발견된 직원은 3개월 이내에 재검 또는 치료를 받아야 하며, 회사는 해당 직원의 치료비를 의료비 지원 한도 내에서 지원한다. (2) 직업성 질환이 의심되는 경우 산업보건의와 상담을 의무적으로 실시한다. (3) 검진 결과는 개인정보로서 엄격하게 관리되며, 인사팀 담당자와 산업보건의만 열람 가능하다. 본인 동의 없이 제3자(팀장 포함)에게 공개하지 않는다. 제6조(신청 기간) 매년 1월~11월 중 자유롭게 예약하되, 12월 15일까지 미수검 시 해당 연도 지원이 소멸된다.',
        '{"tags":["가족검진","배우자","부모","사후관리","개인정보","검진결과"],"category":"건강관리","doc_category":"복지제도","importance":"high"}',
        NULL, 'text-embedding-3-small', false, 1, 2, parent_id, 'sql_import', 'rag_knowledge', NULL
    );
END $$;

-- [문서 2] 의료비 지원 제도
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '의료비 지원 제도',
    'policy',
    'ko',
    '제1조(지원 대상) 정규직 직원 및 그 배우자, 직계 존비속(부모, 자녀)의 의료비를 지원한다. 제2조(지원 범위 및 한도) (1) 본인 의료비: 연간 300만원 한도 내에서 건강보험 본인부담금의 80%를 지원한다. (2) 배우자 의료비: 연간 200만원 한도 내 본인부담금의 70%. (3) 자녀 의료비: 자녀 1인당 연간 150만원 한도 내 본인부담금의 70%. (4) 부모 의료비: 부모 1인당 연간 100만원 한도 내 본인부담금의 50%. 제3조(지원 제외) (1) 미용·성형 목적 의료비 (2) 건강보험 비급여 항목 중 선택진료비 (3) 해외 의료비(해외 파견자 별도 규정 적용) (4) 한방 치료비(침, 한약) 중 월 30만원 초과분. 제4조(신청 절차) (1) 치료 완료 후 60일 이내에 HR시스템 > 복지 > 의료비 청구에서 신청. (2) 첨부 서류: 진료비 영수증, 처방전 사본, 가족관계증명서(가족 의료비). (3) 인사팀 검토 후 익월 급여일에 지급한다. 제5조(중대 질병 특례) 암, 뇌혈관질환, 심장질환 등 중대 질병 진단 시 연간 한도를 500만원으로 상향하며, 별도 심의를 거쳐 추가 지원 가능하다.',
    '{"tags":["의료비","건강보험","본인부담금","가족의료비","중대질병","지원한도"],"category":"건강관리","doc_category":"복지제도","importance":"high"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- [문서 3] 자녀 학자금 지원
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '자녀 학자금 지원',
    'policy',
    'ko',
    '제1조(지원 대상) 재직 1년 이상 정규직 직원의 직계 자녀(법적 양자 포함)에 대해 학자금을 지원한다. 제2조(지원 금액) (1) 유치원·어린이집: 월 20만원 한도(만 3세~취학 전). (2) 초등학교: 학기당 30만원(교육비, 급식비 포함). (3) 중학교: 학기당 50만원. (4) 고등학교: 학기당 100만원(입학금 별도 실비 지원). (5) 대학교: 학기당 300만원 한도 내 등록금 실비(국공립/사립 구분 없음). 제3조(지원 제한) (1) 동일 자녀에 대해 부모 모두 당사 재직 시, 1인만 지원 신청 가능. (2) 자녀 2인까지 지원하며, 3인 이상은 다자녀 특례(100% 지원)를 적용한다. (3) 대학 재학 중 휴학 학기는 지원하지 않으며, 편입·재입학 시 잔여 학기분을 지원한다. (4) 대학원 학자금은 지원하지 않으나, 직무 관련 석사과정은 자기개발비 지원 제도를 활용할 수 있다. 제4조(신청) 매 학기 시작 1개월 전까지 「학자금 지원 신청서」 + 재학증명서 + 등록금 고지서를 제출한다. 지급은 등록 기간 내 직접 납부 후 실비 정산 방식으로 처리한다.',
    '{"tags":["학자금","자녀교육","초중고","대학","등록금","다자녀","유치원"],"category":"교육지원","doc_category":"복지제도","importance":"high"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- [문서 4] 주택 지원 제도
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '주택 지원 제도',
    'policy',
    'ko',
    '제1조(사택 제공) (1) 지방 발령, 해외 전입 등으로 거주지 이전이 필요한 직원에게 사택을 제공한다. (2) 사택 유형: 원룸(단신), 2룸(가족), 관사(임원급). (3) 사택 입주 기간: 발령일로부터 최대 2년, 1회 연장 가능(총 3년). (4) 사택비는 회사가 전액 부담하되, 관리비·공과금은 입주자가 부담한다. 제2조(전세 자금 대출 지원) (1) 재직 3년 이상 무주택 직원에게 전세 자금 대출 이자를 지원한다. (2) 지원 한도: 대출금 1억원 이내, 이자 연 2% 한도(실 이자율 차액 회사 부담). (3) 지원 기간: 최대 5년, 중도 퇴직 시 잔여 지원은 즉시 중단. (4) 대출 실행 후 6개월 이내에 전입신고 확인서를 제출한다. 제3조(주거 지원금) (1) 사택·전세 지원 대상이 아닌 무주택 직원에게 월 20만원의 주거 지원금을 지급한다(수도권 기준, 비수도권 15만원). (2) 지원 기간: 입사 후 3년까지. (3) 자가 보유자, 배우자 명의 주택 보유자는 지원 제외. 제4조(신청 우선순위) 무주택 기간, 부양가족 수, 직급을 종합 고려하여 우선순위를 정하며, 동순위 시 근속 연수가 긴 직원을 우선한다.',
    '{"tags":["주택","사택","전세","대출","주거지원금","무주택","발령"],"category":"주거지원","doc_category":"복지제도","importance":"high"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- [문서 5] 통근 교통비 지원 (멀티청크 2개)
DO $$
DECLARE parent_id BIGINT;
BEGIN
    INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
    VALUES (
        1,
        '통근 교통비 지원',
        'policy',
        'ko',
        '제1조(지원 대상) 자택에서 사업장까지의 편도 거리가 10km 이상인 전 직원에게 통근 교통비를 지원한다. 제2조(대중교통 이용자) (1) 실비 정산 방식: 교통카드 사용 내역을 기준으로 월별 정산한다. (2) 월 상한: 15만원(수도권), 10만원(비수도권). (3) 정산 방법: 매월 말일까지 교통카드 이용 내역서를 HR시스템에 업로드하면 익월 급여에 반영된다. (4) 통근 정기권(월정기 교통카드) 이용 시 정기권 금액을 직접 지원한다. 제3조(자가용 이용자) (1) 편도 20km 이상 자가용 통근자에게 자가운전보조금을 지급한다. (2) 월 지급액: 비과세 한도 내 월 20만원 정액 지급. (3) 자가운전보조금과 대중교통비는 중복 지급되지 않는다. (4) 차량 등록증 사본 제출이 필요하며, 본인 명의 또는 배우자 명의 차량에 한한다.',
        '{"tags":["교통비","통근","대중교통","자가용","자가운전보조금","실비정산"],"category":"교통지원","doc_category":"복지제도","importance":"medium"}',
        NULL, 'text-embedding-3-small', false, 0, 2, NULL, 'sql_import', 'rag_knowledge',
        NULL
    ) RETURNING id INTO parent_id;

    INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
    VALUES (
        1,
        '통근 교통비 지원',
        'policy',
        'ko',
        '제4조(통근 셔틀버스) (1) 주요 거점(강남역, 판교역, 구로디지털단지역)에서 사업장까지 통근 셔틀버스를 운행한다. (2) 운행 시간: 출근 08:00/08:30, 퇴근 18:00/18:30/19:00 (3회 운행). (3) 셔틀버스 이용자는 별도 교통비를 지급하지 않으나, 야근(20:00 이후)으로 셔틀을 이용하지 못한 경우 택시비를 실비 정산한다. 제5조(야간·긴급 교통비) (1) 22:00 이후 퇴근 시 택시비를 실비 지원한다(영수증 첨부, 월 10회 한도). (2) 회사 긴급 호출에 의한 출근 시 교통비 전액을 지원하며, 자가용 이용 시 주차비를 포함한다. 제6조(출장·외근 교통비) 출장·외근 시 발생하는 교통비는 통근 교통비와 별도로 출장 규정에 따라 처리한다. 제7조(재택근무) 재택근무일의 교통비는 지급하지 않으며, 주 2일 이상 재택근무 시 교통비를 근무일수에 비례하여 감액한다.',
        '{"tags":["셔틀버스","야간교통비","택시비","출장교통비","재택근무","긴급호출"],"category":"교통지원","doc_category":"복지제도","importance":"medium"}',
        NULL, 'text-embedding-3-small', false, 1, 2, parent_id, 'sql_import', 'rag_knowledge', NULL
    );
END $$;

-- [문서 6] 식대 지원
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '식대 지원',
    'policy',
    'ko',
    '제1조(구내식당) (1) 본사 사업장에 구내식당을 운영하며, 점심 식사를 무료로 제공한다. (2) 식단: 한식 2종, 일식/중식/양식 1종(일별 교체), 샐러드바 상시 운영. (3) 이용 시간: 11:30~13:30. 제2조(외부 식비 지원) (1) 구내식당이 없는 사업장 근무자에게 월 식대 20만원(비과세)을 지급한다. (2) 식대 지급 기준: 실 근무일수 × 1만원(월 상한 20만원). (3) 연차, 병가, 출장 등으로 사업장에서 근무하지 않은 날은 차감된다. 제3조(야간·휴일 근무 식대) (1) 야간근무(18:00 이후 2시간 이상 초과근무): 석식비 1만원 지급. (2) 야간근무(22:00 이후): 야식비 추가 1만원 지급. (3) 휴일근무: 중식비 1만원 + 석식비 1만원(4시간 이상 근무 시). 제4조(재택근무 식대) 재택근무일에는 구내식당 이용이 불가하므로, 재택근무자에게 근무일당 8,000원의 재택 식대를 지급한다. 제5조(특수 상황) 고객 접대, 팀 회식 등 업무상 식사는 법인카드를 사용하며, 본 규정의 식대와 별도로 처리한다.',
    '{"tags":["식대","구내식당","야근식대","휴일근무","재택근무","비과세"],"category":"식비지원","doc_category":"복지제도","importance":"medium"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- [문서 7] 경조사 지원금 규정
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '경조사 지원금 규정',
    'policy',
    'ko',
    '제1조(지원금 기준) (1) 본인 결혼: 50만원 + 화환. (2) 자녀 결혼: 30만원 + 화환. (3) 본인/배우자 출산: 출산축하금 20만원 + 출산용품(10만원 상당). (4) 부모(배우자 부모 포함) 사망: 조의금 50만원 + 조화 + 장례용품 지원. (5) 배우자 사망: 조의금 100만원 + 조화. (6) 자녀 사망: 조의금 100만원 + 조화. (7) 조부모·외조부모 사망: 조의금 20만원 + 조화. (8) 형제·자매(배우자 포함) 사망: 조의금 20만원. (9) 부모 회갑(칠순): 축하금 10만원. (10) 자녀 돌: 축하금 5만원. 제2조(화환·조화) 회사 명의로 발송하며, 비용은 회사가 부담한다(화환 5만원, 조화 10만원 기준). 직원이 별도 규격을 원하는 경우 차액은 본인이 부담한다. 제3조(신청 및 증빙) 경조사 발생 후 14일 이내에 HR시스템에서 신청하며, 증빙(청첩장, 사망진단서, 출생증명서 등)을 첨부한다. 증빙 미제출 시 지급이 보류된다. 제4조(중복 지원 제한) 동일 경조사에 대해 부부 공동 재직 시 1인에게만 지급하되, 상위 금액 기준을 적용한다.',
    '{"tags":["경조사","경조금","결혼","출산","사망","조의금","축하금","화환"],"category":"경조지원","doc_category":"복지제도","importance":"high"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- [문서 8] 동호회 지원 제도
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '동호회 지원 제도',
    'guide',
    'ko',
    '제1조(동호회 등록) (1) 5인 이상의 직원이 모여 동호회를 결성하고, 총무부에 「동호회 등록 신청서」를 제출한다. (2) 등록 조건: 회원 5인 이상, 회장 1인 지정, 회칙 제출, 분기 1회 이상 활동 계획. (3) 등록 가능 분야: 체육(축구, 야구, 배드민턴, 등산 등), 문화(독서, 영화, 음악, 사진 등), 학습(어학, IT, 자격증 등). 제2조(지원금) (1) 분기별 회원 1인당 3만원(분기 최대 30만원, 회원 10인 이상 시 상한 40만원). (2) 연간 총 지원 한도: 동호회 1개당 120만원. (3) 동호회 가입 수 제한: 1인당 최대 2개 동호회 가입 가능. 제3조(사용 범위) (1) 활동 장소 대관료, 용품 구입비, 식음료비에 사용 가능. (2) 금지 사용: 주류 단독 구매, 현금 분배, 도박성 활동, 사행성 오락. 제4조(정산) (1) 분기 종료 후 15일 이내에 활동 보고서(사진, 참석 인원) + 영수증을 총무부에 제출. (2) 미정산 시 다음 분기 지원금이 보류된다. (3) 2분기 연속 활동 미실시 또는 미정산 시 동호회 자격이 취소된다.',
    '{"tags":["동호회","동아리","활동지원","분기지원","체육","문화","학습"],"category":"여가활동","doc_category":"복지제도","importance":"low"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- [문서 9] 자기개발비 지원 (멀티청크 2개)
DO $$
DECLARE parent_id BIGINT;
BEGIN
    INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
    VALUES (
        1,
        '자기개발비 지원',
        'policy',
        'ko',
        '제1조(지원 목적) 직원의 직무 역량 강화 및 자기 계발을 위해 연간 자기개발비를 지원한다. 제2조(지원 대상 및 한도) (1) 전 직원(수습 기간 포함): 연간 100만원 한도. (2) 팀장급 이상: 연간 150만원 한도. (3) 미사용 잔액은 이월되지 않으며, 연말 소멸된다. 제3조(지원 항목) (1) 도서 구입비: 직무 관련·자기개발 도서(전자책 포함), 1회 5만원 한도·연간 무제한(총 한도 내). (2) 온라인 강좌: Udemy, Coursera, 인프런, 패스트캠퍼스 등 온라인 학습 플랫폼 수강료. (3) 자격증 응시료: 직무 관련 자격증 응시료 전액(불합격 시에도 지원). (4) 외부 교육 수강료: 학원, 세미나, 컨퍼런스 등록비. (5) 어학 학습비: 어학원 수강료, 교재비, 온라인 어학 서비스(월정액 포함).',
        '{"tags":["자기개발","도서구입","온라인강좌","자격증","어학","수강료"],"category":"자기개발","doc_category":"복지제도","importance":"high"}',
        NULL, 'text-embedding-3-small', false, 0, 2, NULL, 'sql_import', 'rag_knowledge',
        NULL
    ) RETURNING id INTO parent_id;

    INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
    VALUES (
        1,
        '자기개발비 지원',
        'policy',
        'ko',
        '제4조(지원 제외 항목) (1) 직무와 무관한 취미 강좌(요리, 그림, 악기 연주 등). 단, 사내 동호회 활동과 연계된 경우 동호회 예산에서 처리. (2) 학위 과정(학점은행제, 대학원 등)은 별도 학자금 지원 규정 적용. (3) 이미 보유한 자격증의 갱신 비용(단, 법적 필수 갱신은 지원). 제5조(신청 및 정산) (1) 사전 신청: 교육 시작 전 HR시스템에서 「자기개발비 사전 신청」 등록(과정명, 기간, 비용). (2) 사후 정산: 교육 완료 후 30일 이내에 수료증·영수증을 첨부하여 정산 신청. (3) 도서 구입비는 사전 신청 없이 영수증 정산만으로 처리 가능. (4) 정산 지급: 매월 25일 마감, 익월 급여일 지급. 제6조(의무) (1) 자기개발비로 취득한 자격증·수료증 사본을 인사팀에 제출하여 인사 기록에 반영한다. (2) 10만원 이상 교육 수강 후 1페이지 이상의 학습 후기를 사내 지식 공유 게시판에 작성하도록 권장한다.',
        '{"tags":["자기개발","정산","사전신청","수료증","지식공유","지원제외"],"category":"자기개발","doc_category":"복지제도","importance":"high"}',
        NULL, 'text-embedding-3-small', false, 1, 2, parent_id, 'sql_import', 'rag_knowledge', NULL
    );
END $$;

-- [문서 10] 체력단련 지원
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '체력단련 지원',
    'policy',
    'ko',
    '제1조(헬스장 이용 지원) (1) 사업장 인근 제휴 헬스장 이용권을 월 5만원 한도 내에서 지원한다. (2) 사내 피트니스센터가 있는 사업장의 경우 무료 이용 가능(근무 시간 외). (3) 제휴 헬스장 목록은 인트라넷 > 복지 > 체력단련에서 확인한다. 제2조(스포츠 강좌비) (1) 요가, 필라테스, 수영, 클라이밍 등 스포츠 강좌 월 회비를 월 5만원 한도 내 지원. (2) 헬스장 이용 지원과 합산하여 월 최대 5만원. 제3조(운동 용품 구입비) (1) 연간 20만원 한도 내에서 운동화, 운동복, 스포츠 장비 구입비를 지원. (2) 영수증 제출 방식이며, 브랜드 매장 및 온라인 구매 모두 인정. 제4조(마라톤·체육대회 참가비) 회사 명의로 참가하는 마라톤, 트라이애슬론, 체육대회의 참가비를 전액 지원하며, 유니폼 제작비도 별도 지원한다. 제5조(건강 챌린지) 월 15일 이상 30분 이상 운동 기록을 제출한 직원에게 월 2만원의 건강 포인트를 추가 부여하며, 복지 포인트로 전환 가능하다.',
    '{"tags":["체력단련","헬스장","운동","스포츠","마라톤","건강챌린지","피트니스"],"category":"건강관리","doc_category":"복지제도","importance":"low"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- [문서 11] 직원 할인 혜택
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '직원 할인 혜택',
    'guide',
    'ko',
    '제1조(자사 제품·서비스 할인) (1) 자사 제품을 정가 대비 30% 할인된 가격으로 구매할 수 있다. (2) 직원 할인 구매 수량: 제품당 연간 3개 한도(고가 제품은 1개). (3) 직원 구매 제품의 재판매는 엄격히 금지하며, 적발 시 할인 자격 영구 박탈 및 징계 대상이 된다. 제2조(협력사 할인) (1) 당사와 제휴한 협력사의 제품·서비스를 임직원 특별 할인가로 이용할 수 있다. (2) 주요 제휴처: 통신사(SKT/KT/LG U+ 월 요금 20% 할인), 렌터카(10% 할인), 호텔(법인가 적용), 보험(단체 보험 요율), 가전(임직원 특가). (3) 제휴 혜택 이용 시 사원증 또는 재직증명서를 제시한다. 제3조(사내 매점·카페) (1) 사내 편의점·카페 이용 시 사원증 태깅으로 10% 할인 적용. (2) 월 이용 한도 10만원 이내에서 할인 적용. 제4조(혜택 변경) 제휴 혜택은 협력사 계약에 따라 변경될 수 있으며, 변경 시 사전 공지한다.',
    '{"tags":["직원할인","자사제품","협력사","제휴","통신사","렌터카","호텔"],"category":"직원혜택","doc_category":"복지제도","importance":"low"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- [문서 12] 우수 직원 포상 제도
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '우수 직원 포상 제도',
    'policy',
    'ko',
    '제1조(포상 종류) (1) 월간 우수사원: 매월 각 본부별 1명 선정, 상패 + 상금 30만원 + 포상 휴가 1일. (2) 분기 MVP: 분기별 전사 3명 선정, 상패 + 상금 100만원 + 포상 휴가 3일. (3) 연간 최우수사원: 연 1회 전사 1명 선정, 트로피 + 상금 300만원 + 포상 휴가 5일 + 해외 연수 기회. (4) 특별 공로상: 중대 프로젝트 성공, 위기 대응, 비용 절감 등 특별 기여 시 수시 수여. 제2조(선발 기준) (1) 성과 달성률(40%), 동료 평가(20%), 고객 만족도(20%), 혁신 기여(20%)를 종합 평가. (2) 인사위원회에서 최종 선정하며, 선정 결과에 대한 이의 신청은 불가. 제3조(시상) (1) 월간 우수사원: 매월 첫째 주 월요일 조회에서 시상. (2) 분기 MVP: 분기 말 전사 타운홀 미팅에서 시상. (3) 연간 최우수사원: 창립기념일 행사에서 대표이사가 시상. 제4조(제한) (1) 동일 직원이 연속 2회 월간 우수사원에 선정될 수 없다. (2) 징계 이력이 있는 직원은 징계 후 1년간 포상 대상에서 제외.',
    '{"tags":["포상","우수사원","MVP","공로상","시상","성과","선발기준"],"category":"인사포상","doc_category":"복지제도","importance":"medium"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- [문서 13] 장기 근속 포상
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '장기 근속 포상',
    'policy',
    'ko',
    '제1조(포상 기준) 입사일 기준 근속 연수에 따라 다음과 같이 포상한다. (1) 5년 근속: 감사패 + 상금 50만원 + 리프레시 휴가 3일. (2) 10년 근속: 공로패 + 상금 150만원 + 리프레시 휴가 5일 + 해외 여행 상품권(100만원). (3) 15년 근속: 공로패 + 상금 250만원 + 리프레시 휴가 7일 + 가전제품(100만원 상당). (4) 20년 근속: 공로패 + 상금 400만원 + 리프레시 휴가 10일 + 순금 기념패(20돈). (5) 25년 이상: 대표이사 특별상 + 상금 500만원 + 리프레시 휴가 15일. 제2조(포상 시기) 근속 도래월에 시상하며, 월간 조회 또는 분기 타운홀에서 수여한다. 제3조(근속 산정) (1) 휴직 기간은 근속에서 제외되나, 육아휴직·병역휴직은 근속에 산입한다. (2) 퇴직 후 재입사한 경우 이전 근속은 합산하지 않는다(1년 이내 복직은 예외). 제4조(세금) 포상금은 기타소득으로 처리되며, 22%의 원천징수(소득세 + 지방소득세)가 적용된다.',
    '{"tags":["장기근속","5년","10년","20년","포상금","리프레시","근속산정"],"category":"인사포상","doc_category":"복지제도","importance":"medium"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- [문서 14] 심리 상담 및 EAP 지원 (멀티청크 2개)
DO $$
DECLARE parent_id BIGINT;
BEGIN
    INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
    VALUES (
        1,
        '심리 상담 및 EAP 지원',
        'policy',
        'ko',
        '제1조(EAP 프로그램 개요) (1) EAP(Employee Assistance Program)은 직원과 그 가족의 심리적·정서적 건강을 지원하는 전문 상담 프로그램이다. (2) 외부 전문 상담 기관과 제휴하여 운영하며, 상담 내용은 회사에 일체 보고되지 않는다(절대 비밀 보장). (3) 이용 대상: 전 직원 및 그 동거 가족(배우자, 자녀, 부모). 제2조(상담 종류) (1) 개인 심리 상담: 우울, 불안, 스트레스, 번아웃, 대인관계 등. (2) 부부·가족 상담: 가정 내 갈등, 육아 스트레스, 부부 관계. (3) 법률 상담: 이혼, 상속, 부동산, 노동 분쟁 등(1회 30분 무료). (4) 재무 상담: 부채 관리, 재테크, 은퇴 설계(1회 무료). (5) 직무 스트레스 상담: 직장 내 괴롭힘, 성희롱 피해, 업무 갈등. 제3조(이용 횟수) (1) 심리 상담: 연간 12회(회당 50분) 무료 제공. (2) 법률·재무 상담: 각 연간 4회 무료.',
        '{"tags":["EAP","심리상담","스트레스","번아웃","법률상담","재무상담","비밀보장"],"category":"심리건강","doc_category":"복지제도","importance":"high"}',
        NULL, 'text-embedding-3-small', false, 0, 2, NULL, 'sql_import', 'rag_knowledge',
        NULL
    ) RETURNING id INTO parent_id;

    INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
    VALUES (
        1,
        '심리 상담 및 EAP 지원',
        'policy',
        'ko',
        '제4조(신청 방법) (1) 전화 예약: 제휴 상담센터 대표번호(1588-XXXX)로 직접 예약. (2) 온라인 예약: 제휴 상담센터 웹사이트에서 직원 코드 입력 후 예약. (3) HR 경유 없이 직접 예약하며, 회사는 이용 여부조차 확인하지 않는다. (4) 12회 초과 시 본인 부담으로 추가 상담 가능(회당 5만원, 일반가 10만원의 50% 할인). 제5조(위기 개입) (1) 자살 충동, 심각한 정신건강 위기 시 24시간 긴급 상담 핫라인을 운영한다(365일). (2) 긴급 상담 후 전문 의료기관 연계가 필요한 경우 상담사가 직접 안내하며, 치료비는 의료비 지원 한도와 별도로 연간 200만원까지 추가 지원한다. 제6조(조직 상담) (1) 팀장이 팀 내 갈등 해결을 위해 팀 단위 상담을 요청할 수 있다. (2) 조직 상담은 인사팀을 경유하여 신청하며, 상담 결과 중 구체적 개인 정보는 보고하지 않고 조직 차원의 개선 권고만 전달한다. 제7조(교육) 연 1회 전 직원 대상 정신건강 인식 교육(1시간)을 실시하며, 팀장급 이상은 추가로 「구성원 정신건강 관리 리더십」 교육(2시간)을 이수한다.',
        '{"tags":["EAP","예약방법","위기개입","긴급상담","조직상담","정신건강교육"],"category":"심리건강","doc_category":"복지제도","importance":"high"}',
        NULL, 'text-embedding-3-small', false, 1, 2, parent_id, 'sql_import', 'rag_knowledge', NULL
    );
END $$;

-- [문서 15] 육아 지원 제도
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '육아 지원 제도',
    'policy',
    'ko',
    '제1조(사내 어린이집) (1) 본사 사업장에 사내 어린이집을 운영하며, 만 1세~만 5세 자녀를 대상으로 한다. (2) 입소 기준: 재직 1년 이상, 맞벌이 가정 우선, 다자녀 가정 우선. (3) 보육료: 정부 보육료 지원 후 차액의 50%를 회사가 부담. (4) 운영 시간: 07:30~19:30(긴급 보육 20:00까지 연장 가능). 제2조(보육비 지원) (1) 사내 어린이집 미이용 직원에게 자녀 1인당 월 20만원의 보육비를 지원한다. (2) 만 0세~만 5세 자녀 대상, 어린이집 또는 유치원 재원 증명서 제출 필요. 제3조(육아용품 지원) 출산 시 육아용품 세트(카시트, 유모차 중 택 1, 30만원 상당)를 지급한다. 제4조(육아기 근로시간 단축) (1) 만 8세 이하 자녀를 양육하는 직원은 주당 15~35시간 범위에서 근로시간 단축을 신청할 수 있다(최대 2년). (2) 단축된 시간에 비례하여 급여를 지급하며, 고용보험에서 육아기 근로시간 단축급여를 별도 지원받는다. (3) 단축 근무 형태: 매일 1~3시간 단축 또는 주 3~4일 근무 중 선택. 제5조(유연근무) 초등학교 1~3학년 자녀를 둔 직원은 등교 시간에 맞춰 시차 출퇴근(08:00~10:00 출근)을 활용할 수 있다.',
    '{"tags":["육아","어린이집","보육비","육아용품","근로시간단축","유연근무","시차출퇴근"],"category":"육아지원","doc_category":"복지제도","importance":"high"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- [문서 16] 퇴직금 및 퇴직연금 제도
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '퇴직금 및 퇴직연금 제도',
    'policy',
    'ko',
    '제1조(퇴직금 산정) (1) 1년 이상 계속 근로한 직원이 퇴직 시, 근속 1년에 대해 30일분 이상의 평균임금을 퇴직금으로 지급한다. (2) 평균임금 = 퇴직일 이전 3개월간 지급된 임금 총액 ÷ 해당 기간의 총 일수. (3) 평균임금이 통상임금보다 낮은 경우 통상임금을 기준으로 한다. 제2조(퇴직연금 유형) (1) 확정급여형(DB): 회사가 운용 책임, 퇴직 시 사전에 정해진 급여 수준(근속 × 평균임금)을 보장. (2) 확정기여형(DC): 직원이 운용 책임, 회사는 매년 연간 임금의 1/12 이상을 개인 계좌에 납입. (3) 입사 시 DB형으로 자동 가입되며, 입사 1년 후 DC형으로 전환 신청 가능. 제3조(중간정산) DC형 가입자에 한해 다음 사유 발생 시 중간정산(중도인출) 가능: 무주택자 주택 구입, 본인·가족 6개월 이상 요양, 개인회생, 천재지변. 제4조(운용 현황 조회) 퇴직연금 적립 현황은 가입 운용사(삼성생명/한화생명) 앱 또는 HR시스템에서 실시간 확인 가능하다. 제5조(수령 방법) 퇴직 시 일시금 또는 연금(55세 이상, 10년 이상 가입 시 가능) 중 선택하며, 연금 수령 시 퇴직소득세의 30~40%를 감면받는다.',
    '{"tags":["퇴직금","퇴직연금","DB","DC","중간정산","평균임금","수령방법"],"category":"퇴직관리","doc_category":"복지제도","importance":"critical"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- [문서 17] 단체보험 혜택
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '단체보험 혜택',
    'policy',
    'ko',
    '제1조(가입 대상) 전 정규직 직원은 입사 시 자동으로 단체보험에 가입된다(별도 건강 심사 불필요). 제2조(보장 내용) (1) 사망보험금: 사고 사망 시 1억원, 질병 사망 시 5,000만원. (2) 상해보험: 입원 시 1일당 3만원(최대 180일), 통원 시 회당 2만원. (3) 질병보험: 암 진단금 2,000만원, 뇌혈관/심장질환 진단금 1,000만원. (4) 수술비: 1회당 50만~500만원(수술 종류에 따라 차등). (5) 장해보험: 장해등급에 따라 최대 1억원. 제3조(피부양자 확대) (1) 배우자: 사망보험금 5,000만원, 상해/질병 보장 본인의 50% 수준. (2) 자녀: 사망보험금 1,000만원, 상해/질병 기본 보장. (3) 피부양자 보험료는 회사가 50%, 직원이 50% 부담(급여 공제). 제4조(보험금 청구) (1) 진단서·입퇴원확인서·수술확인서 + 보험금 청구서를 총무팀에 제출. (2) 제출 후 10영업일 이내에 보험사에서 직접 지급. (3) 청구 기한: 사유 발생일로부터 3년 이내. 제5조(퇴직 후) 퇴직 시 단체보험은 자동 해지되며, 개인 보험으로 전환을 희망할 경우 퇴직 후 30일 이내에 보험사에 직접 신청한다.',
    '{"tags":["단체보험","사망보험","상해보험","질병보험","암진단","피부양자","보험청구"],"category":"보험","doc_category":"복지제도","importance":"high"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- [문서 18] 재택근무 지원 물품 및 환경 지원
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '재택근무 지원 물품 및 환경 지원',
    'guide',
    'ko',
    '제1조(지원 장비) (1) 주 2일 이상 정기 재택근무 직원에게 다음 장비를 대여한다: 노트북(업무용), 24인치 이상 모니터, 키보드·마우스 세트, 헤드셋(마이크 포함). (2) 장비는 회사 자산이며, 재택근무 종료 또는 퇴직 시 반납한다. (3) 개인 장비 사용 시 보안 소프트웨어(MDM, VPN 클라이언트) 설치가 의무이며, IT팀의 보안 점검을 받아야 한다. 제2조(통신비) (1) 재택근무 시 인터넷 통신비를 월 3만원 정액 지원한다. (2) 유선 인터넷 미설치 가정의 경우 초기 설치비(1회, 최대 5만원)를 추가 지원. 제3조(사무용품) 인체공학 의자 구매비 30만원 한도(1회), 책상 스탠드·문구류 등 소모품 연 5만원 한도를 지원한다. 제4조(지원 기간) (1) 장비 대여 기간: 재택근무 지정 기간과 동일. (2) 재택근무 종료 후 7일 이내에 모든 장비를 IT팀에 반납한다. (3) 분실·파손 시 감가상각 잔존가를 기준으로 본인이 배상한다. 제5조(보안 환경) 재택근무 공간은 타인(가족 포함)이 업무 화면을 열람하기 어려운 독립된 공간이어야 하며, 화상회의 시 배경 흐림 처리를 권장한다.',
    '{"tags":["재택근무","장비지원","모니터","통신비","사무용품","보안","반납"],"category":"재택지원","doc_category":"복지제도","importance":"medium"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- [문서 19] 복지 포인트 제도
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '복지 포인트 제도',
    'policy',
    'ko',
    '제1조(포인트 부여) (1) 매년 1월 1일에 전 직원에게 연간 복지 포인트를 일괄 부여한다. (2) 부여 기준: 사원·주임 80만 포인트, 대리·과장 100만 포인트, 차장·부장 120만 포인트, 임원 150만 포인트(1포인트 = 1원). (3) 중도 입사자: 입사월 기준 잔여 월수에 비례하여 부여(월할 계산). 제2조(사용 가능 카테고리) (1) 건강·의료: 병원비, 약국비, 건강식품, 영양제. (2) 자기개발: 도서, 온라인 강좌, 어학(자기개발비와 별도). (3) 생활: 마트, 백화점, 온라인 쇼핑, 가전. (4) 여가·문화: 영화, 공연, 여행, 숙박, 항공권. (5) 체력·운동: 헬스장, 스포츠 용품, 골프(그린피 포함). 제3조(사용 제한) (1) 현금 전환 불가. (2) 타인에게 양도 불가(가족 포함). (3) 유흥업소, 사행성 업종에서는 사용 불가. (4) 1회 결제 한도: 50만 포인트. 제4조(이월 및 소멸) (1) 미사용 포인트는 다음 해로 이월되지 않으며, 12월 31일 자정에 소멸된다. (2) 퇴직 시 잔여 포인트는 퇴직일 자동 소멸. 제5조(사용 방법) 제휴 복지몰(이지웰, 베네피아 등) 웹사이트 또는 앱에서 복지 포인트로 결제한다.',
    '{"tags":["복지포인트","포인트","복지몰","이지웰","베네피아","카테고리","소멸"],"category":"복지포인트","doc_category":"복지제도","importance":"high"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- [문서 20] 복지 제도 FAQ
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '복지 제도 FAQ',
    'faq',
    'ko',
    'Q1. 건강검진을 지정 병원이 아닌 곳에서 받아도 되나요? A1. 네, 비지정 기관도 가능하지만 기본 검진 비용 상한(남성 40만원, 여성 50만원) 내에서 사후 정산됩니다.
Q2. 의료비 지원에 치과 치료도 포함되나요? A2. 네, 건강보험 적용 치과 치료의 본인부담금은 지원 대상입니다. 단, 임플란트·교정 등 비급여 항목은 제외됩니다.
Q3. 복지 포인트로 가족이 대신 사용할 수 있나요? A3. 양도 불가이나, 가족 관련 지출(가족 여행, 가족 건강식품 등)에 본인 계정으로 결제하는 것은 가능합니다.
Q4. 자기개발비와 복지 포인트를 동일 항목에 중복 사용할 수 있나요? A4. 동일 건에 대해 이중 청구는 불가합니다. 하나의 제도만 선택하여 청구해야 합니다.
Q5. 수습 기간에도 복지 혜택을 받을 수 있나요? A5. 건강검진, 단체보험, 식대는 수습 기간에도 적용됩니다. 복지 포인트, 학자금은 수습 완료 후 적용됩니다.
Q6. 퇴직연금을 DB에서 DC로 변경하려면? A6. 입사 1년 후 HR시스템에서 전환 신청서를 제출하면 되며, 연 1회(매년 3월) 전환 접수합니다.
Q7. EAP 상담을 받으면 회사에 알려지나요? A7. 절대 아닙니다. 상담 기관이 직접 운영하며, 회사는 이용 여부조차 확인하지 않습니다.
Q8. 경조금 신청 시 증빙을 분실하면? A8. 가족관계증명서, 혼인증명서 등 공적 서류로 대체 가능합니다.
Q9. 동호회를 새로 만들려면 몇 명이 필요한가요? A9. 최소 5명의 회원이 필요하며, 총무부에 등록 신청서와 회칙을 제출합니다.
Q10. 사내 어린이집 대기가 길면 어떻게 하나요? A10. 대기 기간 중 월 20만원의 보육비를 지원받을 수 있습니다.
Q11. 장기근속 포상금에 세금이 붙나요? A11. 네, 기타소득으로 22% 원천징수됩니다.
Q12. 체력단련비와 자기개발비를 합산할 수 있나요? A12. 별도 관리되는 항목이므로 합산 불가합니다. 각 한도 내에서 별도로 사용합니다.
Q13. 재택근무 장비를 개인적으로 사용해도 되나요? A13. 회사 자산이므로 업무 외 사용은 금지됩니다.
Q14. 직원 할인으로 구매한 제품을 리셀할 수 있나요? A14. 엄격히 금지됩니다. 적발 시 할인 자격 박탈 및 징계 처분됩니다.
Q15. 복지 포인트가 12월에 소멸되면 환불받을 수 있나요? A15. 미사용 포인트의 현금 전환이나 환불은 불가합니다. 연내 소진을 권장합니다.',
    '{"tags":["복지","FAQ","자주묻는질문","건강검진","복지포인트","퇴직연금","EAP"],"category":"복지전체","doc_category":"FAQ","importance":"high"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- original_content = content 동기화 (INSERT 후 실행)
UPDATE tb_docs SET original_content = content
WHERE source_type = 'sql_import' AND usage_type = 'rag_knowledge' AND original_content IS NULL;
