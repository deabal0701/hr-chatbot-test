-- ============================================================
-- RAG 문서 데이터 - Part 01: 연차/휴가/근태 정책
-- 총 문서 수: 20개 (논리적 문서), 멀티청크 포함 총 28행
-- 생성일: 2026-02-27
-- 용도: RAG 검색 테스트 (RAGAS 평가용)
-- ============================================================

-- [문서 1] 연차휴가 발생 기준 (멀티청크 3개)
DO $$
DECLARE parent_id BIGINT;
BEGIN
    INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
    VALUES (
        1,
        '연차휴가 발생 기준',
        'policy',
        'ko',
        '제1조(목적) 본 규정은 근로기준법 제60조에 의거하여 당사 임직원의 연차유급휴가 발생 기준 및 부여 방법을 정함을 목적으로 한다. 제2조(적용 범위) 본 규정은 정규직 및 계약직(1년 이상 근로계약) 직원에게 적용되며, 일용직·파견근로자·인턴은 별도 기준을 따른다. 제3조(1년 미만 근로자) 입사일로부터 1개월 개근 시 1일의 유급휴가가 발생하며, 최대 11일까지 부여된다. 1개월간 소정근로일의 80% 미만 출근 시 해당 월의 연차는 발생하지 않는다. 중도 결근이 3일 이상인 월은 개근으로 인정하지 않되, 업무상 재해로 인한 결근은 출근한 것으로 본다.',
        '{"tags":["연차","발생기준","근로기준법","1년미만","개근"],"category":"연차관리","doc_category":"인사규정","importance":"critical"}',
        NULL, 'text-embedding-3-small', false, 0, 3, NULL, 'sql_import', 'rag_knowledge',
        NULL
    ) RETURNING id INTO parent_id;

    INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
    VALUES (
        1,
        '연차휴가 발생 기준',
        'policy',
        'ko',
        '제4조(1년 이상 근로자) (1) 1년간 80% 이상 출근한 근로자에게 15일의 유급휴가를 부여한다. (2) 3년 이상 계속 근로한 경우 최초 1년을 초과하는 매 2년마다 1일을 가산하여 부여하며, 가산휴가를 포함한 총 휴가일수는 25일을 한도로 한다. (3) 연차 발생 기준일은 입사일 기준(anniversary)으로 하되, 회계연도 기준(1월 1일)으로 전환할 경우 전환 시점에 비례 계산하여 부여한다. 제5조(출근율 계산) (1) 출근율 = 출근일수 ÷ 소정근로일수 × 100. (2) 출근한 것으로 보는 기간: 업무상 부상·질병 휴업, 출산전후휴가, 육아휴직, 남녀고용평등법에 의한 육아기 근로시간 단축. (3) 출근하지 않은 것으로 보는 기간: 개인 사유의 무급휴직, 정직 기간.',
        '{"tags":["연차","1년이상","가산휴가","출근율","계산방법"],"category":"연차관리","doc_category":"인사규정","importance":"critical"}',
        NULL, 'text-embedding-3-small', false, 1, 3, parent_id, 'sql_import', 'rag_knowledge', NULL
    );

    INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
    VALUES (
        1,
        '연차휴가 발생 기준',
        'policy',
        'ko',
        '제6조(입사일 기준과 회계연도 기준 전환) (1) 회사는 입사일 기준에서 회계연도(1월 1일~12월 31일) 기준으로 전환할 수 있으며, 전환 시 근로자에게 불리하지 않도록 비례 산정한다. (2) 전환 첫해에는 입사일 기준으로 발생한 잔여 연차와 회계연도 기준 비례 연차를 합산하여 부여한다. 제7조(80% 미만 출근자) 1년간 소정근로일의 80% 미만 출근한 근로자에게는 1개월 개근 시 1일씩 부여하되, 이미 제3조에 의해 사용한 휴가일수를 차감한다. 제8조(비정규직 특칙) 기간제 근로자의 경우 계약 기간에 비례하여 연차를 부여하며, 계약 갱신 시 이전 계약 기간의 근속을 합산한다. 단, 계약 종료일 이후 30일 이상 공백 기간이 있는 경우 근속을 새로 기산한다.',
        '{"tags":["연차","회계연도전환","비정규직","기간제","비례산정"],"category":"연차관리","doc_category":"인사규정","importance":"critical"}',
        NULL, 'text-embedding-3-small', false, 2, 3, parent_id, 'sql_import', 'rag_knowledge', NULL
    );
END $$;

-- [문서 2] 연차휴가 사용 방법 및 신청 절차
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '연차휴가 사용 방법 및 신청 절차',
    'manual',
    'ko',
    '제1조(신청 방법) (1) 연차휴가를 사용하고자 하는 직원은 휴가 시작일 3영업일 전까지 HR시스템(인사포털)에서 전자결재를 통해 신청하여야 한다. (2) 연속 5일 이상 사용 시에는 7영업일 전까지 신청하고, 소속 팀장의 사전 구두 동의를 받아야 한다. (3) 긴급한 사유(본인 질병, 가족 위급, 천재지변 등)로 사전 신청이 불가한 경우 당일 오전 9시 이전에 소속 팀장에게 유선 또는 메신저로 통보 후 사후 3일 이내에 전자결재를 완료한다. 제2조(결재 라인) (1) 사원~대리: 팀장 승인. (2) 과장~차장: 팀장 → 부서장 승인. (3) 부장 이상: 부서장 → 본부장 승인. (4) 임원: 대표이사 승인. 제3조(사용 제한) 프로젝트 마감, 감사 기간, 결산 기간 등 업무상 불가피한 사유가 있는 경우 팀장은 직원과 협의하여 휴가 시기를 변경할 수 있으나, 연 2회 이상 시기 변경을 반복할 수 없다.',
    '{"tags":["연차","신청절차","전자결재","결재라인","사용제한","긴급휴가"],"category":"연차관리","doc_category":"인사규정","importance":"high"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- [문서 3] 연차휴가 소멸 시효 및 이월 정책
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '연차휴가 소멸 시효 및 이월 정책',
    'policy',
    'ko',
    '제1조(소멸 시효) (1) 연차유급휴가는 발생일로부터 1년 이내에 사용하지 않으면 소멸된다(근로기준법 제60조 제7항). (2) 회계연도 기준 적용 시, 해당 연도 12월 31일까지 미사용 연차는 다음 해 1월 1일 자로 소멸된다. 제2조(이월 정책) (1) 원칙적으로 연차휴가는 이월되지 않는다. (2) 다만 다음 각 호에 해당하는 경우 최대 5일까지 익년도 3월 31일까지 사용할 수 있도록 이월을 허용한다: ① 회사 귀책 사유로 휴가를 사용하지 못한 경우(프로젝트 긴급 투입 등), ② 업무상 재해로 인한 장기 요양 복귀 후 잔여 연차가 있는 경우, ③ 출산전후휴가 또는 육아휴직 복귀 후 잔여 연차가 있는 경우. (3) 이월 신청은 소멸 시효 만료 14일 전까지 HR시스템에서 「연차 이월 신청서」를 제출하여야 하며, 인사팀 검토 후 승인 여부를 통보한다. 제3조(소멸 예외) 연차사용촉진 제도를 회사가 이행하지 않은 경우 미사용 연차는 소멸되지 않으며, 연차미사용수당으로 지급하여야 한다.',
    '{"tags":["연차","소멸시효","이월","미사용","연차수당","촉진제도"],"category":"연차관리","doc_category":"인사규정","importance":"high"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- [문서 4] 연차수당 지급 기준
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '연차수당 지급 기준',
    'policy',
    'ko',
    '제1조(연차미사용수당) (1) 연차사용촉진(근로기준법 제61조) 절차를 이행하였음에도 근로자가 사용하지 않은 연차에 대해서는 수당을 지급하지 아니한다. (2) 회사가 촉진 절차를 이행하지 아니한 경우, 미사용 연차일수 × 1일 통상임금을 산정하여 다음 연차 발생월의 급여일에 지급한다. (3) 1일 통상임금 산정: 월 통상임금 ÷ 해당 월 소정근로일수. 제2조(퇴직 시 정산) (1) 퇴직일 기준 미사용 잔여 연차는 퇴직금과 별도로 정산하여 최종 급여 시 일괄 지급한다. (2) 중도 퇴사 시 연차일수는 해당 연도 재직일수에 비례하여 산정하며, 이미 사용한 일수가 비례 발생분을 초과한 경우 초과분은 공제한다. 제3조(선사용 초과분 공제) 입사 초기 선사용한 연차가 비례 발생분을 초과하여 퇴직하는 경우, 초과 사용일수 × 1일 통상임금을 최종 급여에서 공제한다. 단, 공제 금액이 최종 급여를 초과하는 경우 별도 반납 약정서를 체결한다.',
    '{"tags":["연차수당","미사용","퇴직정산","통상임금","선사용","공제"],"category":"연차관리","doc_category":"인사규정","importance":"high"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- [문서 5] 병가 규정 (멀티청크 2개)
DO $$
DECLARE parent_id BIGINT;
BEGIN
    INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
    VALUES (
        1,
        '병가 규정',
        'policy',
        'ko',
        '제1조(유급 병가) (1) 직원이 질병 또는 부상으로 근무가 불가한 경우, 연간 6일의 유급 병가를 사용할 수 있다. (2) 3일 이하의 병가는 소속 팀장에게 사전 또는 당일 구두 통보 후 사후 전자결재로 처리한다. (3) 4일 이상 연속 병가 시 의료기관의 진단서를 제출하여야 하며, 진단서에는 질병명, 치료 기간, 취업 가능 여부가 명시되어야 한다. (4) 유급 병가 기간 중 통상임금의 100%를 지급한다. 제2조(무급 병가) (1) 유급 병가를 모두 소진한 후에도 추가 치료가 필요한 경우 최대 30일의 무급 병가를 신청할 수 있다. (2) 무급 병가 신청 시 주치의 진단서와 함께 「장기 병가 신청서」를 인사팀에 제출한다. (3) 무급 병가 기간 중에는 급여가 지급되지 않으며, 4대보험 본인 부담분은 계속 공제된다.',
        '{"tags":["병가","유급병가","무급병가","진단서","장기병가"],"category":"휴가관리","doc_category":"인사규정","importance":"high"}',
        NULL, 'text-embedding-3-small', false, 0, 2, NULL, 'sql_import', 'rag_knowledge',
        NULL
    ) RETURNING id INTO parent_id;

    INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
    VALUES (
        1,
        '병가 규정',
        'policy',
        'ko',
        '제3조(장기 병가) (1) 30일을 초과하는 장기 치료가 필요한 경우 휴직으로 전환할 수 있으며, 휴직 기간은 최대 1년으로 한다. (2) 장기 병가에서 휴직으로 전환 시 인사위원회 심의를 거쳐야 한다. 제4조(업무상 재해) (1) 업무상 부상 또는 질병으로 인한 병가는 산업재해보상보험법에 따라 별도 처리하며, 유급/무급 병가 일수에 산입하지 않는다. (2) 요양 기간 중 평균임금의 70%를 산재보험에서 지급받으며, 회사는 나머지 30%를 보전한다. 제5조(감염병) (1) 법정 감염병(코로나19, 결핵, 홍역 등)으로 인한 격리 조치 시 해당 기간은 유급으로 처리하며, 병가 일수에 산입하지 않는다. (2) 격리 해제 시 의사 소견서를 제출하여야 복귀할 수 있다. 제6조(복귀 절차) 7일 이상 병가 사용 후 복귀 시 「업무 복귀 적합 판정서」를 제출하여야 하며, 필요 시 산업보건의와 복귀 면담을 실시한다.',
        '{"tags":["장기병가","휴직전환","산업재해","감염병","복귀절차"],"category":"휴가관리","doc_category":"인사규정","importance":"high"}',
        NULL, 'text-embedding-3-small', false, 1, 2, parent_id, 'sql_import', 'rag_knowledge', NULL
    );
END $$;

-- [문서 6] 경조사 휴가 규정
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '경조사 휴가 규정',
    'policy',
    'ko',
    '제1조(경조휴가 일수) 다음 각 호의 경조사 발생 시 유급 경조휴가를 부여한다. (1) 본인 결혼: 5일 (2) 자녀 결혼: 1일 (3) 배우자 출산: 10일(출산일로부터 90일 이내 사용) (4) 부모(배우자 부모 포함) 사망: 5일 (5) 조부모·외조부모 사망: 3일 (6) 형제·자매 사망: 3일 (7) 배우자 사망: 5일 (8) 자녀 사망: 5일 (9) 배우자 형제·자매 사망: 1일 (10) 본인 회갑(환갑): 1일 (11) 부모 회갑: 1일. 제2조(경조금 지급) 경조사 종류별 지원금: 본인 결혼 50만원, 자녀 결혼 30만원, 부모 사망 50만원, 배우자·자녀 사망 50만원, 조부모·형제자매 사망 20만원, 출산 20만원. 화환/조화는 별도 지원(회사 명의 발송). 제3조(증빙) 경조휴가 사용 후 7일 이내에 청첩장, 가족관계증명서, 사망진단서 등 증빙 서류를 인사팀에 제출하여야 하며, 미제출 시 결근 처리될 수 있다. 제4조(휴일 포함) 경조휴가 기간에 공휴일·주말이 포함되어도 일수에 산입한다.',
    '{"tags":["경조사","경조휴가","경조금","결혼","출산","사망","화환"],"category":"휴가관리","doc_category":"인사규정","importance":"high"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- [문서 7] 출산휴가 및 육아휴직 정책 (멀티청크 3개)
DO $$
DECLARE parent_id BIGINT;
BEGIN
    INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
    VALUES (
        1,
        '출산휴가 및 육아휴직 정책',
        'policy',
        'ko',
        '제1조(출산전후휴가) (1) 임신 중인 여성 직원에게 출산 전후 90일의 유급 출산전후휴가를 부여한다(다태아의 경우 120일). (2) 휴가 기간 배분: 출산 후 45일 이상 확보되어야 하며(다태아 60일), 나머지는 출산 전 사용 가능하다. (3) 급여: 최초 60일(다태아 75일)은 회사가 통상임금 전액을 지급하고, 나머지 30일(다태아 45일)은 고용보험에서 출산전후휴가급여를 지급한다. (4) 우선지원대상기업의 경우 90일(120일) 전체를 고용보험에서 지급받되, 통상임금과의 차액은 회사가 보전한다. 제2조(유산·사산 휴가) 임신 기간에 따라 유산·사산 시 다음 휴가를 부여한다: 11주 이내 5일, 12~15주 10일, 16~21주 30일, 22~27주 60일, 28주 이상 90일.',
        '{"tags":["출산휴가","출산전후휴가","다태아","유산사산","고용보험"],"category":"모성보호","doc_category":"인사규정","importance":"critical"}',
        NULL, 'text-embedding-3-small', false, 0, 3, NULL, 'sql_import', 'rag_knowledge',
        NULL
    ) RETURNING id INTO parent_id;

    INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
    VALUES (
        1,
        '출산휴가 및 육아휴직 정책',
        'policy',
        'ko',
        '제3조(배우자 출산휴가) (1) 배우자가 출산한 남성 직원에게 10일의 유급 배우자 출산휴가를 부여한다. (2) 출산일로부터 90일 이내에 사용하여야 하며, 1회에 한해 분할 사용이 가능하다(최초 사용일이 출산일 포함 90일 이내여야 함). (3) 급여는 최초 5일 회사 부담, 나머지 5일 고용보험 부담으로 한다. 제4조(육아휴직) (1) 만 8세 이하 또는 초등학교 2학년 이하의 자녀를 양육하기 위해 남녀 구분 없이 최대 1년의 육아휴직을 신청할 수 있다. (2) 같은 자녀에 대해 부모가 각각 1년씩 사용할 수 있으며(부부 합산 최대 2년), 동시 사용도 가능하다. (3) 육아휴직 신청은 시작일 30일 전까지 「육아휴직 신청서」를 인사팀에 제출하여야 한다. (4) 긴급한 경우(배우자 사망, 질병 등) 7일 전 신청 가능.',
        '{"tags":["배우자출산휴가","육아휴직","남성육아","신청절차","기간"],"category":"모성보호","doc_category":"인사규정","importance":"critical"}',
        NULL, 'text-embedding-3-small', false, 1, 3, parent_id, 'sql_import', 'rag_knowledge', NULL
    );

    INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
    VALUES (
        1,
        '출산휴가 및 육아휴직 정책',
        'policy',
        'ko',
        '제5조(육아휴직 급여) (1) 고용보험에서 육아휴직급여를 지급하며, 첫 3개월은 통상임금의 80%(상한 150만원), 4개월 이후는 통상임금의 50%(상한 120만원)를 지급한다. (2) 6+6 부모육아휴직제: 같은 자녀에 대해 부모 모두 육아휴직 시, 두 번째 사용자의 첫 6개월간 통상임금의 100%(상한 월 450만원)를 지급받을 수 있다. (3) 회사는 고용보험 급여 외 추가 지원금을 지급하지 않으나, 4대보험 사업주 부담분은 계속 납부한다. 제6조(복직 보장) (1) 육아휴직 종료 후 반드시 휴직 전 동일 업무 또는 동등 수준의 업무에 복귀시켜야 한다. (2) 복직 후 30일 이내에 불이익한 인사조치(전직, 감급 등)를 해서는 안 된다. (3) 육아휴직 기간은 근속 기간에 포함하며, 연차 발생을 위한 출근율 산정 시 출근한 것으로 본다.',
        '{"tags":["육아휴직급여","6+6","복직보장","근속기간","출근율"],"category":"모성보호","doc_category":"인사규정","importance":"critical"}',
        NULL, 'text-embedding-3-small', false, 2, 3, parent_id, 'sql_import', 'rag_knowledge', NULL
    );
END $$;

-- [문서 8] 반차 사용 규정
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '반차 사용 규정',
    'policy',
    'ko',
    '제1조(반차의 정의) (1) 반차란 1일 연차를 0.5일 단위로 분할하여 사용하는 것을 말한다. (2) 오전 반차: 09:00~13:00 근무 면제, 13:00 출근. (3) 오후 반차: 13:00 이후 근무 면제(09:00~13:00 근무 후 퇴근). (4) 반차 사용 시 0.5일의 연차가 차감된다. 제2조(신청 방법) (1) 반차는 사용일 전일 18:00까지 HR시스템에서 신청한다. (2) 긴급 사유로 당일 신청이 필요한 경우 팀장 구두 승인 후 당일 내 전자결재를 완료한다. (3) 반차와 초과근무는 동일 일자에 중복 인정되지 않는다(예: 오전 반차 사용 후 18:00까지 근무하여도 오후 초과근무로 인정하지 않음). 제3조(제한) (1) 동일 일자에 오전+오후 반차를 연속 사용할 수 없으며, 이 경우 1일 연차로 신청하여야 한다. (2) 월 반차 사용은 6회(3일분)를 한도로 하며, 이를 초과하는 경우 팀장 승인이 필요하다.',
    '{"tags":["반차","오전반차","오후반차","0.5일","사용제한","초과근무"],"category":"연차관리","doc_category":"인사규정","importance":"medium"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- [문서 9] 특별휴가 종류 및 신청 방법
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '특별휴가 종류 및 신청 방법',
    'policy',
    'ko',
    '제1조(리프레시 휴가) (1) 5년 이상 근속 직원에게 만 5년 도래 시 3일, 만 10년 5일, 만 15년 7일, 만 20년 10일의 유급 리프레시 휴가를 부여한다. (2) 리프레시 휴가는 발생일로부터 1년 이내에 사용하여야 하며, 연차와 연결 사용을 권장한다. 제2조(포상 휴가) (1) 우수 사원, 프로젝트 성공 기여, 사회공헌 활동 유공 등으로 선정된 직원에게 1~5일의 포상 휴가를 부여할 수 있다. (2) 포상 휴가는 인사위원회 또는 대표이사 결재로 부여하며, 부여일로부터 6개월 이내에 사용한다. 제3조(창립기념일 휴가) 매년 3월 15일 창립기념일에 전 직원에게 1일의 유급 휴가를 부여한다. 단, 필수 운영 부서(보안, 전산, CS)는 교대 적용한다. 제4조(하계 특별휴가) 7월~9월 중 3일의 하계 특별 유급휴가를 부여하며, 연차와 별도로 관리한다. 사용 시기는 팀별 조율 후 확정한다.',
    '{"tags":["특별휴가","리프레시","포상휴가","창립기념일","하계휴가","장기근속"],"category":"휴가관리","doc_category":"인사규정","importance":"medium"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- [문서 10] 대체휴무 사용 규정
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '대체휴무 사용 규정',
    'policy',
    'ko',
    '제1조(대체휴무 발생) (1) 공휴일, 주말(토·일요일), 근로자의 날에 업무 지시에 의해 근무한 경우 동일 시간만큼의 대체휴무가 발생한다. (2) 4시간 이상 8시간 미만 근무 시 반일(0.5일) 대체휴무, 8시간 이상 근무 시 1일 대체휴무로 산정한다. (3) 대체휴무는 HR시스템에 자동 등록되며, 근무 확인은 팀장이 승인한다. 제2조(사용 기한) (1) 대체휴무는 발생일로부터 3개월 이내에 사용하여야 한다. (2) 3개월 이내에 미사용 시 자동 소멸되며, 초과근무수당으로 전환되지 않는다. 단, 회사 귀책으로 사용 기회를 부여하지 않은 경우 수당으로 전환 지급한다. 제3조(사용 우선순위) 연차와 대체휴무가 모두 잔여한 경우 대체휴무를 우선 사용하도록 권장한다. 제4조(해외 출장 중 휴일 근무) 해외 출장 중 현지 휴일에 근무한 경우에도 대체휴무가 발생하며, 출장 복귀 후 1개월 이내 추가로 사용 기한을 부여한다.',
    '{"tags":["대체휴무","주말근무","공휴일","사용기한","초과근무수당","해외출장"],"category":"휴가관리","doc_category":"인사규정","importance":"medium"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- [문서 11] 공가 규정
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '공가 규정',
    'policy',
    'ko',
    '제1조(공가의 정의) 공가란 법령에 의한 공적 의무 수행 또는 회사가 인정하는 공적 사유로 인해 근무하지 못하는 경우 부여하는 유급 휴가를 말한다. 제2조(공가 사유) (1) 예비군 훈련(동원·비동원 포함) (2) 민방위 훈련 (3) 공직선거법에 의한 투표 참여 (4) 법원 증인 출석·배심원 참여 (5) 천재지변·재난 시 긴급 소개(疏開) (6) 병역법에 의한 신체검사 (7) 건강검진(국가 건강검진 대상자). 제3조(기간 및 급여) (1) 공가 기간은 해당 공적 의무 수행에 필요한 최소 일수로 하며, 통상임금 전액을 지급한다. (2) 예비군 훈련의 경우 훈련 통지서에 명시된 기간 + 왕복 이동일(원거리 훈련장 기준)을 공가 기간으로 인정한다. (3) 투표의 경우 선거일 당일 또는 사전투표일 중 1일을 공가로 부여하되, 근무 시간 중 2시간 이상 투표 시간을 보장한다. 제4조(증빙 제출) 공가 사용 후 3일 이내에 훈련 확인서, 출석 확인서, 투표 확인서 등 증빙을 인사팀에 제출한다.',
    '{"tags":["공가","예비군","민방위","투표","증인","공적의무","유급"],"category":"휴가관리","doc_category":"인사규정","importance":"medium"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- [문서 12] 연차 선사용 및 마이너스 연차 정책
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '연차 선사용 및 마이너스 연차 정책',
    'policy',
    'ko',
    '제1조(선사용 허용 조건) (1) 입사일 기준 6개월 미만의 신입 직원에게 최대 3일의 연차 선사용을 허용한다. (2) 선사용 신청 시 팀장 및 인사팀장의 이중 승인이 필요하며, 「연차 선사용 확인서」에 서명하여야 한다. (3) 선사용 확인서에는 퇴직 시 정산 동의 조항이 포함된다. 제2조(마이너스 연차) (1) 회계연도 기준 적용 시, 연초에 부여된 연차를 모두 사용하고 연도 중 퇴직하는 경우 비례 발생분 초과 사용한 연차가 마이너스로 산정된다. (2) 마이너스 연차 = 사용일수 - (15일 × 재직월수 ÷ 12, 소수점 이하 절사). (3) 마이너스 연차 발생 시 퇴직일 기준 1일 통상임금 × 마이너스 일수를 최종 급여에서 공제한다. 제3조(공제 한도) (1) 최종 급여 대비 공제 가능 금액은 급여의 50%를 한도로 하며, 초과분은 별도 반납 약정을 체결한다. (2) 업무상 재해, 경영상 해고 등 비자발적 퇴직의 경우 마이너스 연차 정산을 면제할 수 있다.',
    '{"tags":["선사용","마이너스연차","비례계산","퇴직정산","공제한도","신입직원"],"category":"연차관리","doc_category":"인사규정","importance":"high"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- [문서 13] 태아검진휴가 및 임신 중 근로시간 단축 규정
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '태아검진휴가 및 임신 중 근로시간 단축 규정',
    'policy',
    'ko',
    '제1조(태아검진 시간 허용) (1) 임신 중인 여성 직원은 임신 기간에 따라 다음과 같이 태아검진을 위한 유급 시간을 보장받는다: 임신 28주까지 4주마다 1회, 임신 29~36주 2주마다 1회, 임신 37주 이후 1주마다 1회. (2) 태아검진 시간은 정기 검진에 필요한 시간(이동 시간 포함)으로 하며, 연차에서 차감하지 않는다. (3) 검진 후 진료 확인서(영수증)를 HR시스템에 업로드한다. 제2조(임신기 근로시간 단축) (1) 임신 후 12주 이내 또는 36주 이후의 여성 직원은 1일 2시간의 근로시간 단축을 신청할 수 있다. (2) 단축된 시간에 대하여 임금을 삭감하지 아니한다. (3) 단축 근무 형태: 09:00~16:00(1시간 단축) 또는 10:00~17:00(1시간 단축), 합산 2시간 단축도 가능(10:00~16:00). (4) 사용자는 임신 중 근로시간 단축 신청을 거부할 수 없으며, 이를 이유로 불이익한 처우를 해서는 안 된다. 제3조(야간·휴일근무 제한) 임신 중인 직원에게 야간근무(22:00~06:00) 및 휴일근무를 시키지 아니한다.',
    '{"tags":["태아검진","임신","근로시간단축","모성보호","야간근무제한"],"category":"모성보호","doc_category":"인사규정","importance":"critical"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- [문서 14] 가족돌봄휴가 및 가족돌봄휴직 규정
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '가족돌봄휴가 및 가족돌봄휴직 규정',
    'policy',
    'ko',
    '제1조(가족돌봄휴가) (1) 직원은 가족(조부모, 부모, 배우자, 배우자의 부모, 자녀, 손자녀)의 질병, 사고, 노령으로 인한 돌봄이 필요한 경우 연간 10일의 가족돌봄휴가를 신청할 수 있다. (2) 가족돌봄휴가는 1일 단위로 사용하며, 긴급 시 사후 신청이 가능하다. (3) 가족돌봄휴가 중 최초 5일은 유급으로, 나머지 5일은 무급으로 처리한다(회사 복지 기준). (4) 감염병 관련 자녀 돌봄의 경우 연간 10일 외 추가 10일을 사용할 수 있다. 제2조(가족돌봄휴직) (1) 가족의 장기 질병, 사고, 장애, 노령 등으로 장기간 돌봄이 필요한 경우 최대 90일의 가족돌봄휴직을 신청할 수 있다. (2) 1회 사용 시 최소 30일 이상이어야 하며, 분할 사용 가능(최대 3회). (3) 가족돌봄휴직 기간 중 급여는 지급되지 않으며, 4대보험은 본인이 부담한다. (4) 사업주는 정당한 사유 없이 휴직을 거부할 수 없으며, 휴직을 이유로 불이익 처우를 해서는 안 된다.',
    '{"tags":["가족돌봄","돌봄휴가","돌봄휴직","감염병","자녀돌봄","유급무급"],"category":"휴가관리","doc_category":"인사규정","importance":"high"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- [문서 15] 연차 사용 촉진 제도
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '연차 사용 촉진 제도',
    'policy',
    'ko',
    '제1조(촉진 절차) 근로기준법 제61조에 따라 회사는 다음의 연차사용촉진 절차를 이행한다. (1) 1차 촉진(연차 발생일로부터 10개월 경과 시점): 미사용 연차일수를 서면(이메일 또는 전자문서)으로 근로자에게 통보하고, 10일 이내에 사용 시기를 지정하여 회신하도록 촉구한다. (2) 2차 촉진(1차 촉구 후 10일 이내 미회신 시): 회사가 미사용 연차의 사용 시기를 지정하여 서면 통보한다. (3) 근로자가 회사 지정 시기에도 사용하지 않은 경우, 해당 미사용 연차에 대한 수당 지급 의무가 면제된다. 제2조(회계연도 기준 촉진 일정) (1) 1차 촉진: 매년 7월 1일~10일 사이에 실시. (2) 2차 촉진: 미회신자에 대해 7월 20일까지 사용 시기 지정 통보. (3) 촉진 대상: 잔여 연차가 5일 이상인 직원. 제3조(촉진 미이행 효과) 회사가 촉진 절차를 이행하지 않은 경우, 근로자의 미사용 연차는 소멸되지 않으며, 연차미사용수당으로 전액 보상하여야 한다. 제4조(기록 보관) 촉진 통보 및 회신 기록은 3년간 보관한다.',
    '{"tags":["연차촉진","사용촉진","근로기준법61조","미사용수당","서면통보","기록보관"],"category":"연차관리","doc_category":"인사규정","importance":"high"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- [문서 16] 시간단위 연차 사용 정책
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '시간단위 연차 사용 정책',
    'policy',
    'ko',
    '제1조(시간 연차 도입 목적) 직원의 유연한 휴가 사용을 지원하기 위해 연차를 시간 단위로 분할하여 사용할 수 있는 제도를 운영한다. 제2조(사용 기준) (1) 시간 단위 연차의 최소 사용 단위는 1시간이며, 1시간 단위로 추가 사용 가능하다. (2) 1일 소정근로시간(8시간) = 연차 1일로 환산한다. (3) 시간 연차 연간 사용 한도: 총 연차일수 중 최대 5일분(40시간)까지 시간 단위로 사용 가능하다. 제3조(신청 방법) (1) HR시스템에서 「시간 연차 신청」 메뉴를 통해 사용 일시, 사용 시간을 입력한다. (2) 사용일 전일 18:00까지 신청을 원칙으로 하되, 당일 신청도 팀장 승인 하에 가능하다. (3) 시간 연차는 근무 시작 전 또는 근무 종료 전에 사용하는 것을 원칙으로 하며, 근무 중간에 사용하는 경우 팀장과 사전 합의가 필요하다. 제4조(적용 제외) (1) 교대 근무자, 현장 근무자는 시간 연차 적용에서 제외될 수 있다. (2) 시간 연차와 반차는 동일 일자에 중복 사용할 수 없다.',
    '{"tags":["시간연차","시간단위","유연근무","1시간","사용한도","적용제외"],"category":"연차관리","doc_category":"인사규정","importance":"medium"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- [문서 17] 연차 집중 사용 기간 지정
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '연차 집중 사용 기간 지정',
    'guide',
    'ko',
    '제1조(목적) 직원의 충분한 휴식 보장과 연차 소진율 향상을 위해 연차 집중 사용 권장 기간을 지정하여 운영한다. 제2조(하계 연차 집중 기간) (1) 매년 7월 15일~8월 31일을 하계 연차 집중 기간으로 지정한다. (2) 해당 기간 중 최소 3일 이상의 연차를 사용하도록 권장하며, 하계 특별휴가(3일)와 연계 사용을 장려한다. (3) 팀별 최소 인원 유지를 위해 팀 내 50% 이상이 동시 부재하지 않도록 팀장이 조율한다. 제3조(동계 연차 집중 기간) (1) 매년 12월 24일~다음해 1월 3일을 동계 연차 집중 기간으로 지정한다. (2) 해당 기간 중 공휴일·주말과 연계하여 연차를 사용하도록 권장한다. 제4조(부서별 조율) (1) 팀장은 연차 집중 기간 시작 1개월 전까지 팀원의 사용 일정을 취합하여 인사팀에 보고한다. (2) 필수 운영 인력이 필요한 부서는 교대 스케줄을 수립하여 인사팀 승인을 받는다. 제5조(미사용 독려) 집중 기간에 연차를 사용하지 않은 직원에게는 개별 면담을 실시하여 사용을 독려한다.',
    '{"tags":["연차집중","하계휴가","동계휴가","사용권장","팀조율","교대스케줄"],"category":"연차관리","doc_category":"인사가이드","importance":"medium"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- [문서 18] 무급휴가 및 휴직 신청 규정 (멀티청크 2개)
DO $$
DECLARE parent_id BIGINT;
BEGIN
    INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
    VALUES (
        1,
        '무급휴가 및 휴직 신청 규정',
        'policy',
        'ko',
        '제1조(무급휴가) (1) 연차 및 기타 유급휴가를 모두 소진한 직원이 개인 사유로 추가 휴가가 필요한 경우 무급휴가를 신청할 수 있다. (2) 무급휴가 신청은 사용일 7일 전까지 「무급휴가 신청서」를 팀장 → 인사팀장 결재를 거쳐 제출한다. (3) 1회 무급휴가는 최대 30일까지 신청 가능하며, 연간 총 60일을 초과할 수 없다. (4) 무급휴가 기간 중 급여는 지급되지 않으며, 4대보험 본인 부담분은 계속 공제된다. 제2조(휴직 종류) (1) 질병 휴직: 업무 외 질병·부상으로 3개월 이상 치료가 필요한 경우(최대 1년) (2) 육아 휴직: 만 8세 이하 자녀 양육(최대 1년) (3) 가족돌봄 휴직: 가족 질병·사고·노령 돌봄(최대 90일) (4) 학업 휴직: 석·박사 과정(최대 2년, 사전 심의 필요) (5) 병역 휴직: 군 복무(의무 복무 기간) (6) 기타 휴직: 인사위원회 승인에 의한 특별 사유(최대 6개월)',
        '{"tags":["무급휴가","휴직","질병휴직","학업휴직","병역휴직","신청절차"],"category":"휴가관리","doc_category":"인사규정","importance":"high"}',
        NULL, 'text-embedding-3-small', false, 0, 2, NULL, 'sql_import', 'rag_knowledge',
        NULL
    ) RETURNING id INTO parent_id;

    INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
    VALUES (
        1,
        '무급휴가 및 휴직 신청 규정',
        'policy',
        'ko',
        '제3조(휴직 신청 절차) (1) 휴직을 희망하는 직원은 휴직 시작일 30일 전까지 「휴직 신청서」와 사유 증빙 서류를 인사팀에 제출한다. (2) 질병 휴직: 진단서(치료 기간 3개월 이상 명시), 학업 휴직: 입학 허가서 또는 학적 증명서. (3) 인사팀은 심의 후 10영업일 이내에 승인/반려를 통보한다. 제4조(급여 및 복리후생) (1) 육아휴직을 제외한 무급 휴직 기간 중 급여는 지급되지 않는다. (2) 건강보험·국민연금은 휴직 기간 중 납입 유예 신청이 가능하다(질병·육아 한정). (3) 복지 포인트, 자기개발비 등 복리후생은 휴직 중 적용이 중지된다. 제5조(복직 절차) (1) 휴직 만료 14일 전까지 「복직 신청서」를 인사팀에 제출한다. (2) 질병 휴직의 경우 복직 전 「업무 복귀 적합 판정서」를 첨부한다. (3) 복직 시 원칙적으로 휴직 전 동일 직위·직급의 업무에 배치하되, 조직 개편 등 불가피한 사유가 있는 경우 동등 수준의 업무에 배치한다. (4) 복직 후 3개월 이내에 재휴직을 신청할 수 없다(질병 악화 등 긴급 사유 제외).',
        '{"tags":["휴직신청","복직절차","급여처리","4대보험","복리후생중지","배치"],"category":"휴가관리","doc_category":"인사규정","importance":"high"}',
        NULL, 'text-embedding-3-small', false, 1, 2, parent_id, 'sql_import', 'rag_knowledge', NULL
    );
END $$;

-- [문서 19] 연차휴가 FAQ
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '연차휴가 FAQ',
    'faq',
    'ko',
    'Q1. 입사 후 바로 연차를 사용할 수 있나요? A1. 입사 후 1개월 개근 시 1일이 발생하므로, 최초 1개월 경과 후 사용 가능합니다. 다만 선사용 제도(최대 3일)를 활용하면 입사 즉시 사용할 수 있습니다.
Q2. 연차를 시간 단위로 쪼개서 사용할 수 있나요? A2. 네, 시간 연차 제도가 도입되어 1시간 단위로 사용 가능하며, 연간 40시간(5일분)까지 시간 단위로 사용할 수 있습니다.
Q3. 연차를 다음 해로 이월할 수 있나요? A3. 원칙적으로 불가하나, 회사 귀책 사유(프로젝트 투입 등)인 경우 최대 5일까지 익년도 3월 31일까지 사용 가능한 이월을 신청할 수 있습니다.
Q4. 수습 기간 중에도 연차가 발생하나요? A4. 네, 수습 기간도 근로기간에 포함되므로 1개월 개근 시 1일씩 정상 발생합니다.
Q5. 연차 사용을 팀장이 거부할 수 있나요? A5. 사업 운영에 막대한 지장이 있는 경우에 한해 시기 변경을 요청할 수 있으나, 연 2회 이상 반복 변경은 불가합니다.
Q6. 경조휴가는 연차에서 차감되나요? A6. 아닙니다. 경조휴가는 별도 유급 특별휴가로 연차와 무관합니다.
Q7. 육아휴직 기간에 연차가 발생하나요? A7. 육아휴직 기간은 출근한 것으로 보므로, 복귀 후 정상적으로 연차가 발생합니다.
Q8. 아르바이트/파트타임도 연차가 있나요? A8. 주 15시간 이상 근로하는 단시간 근로자는 비례하여 연차가 발생합니다.
Q9. 잔여 연차를 확인하는 방법은? A9. HR시스템 > 마이페이지 > 연차 현황에서 실시간 확인 가능합니다.
Q10. 연차 소진 후 추가 휴가가 필요하면? A10. 무급휴가(연간 최대 60일)를 신청하거나, 대체휴무 잔여분을 활용할 수 있습니다.',
    '{"tags":["연차","FAQ","자주묻는질문","시간연차","이월","수습기간","경조휴가"],"category":"연차관리","doc_category":"FAQ","importance":"high"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- [문서 20] 근태 기록 및 이의 신청 절차
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '근태 기록 및 이의 신청 절차',
    'manual',
    'ko',
    '제1조(근태 기록 방법) (1) 출퇴근 기록은 사원증(RFID) 태깅, 모바일 앱 GPS 체크인, 또는 PC 기반 근태 시스템을 통해 등록한다. (2) 재택근무 시 VPN 접속 기록 + 모바일 앱 체크인으로 대체하며, 오전 9시 이전 체크인·오후 6시 이후 체크아웃을 기본으로 한다. (3) 외근·출장 시 사전 등록된 일정에 따라 자동 인정되며, 추가 증빙이 필요한 경우 팀장 확인을 받는다. 제2조(이의 신청) (1) 근태 기록에 오류가 있는 경우(미체크인, 시스템 오류 등) 발생일로부터 7영업일 이내에 HR시스템에서 「근태 정정 신청」을 제출한다. (2) 정정 신청 시 사유와 증빙(팀장 확인서, 사진 등)을 첨부한다. (3) 인사팀은 5영업일 이내에 승인 또는 반려를 통보한다. 제3조(지각·조퇴·결근 기준) (1) 지각: 09:10 이후 체크인(유예 10분). 월 3회 이상 지각 시 인사 경고. (2) 조퇴: 17:00 이전 퇴근(팀장 사전 승인 필요). (3) 결근: 무단 미출근(사전 통보 없이 근무하지 않은 날). 무단 결근 3일 누적 시 징계 대상. 제4조(기록 보관) 근태 데이터는 3년간 보관하며, 급여 분쟁 시 증거 자료로 활용한다.',
    '{"tags":["근태","출퇴근","이의신청","정정","지각","조퇴","결근","RFID","재택근무"],"category":"근태관리","doc_category":"인사규정","importance":"high"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- original_content = content 동기화 (INSERT 후 실행)
UPDATE tb_docs SET original_content = content
WHERE source_type = 'sql_import' AND usage_type = 'rag_knowledge' AND original_content IS NULL;
