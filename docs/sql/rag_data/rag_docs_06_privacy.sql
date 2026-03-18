-- ============================================================
-- RAG 문서 데이터 - Part 06: 개인정보보호/PIPA/정보주체 권리
-- 총 문서 수: 20개 (논리적 문서), 멀티청크 포함 총 28행
-- 생성일: 2026-02-27
-- 용도: RAG 검색 테스트 (RAGAS 평가용)
-- ============================================================

-- [문서 1] 개인정보보호 정책 총칙 (멀티청크 3개)
DO $$
DECLARE parent_id BIGINT;
BEGIN
    INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
    VALUES (
        1,
        '개인정보보호 정책 총칙',
        'regulation',
        'ko',
        '제1조(목적) 본 정책은 「개인정보 보호법」(이하 "법") 및 동법 시행령에 따라, 당사가 처리하는 모든 개인정보의 안전한 관리와 정보주체의 권리 보장을 목적으로 한다. 제2조(정의) (1) "개인정보"란 살아 있는 개인에 관한 정보로서 성명, 주민등록번호, 영상 등을 통하여 개인을 알아볼 수 있는 정보를 말한다. 해당 정보만으로는 특정 개인을 알아볼 수 없더라도 다른 정보와 쉽게 결합하여 알아볼 수 있는 정보를 포함한다. (2) "처리"란 개인정보의 수집, 생성, 연계, 연동, 기록, 저장, 보유, 가공, 편집, 검색, 출력, 정정, 복구, 이용, 제공, 공개, 파기 등을 말한다. (3) "정보주체"란 처리되는 정보에 의하여 알아볼 수 있는 사람으로서 그 정보의 주체가 되는 사람을 말한다. 제3조(적용 범위) (1) 당사가 업무 목적으로 처리하는 모든 개인정보에 적용된다. (2) 임직원, 계약직, 파견직, 인턴, 협력업체 직원이 접근하는 개인정보를 포함한다. (3) 종이 문서, 전자 문서, 데이터베이스, 영상 정보 등 매체를 불문한다.',
        '{"tags":["개인정보보호","총칙","PIPA","정보주체","개인정보정의","적용범위"],"category":"개인정보보호","doc_category":"개인정보보호","importance":"critical"}',
        NULL, 'text-embedding-3-small', false, 0, 3, NULL, 'sql_import', 'rag_knowledge',
        NULL
    ) RETURNING id INTO parent_id;

    INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
    VALUES (
        1,
        '개인정보보호 정책 총칙',
        'regulation',
        'ko',
        '제4조(개인정보보호 원칙) (1) 목적 제한의 원칙: 명확한 목적 범위 내에서만 개인정보를 처리하며, 그 목적에 필요한 범위에서 최소한의 개인정보만 수집한다. (2) 정확성의 원칙: 개인정보의 처리 목적에 필요한 범위에서 개인정보의 정확성, 완전성, 최신성이 보장되도록 한다. (3) 안전성 확보의 원칙: 개인정보의 분실, 도난, 유출, 위조, 변조, 훼손을 방지하기 위한 기술적·관리적·물리적 안전조치를 취한다. (4) 투명성의 원칙: 개인정보 처리방침을 공개하고, 정보주체의 열람 청구권 등 권리를 보장한다. (5) 사생활 침해 최소화: 익명처리가 가능한 경우 익명에 의하여 처리하고, 가명처리가 가능한 경우 가명에 의하여 처리할 수 있도록 한다. 제5조(책임) (1) 개인정보보호 책임자(CPO): 대표이사가 지명하며, 개인정보 처리 전반을 총괄한다. (2) 개인정보보호 실무자: 각 부서별 1인 이상 지정하여 부서 내 개인정보 처리 현황을 관리한다. (3) 전 임직원: 업무 과정에서 접하는 개인정보의 보호 책임을 진다.',
        '{"tags":["개인정보보호원칙","목적제한","정확성","안전성","투명성","CPO"],"category":"개인정보보호","doc_category":"개인정보보호","importance":"critical"}',
        NULL, 'text-embedding-3-small', false, 1, 3, parent_id, 'sql_import', 'rag_knowledge', NULL
    );

    INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
    VALUES (
        1,
        '개인정보보호 정책 총칙',
        'regulation',
        'ko',
        '제6조(개인정보보호 관리 체계) (1) 개인정보보호 위원회: CPO 주관, 분기 1회 개최. 구성: CPO, 법무팀장, IT보안팀장, 인사팀장, 각 부서 개인정보보호 실무자. 안건: 정책 개정, 사고 보고, 법규 변경 대응, 교육 계획. (2) 개인정보 처리 대장: 각 부서는 개인정보 처리 현황(수집항목, 목적, 보유기간, 접근자)을 기록·유지한다. 변경 발생 시 7일 이내 갱신. (3) 개인정보 영향평가: 5만명 이상의 민감정보 또는 고유식별정보를 처리하는 신규 시스템 도입 시 사전에 영향평가를 실시한다. (4) 내부 감사: 연 1회 이상 개인정보 처리 전반에 대한 자체 감사를 실시하고, 결과를 경영진에 보고한다. 미흡 사항은 60일 이내 시정한다. 제7조(정책 개정) (1) 본 정책은 연 1회 이상 검토·개정한다. (2) 개인정보 보호법 개정, 보호위원회 지침 변경, 개인정보 침해 사고 발생 시 수시 개정한다. (3) 개정 절차: 개인정보보호팀 초안 → CPO 검토 → 법무팀 법적 검토 → 경영회의 승인 → 전 직원 공지. 제8조(시행일) 본 정책은 2024년 1월 1일부터 시행한다.',
        '{"tags":["관리체계","개인정보위원회","영향평가","내부감사","처리대장","시행일"],"category":"개인정보보호","doc_category":"개인정보보호","importance":"critical"}',
        NULL, 'text-embedding-3-small', false, 2, 3, parent_id, 'sql_import', 'rag_knowledge', NULL
    );
END $$;

-- [문서 2] 개인정보 수집·동의 절차
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '개인정보 수집 및 동의 절차',
    'policy',
    'ko',
    '제1조(수집 원칙) (1) 개인정보는 정보주체의 동의를 받거나 법률에 특별한 규정이 있는 경우에만 수집한다. (2) 필요 최소한의 개인정보만 수집하며, 최소한의 정보 외의 개인정보 수집에 동의하지 않는다는 이유로 서비스 제공을 거부하지 아니한다. 제2조(동의 취득 방법) (1) 서면 동의: 별도의 동의서에 정보주체가 직접 서명한다. (2) 전자적 동의: 홈페이지, 앱 등에서 동의 내용을 확인한 후 체크박스에 동의한다. (3) 동의 사항 고지: ①수집 항목, ②수집 목적, ③보유·이용 기간, ④동의 거부 시 불이익(있는 경우)을 반드시 고지한다. (4) 필수 동의와 선택 동의를 구분하여 안내하며, 선택 동의는 별도로 받는다. 제3조(임직원 개인정보 수집) (1) 채용 시: 이력서, 자기소개서, 증빙서류(학위증, 경력증명서). 목적: 채용 심사. 보유: 채용 종료 후 6개월(불합격자), 재직 기간+퇴직 후 3년(합격자). (2) 입사 시: 주민등록번호(4대 보험·세금 신고용), 가족관계증명서, 통장사본. 목적: 인사·급여·복리후생 관리. (3) 재직 중: 인사평가 결과, 교육 이력, 건강검진 결과(본인 동의 시). 제4조(동의 철회) 정보주체는 언제든지 동의를 철회할 수 있으며, 철회 즉시 해당 개인정보를 파기한다. 단, 법령상 보관 의무가 있는 정보는 의무 기간까지 보관 후 파기한다.',
    '{"tags":["개인정보수집","동의","필수동의","선택동의","임직원정보","동의철회"],"category":"개인정보보호","doc_category":"개인정보보호","importance":"high"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- [문서 3] 개인정보 처리 목적 및 보유 기간 (멀티청크 2개)
DO $$
DECLARE parent_id BIGINT;
BEGIN
    INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
    VALUES (
        1,
        '개인정보 처리 목적 및 보유 기간',
        'policy',
        'ko',
        '제1조(처리 목적별 보유 기간) 당사는 다음 목적으로 개인정보를 처리하며, 목적 달성 시 지체 없이 파기한다. (1) 인사관리: 성명, 생년월일, 주소, 연락처, 학력, 경력, 가족사항 → 퇴직 후 3년. (2) 급여·세무: 주민등록번호, 계좌정보 → 「소득세법」에 따라 5년. (3) 4대 보험: 주민등록번호, 소득정보 → 「국민건강보험법」 등에 따라 3년. (4) 복리후생: 가족관계증명서, 건강검진 결과 → 해당 복지 종료 후 1년. (5) 교육·훈련: 교육이수내역, 자격증 사본 → 퇴직 후 3년. (6) 성과평가: 평가 결과, 피드백 기록 → 퇴직 후 3년. (7) 채용: 이력서, 자기소개서, 면접 평가표 → 불합격 통보 후 6개월. (8) CCTV 영상: 사업장 출입 영상 → 촬영일로부터 30일. 제2조(법령에 따른 보유) 다른 법률에 특별한 규정이 있는 경우 해당 법률의 규정에 따른다. 예: 「근로기준법」 근로자 명부 3년, 「국세기본법」 거래 기록 5년, 「전자상거래법」 소비자 불만 3년.',
        '{"tags":["보유기간","처리목적","인사관리","급여","4대보험","CCTV","법정보유"],"category":"개인정보보호","doc_category":"개인정보보호","importance":"high"}',
        NULL, 'text-embedding-3-small', false, 0, 2, NULL, 'sql_import', 'rag_knowledge',
        NULL
    ) RETURNING id INTO parent_id;

    INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
    VALUES (
        1,
        '개인정보 처리 목적 및 보유 기간',
        'policy',
        'ko',
        '제3조(보유 기간 산정 기준) (1) 보유 기간은 개인정보 수집 시 정보주체에게 고지한 기간을 원칙으로 한다. (2) 법령에서 정한 보유 기간이 동의 받은 기간보다 긴 경우, 법령 기간을 따른다. (3) 보유 기간 경과 후 5일 이내 파기한다. 제4조(보유 현황 관리) (1) 각 부서는 보유 중인 개인정보 파일의 현황(파일명, 항목, 건수, 보유기간, 접근권한자)을 분기 1회 업데이트한다. (2) 개인정보보호팀은 전사 보유 현황을 종합하여 CPO에게 보고한다. (3) 보유 기간이 만료된 개인정보는 자동 알림 시스템을 통해 담당자에게 파기 알림을 발송하며, 담당자는 7일 이내 파기 여부를 결정한다. 제5조(처리 목적 변경 시) (1) 개인정보를 당초 수집 목적 외의 용도로 이용하거나 제3자에게 제공하려는 경우, 정보주체에게 별도의 동의를 받아야 한다. (2) 동의 시 변경된 목적, 제공 항목, 보유 기간을 명확히 고지한다. (3) 법률에 특별한 규정이 있는 경우, 수사기관의 영장 제시, 생명·신체 안전을 위한 긴급 상황 등 법정 예외 사유에 한하여 동의 없이 처리할 수 있다.',
        '{"tags":["보유기간산정","보유현황관리","파기알림","목적변경","법정예외","자동알림"],"category":"개인정보보호","doc_category":"개인정보보호","importance":"high"}',
        NULL, 'text-embedding-3-small', false, 1, 2, parent_id, 'sql_import', 'rag_knowledge', NULL
    );
END $$;

-- [문서 4] 민감정보 및 고유식별정보 처리
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '민감정보 및 고유식별정보 처리 정책',
    'policy',
    'ko',
    '제1조(민감정보) (1) "민감정보"란 사상·신념, 노동조합·정당 가입·탈퇴, 정치적 견해, 건강, 성생활, 유전정보, 범죄경력, 인종·민족, 생체인식정보를 말한다. (2) 민감정보는 별도의 동의를 받은 경우 또는 법령에서 허용한 경우에만 처리한다. (3) 당사에서 처리하는 민감정보: ①건강검진 결과(산업안전보건법), ②장애 여부(장애인고용촉진법), ③노조 가입 여부(급여공제 목적). 제2조(고유식별정보) (1) "고유식별정보"란 주민등록번호, 여권번호, 운전면허번호, 외국인등록번호를 말한다. (2) 주민등록번호는 법률·대통령령·보호위원회 고시에서 구체적으로 허용한 경우에만 수집한다. (3) 당사의 주민등록번호 처리 근거: 「소득세법」 제145조(원천징수), 「국민건강보험법」 제12조, 「고용보험법」 제13조. (4) 여권번호: 해외 출장·파견 업무 처리 목적으로 수집하며, 업무 완료 후 즉시 파기한다. 제3조(추가 안전조치) (1) 민감정보·고유식별정보는 암호화하여 저장한다(AES-256 이상). (2) 접근 권한을 엄격히 제한하며, 접근 이력을 최소 3년간 보관한다. (3) 주민등록번호는 마스킹 처리하여 표시하며(예: 800101-1******), 전체 번호 조회는 CPO 승인 후에만 가능하다. (4) 민감정보가 포함된 문서는 별도의 잠금 캐비넷에 보관하며, 열쇠 관리대장을 운용한다.',
    '{"tags":["민감정보","고유식별정보","주민등록번호","건강검진","암호화","마스킹"],"category":"개인정보보호","doc_category":"개인정보보호","importance":"critical"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- [문서 5] 개인정보 제3자 제공
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '개인정보 제3자 제공 정책',
    'policy',
    'ko',
    '제1조(제3자 제공의 원칙) (1) 개인정보를 제3자에게 제공하려면 정보주체의 별도 동의를 받아야 한다. (2) 동의 시 고지 사항: ①제공받는 자, ②제공 목적, ③제공 항목, ④보유·이용 기간, ⑤동의 거부 시 불이익. 제2조(동의 없이 제공 가능한 경우) (1) 법률에 특별한 규정이 있는 경우(예: 국세청 원천징수 신고, 4대 보험 가입 신고). (2) 수사기관의 영장에 의한 요청. (3) 정보주체 또는 법정대리인이 의사표시를 할 수 없는 상태에서 생명·신체의 급박한 이익을 위해 필요한 경우. (4) 통계 작성, 학술 연구 목적으로 특정 개인을 알아볼 수 없는 형태로 제공하는 경우. 제3조(제공 현황) 당사의 주요 제3자 제공: (1) 국민건강보험공단: 직원 인적사항, 보수월액 → 건강보험 자격 관리 → 자격 상실 후 3년. (2) 국민연금공단: 직원 인적사항, 소득 → 연금 가입 관리 → 자격 상실 후 3년. (3) 고용노동부: 직원 인적사항, 고용정보 → 고용보험 관리 → 3년. (4) 세무서: 주민등록번호, 소득 → 원천세 신고 → 5년. (5) 위탁 급여 시스템(OOO사): 급여 관련 정보 → 급여 정산 → 계약 종료 시. 제4조(제공 시 안전조치) (1) 제3자 제공 시 암호화 전송(TLS 1.2 이상). (2) 제공 기록을 5년간 보관한다. (3) 제공받는 자의 개인정보 보호 수준을 사전에 확인한다.',
    '{"tags":["제3자제공","동의","국세청","4대보험","암호화전송","제공기록"],"category":"개인정보보호","doc_category":"개인정보보호","importance":"high"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- [문서 6] 개인정보 처리 위탁 관리 (멀티청크 2개)
DO $$
DECLARE parent_id BIGINT;
BEGIN
    INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
    VALUES (
        1,
        '개인정보 처리 위탁 관리',
        'policy',
        'ko',
        '제1조(위탁의 정의) "처리 위탁"이란 개인정보 처리 업무의 일부를 외부 업체에 맡겨 처리하게 하는 것을 말하며, 「제3자 제공」과 구별한다. 위탁은 위탁자의 업무 처리 목적 범위 내에서 수탁자가 대신 처리하는 것이다. 제2조(위탁 계약) (1) 위탁 시 반드시 문서(계약서)로 체결하며, 다음 사항을 명시한다: ①위탁 업무 내용, ②개인정보 처리 범위, ③재위탁 제한, ④안전관리 의무, ⑤수탁자 감독 방법, ⑥위반 시 손해배상. (2) 수탁자는 위탁받은 목적 외 개인정보를 이용·제공하지 않는다. (3) 계약 기간은 원칙적으로 1년 이내로 하며, 갱신 시 보안 점검 후 체결한다. 제3조(현행 위탁 현황) (1) 급여 아웃소싱(OO사): 성명, 계좌번호, 급여정보 → 급여 계산·지급 → 계약 종료 시 즉시 파기. (2) 건강검진 대행(XX병원): 성명, 생년월일, 건강검진 결과 → 검진 실시·결과 통보 → 검진 후 2년. (3) IT시스템 운영(△△사): 시스템 접속 로그, 사용자 계정정보 → 시스템 유지보수 → 계약 종료 시 파기. (4) 복리후생 운영(□□사): 성명, 부서, 복지포인트 → 복지몰 운영 → 계약 종료 시 파기.',
        '{"tags":["처리위탁","위탁계약","수탁자","급여아웃소싱","건강검진대행","IT운영"],"category":"개인정보보호","doc_category":"개인정보보호","importance":"high"}',
        NULL, 'text-embedding-3-small', false, 0, 2, NULL, 'sql_import', 'rag_knowledge',
        NULL
    ) RETURNING id INTO parent_id;

    INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
    VALUES (
        1,
        '개인정보 처리 위탁 관리',
        'policy',
        'ko',
        '제4조(수탁자 관리·감독) (1) 수탁자에 대해 연 1회 이상 개인정보 보호 실태 점검을 실시한다. (2) 점검 항목: 접근통제, 암호화, 파기 현황, 교육 실시, 사고 대응 체계. (3) 점검 결과 미흡 시 시정 요구하며, 시정되지 않을 경우 계약을 해지할 수 있다. (4) 수탁자가 개인정보 보호법을 위반하여 손해를 발생시킨 경우, 수탁자는 위탁자의 소속 직원으로 본다(법적 책임 동일). 제5조(재위탁) (1) 수탁자는 위탁자의 사전 서면 동의 없이 재위탁할 수 없다. (2) 재위탁 시 재수탁자에 대해서도 동일한 관리·감독 의무를 부과한다. 제6조(위탁 변경 시 공개) (1) 위탁 내용이 변경될 경우, 지체 없이 개인정보 처리방침을 업데이트한다. (2) 홈페이지, 사내 게시판 등을 통해 위탁 현황을 상시 공개한다. 제7조(계약 종료 시 처리) (1) 위탁 계약 종료 시 수탁자는 보유 중인 개인정보를 즉시 파기하고, 파기 확인서를 위탁자에게 제출한다. (2) 파기 완료 후 30일 이내 파기 증빙(화면 캡처, 파기 로그 등)을 제출한다.',
        '{"tags":["수탁자감독","재위탁","점검","파기확인서","계약종료","관리감독"],"category":"개인정보보호","doc_category":"개인정보보호","importance":"high"}',
        NULL, 'text-embedding-3-small', false, 1, 2, parent_id, 'sql_import', 'rag_knowledge', NULL
    );
END $$;

-- [문서 7] 정보주체의 권리와 행사 방법
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '정보주체의 권리와 행사 방법',
    'policy',
    'ko',
    '제1조(권리 내용) 정보주체는 다음의 권리를 가진다: (1) 열람권: 자신의 개인정보 처리 현황(수집 항목, 목적, 보유 기간, 제3자 제공 현황 등)을 열람할 수 있다. (2) 정정·삭제권: 사실과 다르거나 불필요한 개인정보의 정정 또는 삭제를 요구할 수 있다. (3) 처리정지권: 개인정보 처리의 정지를 요구할 수 있다. 단, 법률에 따른 의무 이행, 계약 이행, 정보주체 이익 보호 등의 경우 거절할 수 있다. (4) 동의 철회권: 이전에 한 동의를 언제든 철회할 수 있다. (5) 자동화된 의사결정에 대한 거부권: 자동화된 처리(프로파일링 등)에 의한 결정을 거부하고, 인적 개입을 요구할 수 있다. 제2조(행사 방법) (1) 서면: 「개인정보 열람/정정/삭제/처리정지 청구서」를 작성하여 인사팀(개인정보보호 담당)에 제출. (2) 이메일: privacy@company.com으로 청구서 첨부 제출. (3) 온라인: 사내 인트라넷 「개인정보 관리」 메뉴에서 직접 열람 및 정정 가능. (4) 대리인: 정보주체의 법정대리인 또는 위임을 받은 자가 대리 행사 가능(위임장 + 신분증 사본 필요). 제3조(처리 기한) (1) 열람: 청구 접수일로부터 10일 이내. (2) 정정·삭제: 청구 접수일로부터 10일 이내 조치 후 통지. (3) 처리 정지: 청구 접수일로부터 10일 이내 조치 후 통지. (4) 지연 시 사유와 처리 예정일을 정보주체에게 통지한다.',
    '{"tags":["정보주체권리","열람권","정정삭제권","처리정지","동의철회","자동화거부"],"category":"개인정보보호","doc_category":"개인정보보호","importance":"high"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- [문서 8] 개인정보 파기 절차 및 방법
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '개인정보 파기 절차 및 방법',
    'policy',
    'ko',
    '제1조(파기 원칙) (1) 보유 기간이 경과하거나 처리 목적이 달성된 개인정보는 지체 없이(5일 이내) 파기한다. (2) 다른 법령에 따라 보존이 필요한 경우, 해당 개인정보를 별도 분리하여 저장·관리하며, 법정 보유 기간 경과 후 파기한다. 제2조(파기 절차) (1) 파기 대상 선정: 보유 기간 만료 자동 알림 → 담당자 확인 → 파기 승인(팀장 이상). (2) 파기 실행: 개인정보보호 실무자가 파기를 실행한다. (3) 파기 기록: 「개인정보 파기 관리대장」에 파기 일자, 대상, 방법, 실행자, 확인자를 기록한다. (4) 파기 완료 보고: 분기별로 파기 현황을 CPO에게 보고한다. 제3조(파기 방법) (1) 전자적 파일: 복원이 불가능하도록 영구 삭제한다. ①DB 레코드: 해당 행 완전 삭제 후 덮어쓰기. ②파일: DoD 5220.22-M 표준 또는 동등 이상 방법으로 3회 이상 덮어쓰기. ③SSD: Secure Erase 또는 물리적 파쇄. (2) 종이 문서: 파쇄기(교차 절단, 4mm×40mm 이하)로 파쇄하거나 소각한다. (3) 매체(USB, HDD 등): 물리적 파쇄 또는 자기 소거(Degaussing)를 실시한다. 제4조(파기 예외) (1) 법정 보유 의무가 있는 정보는 별도 DB 또는 잠금 캐비넷에 분리 보관하며, 접근 권한을 CPO+해당 담당자로 제한한다. (2) 분리 보관된 개인정보는 법정 보유 기간 만료 후 5일 이내 파기한다.',
    '{"tags":["파기","파기절차","파기방법","복원불가","종이파쇄","매체파쇄","파기관리대장"],"category":"개인정보보호","doc_category":"개인정보보호","importance":"high"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- [문서 9] 개인정보 유출 사고 대응 절차 (멀티청크 2개)
DO $$
DECLARE parent_id BIGINT;
BEGIN
    INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
    VALUES (
        1,
        '개인정보 유출 사고 대응 절차',
        'procedure',
        'ko',
        '제1조(유출의 정의) "개인정보 유출"이란 법령이나 개인정보처리자의 자유로운 의사에 의하지 않고, 개인정보가 제3자에게 제공·열람되거나 외부로 유출되는 것을 말한다. 유형: ①해킹·악성코드 감염, ②내부자 유출, ③분실·도난, ④이메일 오발송, ⑤시스템 오류로 인한 노출. 제2조(대응 체계) (1) 1단계(인지·접수): 유출 인지 즉시 개인정보보호팀에 신고(24시간 핫라인 운영). (2) 2단계(초기 대응): ①유출 경로 차단(계정 잠금, 시스템 차단, 네트워크 격리). ②유출 범위 파악(영향받은 정보주체 수, 유출 항목, 유출 경로). ③증거 보전(로그, 스크린샷, 이메일 원본 등). (3) 3단계(통지): ①정보주체 통지(유출 사실, 유출 항목, 대응 조치, 피해 구제 방법, 문의처). ②보호위원회/한국인터넷진흥원(KISA) 신고: 1,000명 이상 유출 시 72시간 이내 신고. ③경영진 보고. (4) 4단계(피해 구제): 정보주체의 피해 최소화를 위한 조치(비밀번호 변경 안내, 신용 모니터링 서비스 제공 등). (5) 5단계(재발 방지): 근본 원인 분석, 보안 강화, 관련자 징계, 교육 강화.',
        '{"tags":["개인정보유출","사고대응","KISA신고","유출통지","증거보전","피해구제"],"category":"개인정보보호","doc_category":"개인정보보호","importance":"critical"}',
        NULL, 'text-embedding-3-small', false, 0, 2, NULL, 'sql_import', 'rag_knowledge',
        NULL
    ) RETURNING id INTO parent_id;

    INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
    VALUES (
        1,
        '개인정보 유출 사고 대응 절차',
        'procedure',
        'ko',
        '제3조(유출 통지 방법) (1) 서면: 정보주체의 주소지로 등기우편 발송. (2) 이메일: 정보주체의 이메일 주소로 발송(수신 확인 요청). (3) 전화: 1,000명 미만 유출 시 개별 전화 통지 가능. (4) 홈페이지 게시: 정보주체에게 개별 통지가 어려운 경우, 홈페이지에 30일 이상 게시. 제4조(과징금·과태료) (1) 유출 사고 발생 시 보호위원회 조사를 받을 수 있으며, 위반 내용에 따라 과징금(매출액의 3% 이내) 또는 과태료가 부과된다. (2) 통지 의무 미이행: 3,000만원 이하 과태료. (3) 안전조치 의무 미이행: 과징금 또는 2년 이하 징역·2,000만원 이하 벌금. 제5조(모의 훈련) (1) 연 1회 이상 개인정보 유출 사고 대응 모의 훈련을 실시한다. (2) 훈련 시나리오: 해킹, 내부자 유출, 이메일 오발송 등 실제 발생 가능 시나리오를 적용한다. (3) 훈련 후 평가 보고서를 작성하고, 미흡 사항을 개선한다. 제6조(손해배상) (1) 개인정보 유출로 인해 정보주체에게 손해가 발생한 경우, 당사는 고의·과실이 없음을 입증하지 못하면 손해배상 책임을 진다(입증 책임 전환). (2) 300인 이상 대량 유출 시 법정손해배상제도(피해자 1인당 300만원 이내)가 적용될 수 있다.',
        '{"tags":["유출통지","과징금","과태료","모의훈련","손해배상","법정손해배상"],"category":"개인정보보호","doc_category":"개인정보보호","importance":"critical"}',
        NULL, 'text-embedding-3-small', false, 1, 2, parent_id, 'sql_import', 'rag_knowledge', NULL
    );
END $$;

-- [문서 10] CCTV 운영 및 개인영상정보 보호
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    'CCTV 운영 및 개인영상정보 보호 정책',
    'policy',
    'ko',
    '제1조(설치 목적) 당사는 다음 목적으로 영상정보처리기기(CCTV)를 설치·운영한다: (1) 시설 안전 및 범죄 예방. (2) 출입 통제. (3) 주차장 관리. (4) 산업재해 예방(생산 현장). 제2조(설치 현황) (1) 사옥 1층 로비: 2대(출입 통제). (2) 지하 주차장: 4대(차량 관리, 범죄 예방). (3) 서버실: 2대(물리적 보안). (4) 생산동: 6대(산업안전). 총 14대 운영. 제3조(안내판 설치) CCTV 설치 장소마다 안내판을 부착하며, 안내판에는 ①설치 목적, ②촬영 범위, ③관리 책임자 성명·연락처, ④설치 시기를 기재한다. 제4조(촬영 제한) (1) 탈의실, 화장실, 휴게실 등 개인의 사생활을 현저히 침해할 우려가 있는 장소에는 설치하지 않는다. (2) 촬영 범위는 설치 목적에 필요한 최소한의 범위로 한정하며, 임의로 조작(줌·회전)하지 않는다. 제5조(영상정보 보관·파기) (1) 보관 기간: 촬영일로부터 30일. (2) 보관 기간 경과 시 자동 삭제(덮어쓰기 방식). (3) 수사기관 요청 등 법적 사유가 있는 경우, 해당 영상만 별도 보관할 수 있으며, 사유 해소 시 즉시 파기한다. 제6조(열람·제공) (1) 정보주체 본인이 촬영된 영상의 열람을 요구할 수 있다(서면 청구). (2) 제3자 제공: 법원 영장, 수사기관 요청 등 법적 근거가 있는 경우에만 제공한다. (3) 열람·제공 시 기록을 「영상정보 열람·제공 대장」에 기재한다.',
    '{"tags":["CCTV","영상정보","촬영제한","보관기간","안내판","열람제공"],"category":"개인정보보호","doc_category":"개인정보보호","importance":"medium"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- [문서 11] 임직원 개인정보 내부 관리 계획
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '임직원 개인정보 내부 관리 계획',
    'plan',
    'ko',
    '제1조(목적) 본 계획은 당사가 처리하는 임직원 개인정보의 안전한 관리를 위한 내부 관리 체계를 수립함을 목적으로 한다. 제2조(관리 조직) (1) CPO(개인정보보호 책임자): OOO 전무 (연락처: 02-XXXX-XXXX). (2) 개인정보보호 실무 담당: 인사팀 OOO 과장. (3) 부서별 개인정보보호 담당자: 각 부서장이 1인을 지정. 제3조(접근 권한 관리) (1) HRIS(인사정보시스템) 접근 권한: 인사팀 담당자에 한하여 부여하며, 직급별 열람 범위를 차등 적용한다. ①인사팀장: 전 직원 인사 정보 열람·수정. ②인사팀 담당자: 담당 부문 직원 인사 정보 열람·수정. ③부서장: 소속 부서원 기본 인사 정보 열람(성명, 직급, 연락처). ④일반 직원: 본인 정보만 열람·일부 수정(연락처, 비상연락망). (2) 권한 부여·변경·말소는 「접근 권한 관리대장」에 기록하며, 인사 이동·퇴직 시 즉시 권한을 회수한다. (3) 접근 권한 현황은 반기 1회 전수 점검한다. 제4조(비밀번호 관리) HRIS 비밀번호는 10자 이상, 영·숫·특수문자 조합, 90일 변경 주기를 적용한다. 제5조(교육 계획) (1) 전 직원 개인정보보호 교육: 연 1회(2시간 이상, 법정 의무). (2) 개인정보 취급자 교육: 반기 1회(4시간 이상, 실무 중심). (3) 신규 입사자 교육: 입사 후 1개월 이내. (4) 교육 이수 현황을 기록하고, 미이수 시 해당 부서장에게 통보한다.',
    '{"tags":["내부관리계획","접근권한","HRIS","CPO","교육계획","비밀번호관리"],"category":"개인정보보호","doc_category":"개인정보보호","importance":"high"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- [문서 12] 개인정보 국외 이전
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '개인정보 국외 이전 정책',
    'policy',
    'ko',
    '제1조(원칙) (1) 개인정보를 국외로 이전하려면 정보주체에게 관련 사항을 고지하고 별도 동의를 받아야 한다. (2) 고지 사항: ①이전되는 개인정보 항목, ②이전받는 자(업체명, 국가), ③이전 목적, ④이전 방법, ⑤보유 기간, ⑥동의 거부 시 불이익. 제2조(동의 없이 이전 가능한 경우) (1) 법률에 특별한 규정. (2) 정보주체와의 계약 이행에 필요(예: 해외 호텔 예약을 위한 여권 정보 전달). (3) 보호위원회가 인정하는 적정성 평가를 통과한 국가로의 이전. 제3조(현행 국외 이전 현황) (1) 글로벌 인사시스템(미국 소재 OO사 클라우드): 성명, 사번, 직급, 부서 → 본사 인사 통합 관리 → 계약 종료 시 파기. AWS US-East 리전 사용, 표준계약조항(SCC) 체결. (2) 해외 법인 인사 교류: 성명, 경력, 평가 결과 → 해외 파견·전보 관리 → 파견 종료 후 1년. (3) 글로벌 이메일 서비스(Microsoft 365, 데이터센터: 미국·유럽): 이메일 주소, 이메일 내용 → 이메일 서비스 제공 → 계약 종료 시. 제4조(안전조치) (1) 이전 시 암호화 전송(TLS 1.3). (2) 이전받는 자의 개인정보 보호 수준 점검(연 1회). (3) 「개인정보 보호법」 수준 이상의 보호를 보장하는 계약 체결. (4) 국외 이전 기록을 5년간 보관한다. 제5조(EU GDPR 대응) EU 거주 직원(유럽 법인)의 개인정보 처리 시 GDPR을 준수하며, DPO(Data Protection Officer)를 별도 지정한다.',
    '{"tags":["국외이전","SCC","GDPR","클라우드","해외파견","적정성평가"],"category":"개인정보보호","doc_category":"개인정보보호","importance":"high"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- [문서 13] 가명정보 처리 및 결합
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '가명정보 처리 및 결합 정책',
    'policy',
    'ko',
    '제1조(가명처리의 정의) "가명처리"란 개인정보의 일부를 삭제하거나 일부 또는 전부를 대체하는 등의 방법으로 추가 정보 없이는 특정 개인을 알아볼 수 없도록 처리하는 것을 말한다. 제2조(가명정보 처리 목적) (1) 통계 작성(인력 현황, 이직률 분석, 급여 분포). (2) 과학적 연구(HR 트렌드 분석, 직원 만족도 연구). (3) 공익적 기록 보존. 제3조(가명처리 방법) (1) 삭제: 성명, 주민등록번호 등 직접 식별자 삭제. (2) 총계 처리: 개별 값을 합계, 평균 등으로 대체(예: 개인 급여 → 부서별 평균 급여). (3) 범주화: 구체적 값을 범위로 대체(예: 나이 35→30대, 연봉 4,500만→4,000~5,000만). (4) 마스킹: 일부 문자를 *로 대체(예: 홍*동, 010-****-1234). (5) 가명 부여: 원래 값을 임의의 식별자로 대체(예: User_001). 제4조(안전조치) (1) 가명정보는 원본과 물리적·논리적으로 분리 저장한다. (2) 추가 정보(매핑 테이블, 암호화 키 등)는 별도 관리하며, 접근 권한을 CPO 승인자에 한정한다. (3) 가명정보 처리 기록을 3년간 보관한다. 제5조(가명정보 결합) (1) 가명정보를 다른 기관의 가명정보와 결합하려면 보호위원회가 지정한 전문기관을 통해서만 가능하다. (2) 결합 후 반출 시 익명 처리 여부를 전문기관이 확인한다. 제6조(재식별 금지) (1) 가명정보를 처리하는 과정에서 특정 개인을 알아볼 수 있게 된 경우, 즉시 처리를 중지하고 해당 정보를 회수·파기한다. (2) 재식별을 시도하는 행위는 징계 사유에 해당하며, 법적 처벌(3년 이하 징역 또는 3천만원 이하 벌금)을 받을 수 있다.',
    '{"tags":["가명정보","가명처리","재식별금지","마스킹","범주화","결합"],"category":"개인정보보호","doc_category":"개인정보보호","importance":"medium"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- [문서 14] 개인정보보호 책임자(CPO) 역할과 책무
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '개인정보보호 책임자(CPO) 역할과 책무',
    'policy',
    'ko',
    '제1조(지정) (1) 대표이사는 임원급 이상의 자를 개인정보보호 책임자(CPO)로 지정한다. (2) 현 CPO: 경영지원본부장 OOO 전무. (3) CPO 변경 시 개인정보 처리방침에 즉시 반영한다. 제2조(역할) (1) 개인정보 처리에 관한 정책 수립·시행·점검. (2) 개인정보 처리 관련 불만 처리 및 피해 구제. (3) 개인정보 유출 및 오·남용 방지를 위한 내부 통제. (4) 개인정보보호 교육 계획 수립 및 시행. (5) 개인정보 파일의 보호 및 관리·감독. (6) 개인정보 영향평가 실시 여부 결정 및 총괄. (7) 처리 목적 달성 후 파기 여부 확인. 제3조(권한) (1) CPO는 개인정보 처리와 관련한 모든 부서에 자료 제출 및 시정을 요구할 수 있다. (2) CPO의 시정 요구에 대해 각 부서장은 정당한 사유 없이 거부할 수 없다. (3) 경영진은 CPO가 독립적으로 업무를 수행할 수 있도록 인력, 예산, 권한을 보장한다. (4) CPO의 개인정보보호 업무 수행으로 인한 불이익을 주어서는 안 된다. 제4조(보고) (1) CPO는 분기 1회 개인정보 처리 현황을 경영진에게 보고한다. (2) 개인정보 유출 사고 발생 시 즉시 대표이사에게 보고한다. (3) 연 1회 개인정보 보호 연간 보고서를 작성하여 이사회에 보고한다.',
    '{"tags":["CPO","개인정보보호책임자","역할","권한","지정","보고"],"category":"개인정보보호","doc_category":"개인정보보호","importance":"high"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- [문서 15] 개인정보 처리방침 공개
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '개인정보 처리방침 공개 정책',
    'policy',
    'ko',
    '제1조(공개 의무) (1) 당사는 「개인정보 처리방침」을 수립하고 공개하여야 한다. (2) 처리방침에 포함할 사항: ①개인정보 처리 목적, ②처리 항목, ③보유 기간, ④제3자 제공 사항, ⑤처리 위탁 사항, ⑥정보주체 권리·행사 방법, ⑦안전성 확보 조치, ⑧CPO 연락처, ⑨국외 이전 사항, ⑩자동 수집 장치(쿠키 등) 사항. 제2조(공개 방법) (1) 회사 홈페이지: 첫 화면에서 1회 클릭으로 접근 가능한 위치에 게시(폰트 크기 9pt 이상). (2) 사내 인트라넷: 「개인정보보호」 메뉴에 상시 게시. (3) 사업장: 사무실 게시판에 출력물 부착(A4 이상 크기). 제3조(변경 시 절차) (1) 처리방침 변경 시 변경 사유, 변경 내용, 시행일을 명시한다. (2) 변경 전·후 내용을 비교하여 정보주체가 쉽게 확인할 수 있도록 한다. (3) 중요한 변경(수집 항목 추가, 제3자 제공 신설 등)은 시행 7일 전 사전 공지한다. (4) 처리방침 변경 이력을 3년간 보존한다. 제4조(이해가능성) (1) 처리방침은 정보주체가 이해하기 쉬운 용어로 작성한다. (2) 법적 용어가 불가피한 경우 괄호 안에 쉬운 설명을 병기한다. (3) 연 1회 이상 가독성 검토를 실시하여 개선한다.',
    '{"tags":["처리방침","공개","홈페이지","변경절차","가독성","이해가능성"],"category":"개인정보보호","doc_category":"개인정보보호","importance":"medium"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- [문서 16] 개인정보보호 교육 계획
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '개인정보보호 교육 계획',
    'plan',
    'ko',
    '제1조(교육 대상) (1) 전 임직원(정규직, 계약직, 파견직, 인턴 포함). (2) 개인정보 취급자(HRIS, 급여시스템, 고객DB 접근자 등)는 강화 교육 대상. (3) 수탁업체 직원(개인정보 처리 업무 수행자). 제2조(교육 과정) (1) 전직원 기본 교육(연 1회, 2시간): 개인정보보호법 개요, 정보주체 권리, 유출 예방, 사고 대응, 법적 책임. (2) 취급자 심화 교육(반기 1회, 4시간): 접근 권한 관리, 암호화 실무, 로그 관리, 위탁 관리, 파기 실무, 최신 판례. (3) 신규 입사자 교육(입사 1개월 내, 2시간): 회사 개인정보 처리 현황, 보안 서약서, 시스템 접근 권한 안내. (4) CPO·관리자 교육(연 1회, 3시간): 법규 변경사항, 사고 대응 리더십, 내부 감사 방법, 과징금 사례. (5) 수탁업체 교육(연 1회, 2시간): 위탁 범위, 안전관리 의무, 사고 시 통보 절차. 제3조(교육 방법) 온라인(LMS), 집합교육, 동영상, 퀴즈, 사례 학습을 병행한다. 제4조(평가) 교육 후 평가 점수 80점 미만 시 재교육을 실시한다. 제5조(기록 관리) 교육 이수 현황(일시, 대상, 내용, 평가 결과)을 3년간 보관하며, 감사 시 제출한다. 제6조(미이수 시 조치) (1) 1차 미이수: 해당 부서장에게 통보 및 2주 내 보충 교육. (2) 2차 미이수: 인사고과 반영(감점). (3) 3차 미이수: 개인정보 접근 권한 정지.',
    '{"tags":["개인정보교육","법정교육","취급자교육","CPO교육","LMS","미이수조치"],"category":"개인정보보호","doc_category":"개인정보보호","importance":"medium"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- [문서 17] 쿠키 및 자동 수집 장치 운영 정책
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '쿠키 및 자동 수집 장치 운영 정책',
    'policy',
    'ko',
    '제1조(목적) 당사는 이용자 맞춤 서비스 제공 및 서비스 개선을 위하여 쿠키(Cookie) 및 자동 수집 장치를 운용한다. 제2조(쿠키의 정의) "쿠키"란 웹서버가 이용자의 브라우저에 보내는 소량의 텍스트 파일로, 이용자의 하드디스크에 저장된다. 제3조(사용 목적) (1) 필수 쿠키: 로그인 세션 유지, 보안 인증(CSRF 방지). (2) 기능 쿠키: 언어 설정, 화면 레이아웃 등 이용자 환경 설정 기억. (3) 분석 쿠키: 서비스 이용 통계(방문 수, 페이지뷰, 체류 시간). (4) 마케팅 쿠키: 사내 인트라넷에서는 사용하지 않음. 제4조(동의 및 거부) (1) 이용자는 브라우저 설정을 통해 쿠키를 허용하거나 거부할 수 있다. (2) 필수 쿠키를 거부하면 로그인 등 핵심 기능이 제한될 수 있다. (3) 외부 홈페이지의 경우, 첫 방문 시 쿠키 배너를 통해 동의를 받는다. 제5조(보관 기간) (1) 세션 쿠키: 브라우저 종료 시 자동 삭제. (2) 영속 쿠키: 최대 1년, 설정 목적 달성 후 자동 삭제. (3) 분석 쿠키: 최대 2년. 제6조(제3자 쿠키) 외부 분석 도구(Google Analytics 등) 사용 시 해당 서비스의 개인정보 처리방침을 고지하며, IP 익명화(마지막 옥텟 삭제)를 적용한다.',
    '{"tags":["쿠키","자동수집","세션쿠키","분석쿠키","GoogleAnalytics","동의배너"],"category":"개인정보보호","doc_category":"개인정보보호","importance":"low"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- [문서 18] 채용 과정에서의 개인정보 처리 (멀티청크 2개)
DO $$
DECLARE parent_id BIGINT;
BEGIN
    INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
    VALUES (
        1,
        '채용 과정에서의 개인정보 처리',
        'policy',
        'ko',
        '제1조(수집 항목) (1) 필수: 성명, 생년월일, 연락처(전화·이메일), 학력(학교명, 전공, 졸업연도), 경력(회사명, 기간, 직무), 자격증. (2) 선택: 사진, 추천인 정보, 포트폴리오 URL, 어학성적. (3) 수집 금지 항목: 종교, 혼인 여부, 가족의 직업·재산, 신체 조건(키·몸무게, 직무 관련성 있는 경우 제외), 출신 지역, 범죄 경력(법령에 따른 경우 제외). 제2조(수집 경로) (1) 자사 채용 페이지 직접 입력. (2) 채용 플랫폼(사람인, 잡코리아 등) 연동. (3) 이메일 접수(채용 전용 이메일: recruit@company.com). (4) 헤드헌팅 업체 추천(정보주체 동의 확인 후 수령). 제3조(이용 목적) (1) 채용 심사(서류 전형, 면접 전형, 적성검사). (2) 합격 통지 및 입사 안내. (3) 채용 비리 방지(허위 경력·학력 확인). (4) 인재 풀 관리(정보주체 별도 동의 시). 제4조(면접 시 주의) (1) 면접관은 직무와 무관한 개인정보(결혼 계획, 임신 여부, 정치적 성향, 종교 등)를 질문하지 않는다. (2) 면접 평가표에 직무 무관 개인정보를 기재하지 않는다. (3) 면접관 교육 시 개인정보보호 관련 주의사항을 필수로 포함한다.',
        '{"tags":["채용개인정보","수집항목","수집금지","면접주의","인재풀","채용플랫폼"],"category":"개인정보보호","doc_category":"개인정보보호","importance":"high"}',
        NULL, 'text-embedding-3-small', false, 0, 2, NULL, 'sql_import', 'rag_knowledge',
        NULL
    ) RETURNING id INTO parent_id;

    INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
    VALUES (
        1,
        '채용 과정에서의 개인정보 처리',
        'policy',
        'ko',
        '제5조(보유 기간) (1) 합격자: 입사 후 인사 파일에 통합 관리(임직원 개인정보 보유 기간 적용). (2) 불합격자: 채용 결과 통보 후 6개월간 보관 후 파기. (3) 인재 풀 등록 동의자: 동의일로부터 2년간 보관. 기간 만료 전 연장 동의를 구하며, 동의하지 않으면 파기. (4) 채용 과정에서 제출받은 서류 원본(학위증, 자격증 사본 등): 불합격자는 반환 요청 시 14일 이내 반환하고, 미요청 시 보유 기간 만료 후 파기. 제6조(채용 플랫폼 연동) (1) 외부 채용 플랫폼에서 지원자 정보를 수신할 때, 지원자가 해당 플랫폼에서 동의한 범위 내에서만 이용한다. (2) 채용 플랫폼과의 API 연동 시 개인정보 전송은 암호화(TLS 1.2 이상)로 처리한다. (3) 연동 플랫폼의 개인정보 보호 수준을 연 1회 점검한다. 제7조(배경 조회) (1) 경력 확인, 학력 확인, 자격증 진위 확인은 지원자의 별도 동의 후 실시한다. (2) 범죄 경력 조회: 법률에 따라 허용되는 직무(아동 관련 종사자 등)에 한하여, 지원자 동의 후 공식 기관을 통해 확인한다. (3) 신용 정보 조회: 금융 관련 직무에 한하여, 지원자 동의 후 신용정보회사를 통해 확인한다. 제8조(파기 방법) 전자 파일: 영구 삭제. 종이 서류: 파쇄. 파기 후 「채용 개인정보 파기 대장」에 기록한다.',
        '{"tags":["채용보유기간","불합격자파기","인재풀","배경조회","채용플랫폼연동","파기방법"],"category":"개인정보보호","doc_category":"개인정보보호","importance":"high"}',
        NULL, 'text-embedding-3-small', false, 1, 2, parent_id, 'sql_import', 'rag_knowledge', NULL
    );
END $$;

-- [문서 19] 개인정보보호 FAQ
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '개인정보보호 FAQ',
    'faq',
    'ko',
    'Q1: 내 개인정보가 어떻게 사용되는지 확인하려면? A1: 사내 인트라넷 「개인정보 관리」 메뉴에서 본인의 개인정보 처리 현황을 열람할 수 있습니다. 추가로 서면 또는 이메일(privacy@company.com)로 상세 열람을 청구할 수 있으며, 10일 이내 회신됩니다. Q2: 주민등록번호를 왜 수집하나요? A2: 소득세법에 따른 원천징수 신고, 국민건강보험·국민연금·고용보험·산재보험 가입 관리 목적으로 법적 근거에 의해 수집합니다. 법적 의무 이외의 목적으로는 사용하지 않습니다. Q3: 퇴사 후 내 개인정보는 어떻게 되나요? A3: 퇴직 후 인사기록은 근로기준법에 따라 3년간 보관 후 파기합니다. 급여·세무 관련 정보는 소득세법에 따라 5년간 보관됩니다. 법정 보유 기간이 없는 정보는 퇴직 후 즉시 파기합니다. Q4: 이메일을 잘못 보내서 개인정보가 유출된 것 같아요. A4: 즉시 개인정보보호팀(내선 1234 또는 privacy@company.com)에 신고해 주세요. 수신자에게 삭제를 요청하고, 유출 범위를 파악하여 필요 시 정보주체에게 통지합니다. 신고는 빠를수록 피해를 최소화할 수 있습니다. Q5: 가족관계증명서는 왜 제출해야 하나요? A5: 부양가족 연말정산 공제, 가족수당 지급, 경조사 지원 등 복리후생 목적으로 필요합니다. 해당 목적 달성 후 또는 변경 사항 반영 후 원본은 반환하거나 파기합니다. Q6: 협력업체 직원인데 개인정보보호 교육을 받아야 하나요? A6: 네, 당사 개인정보를 처리하는 협력업체 직원은 연 1회 개인정보보호 교육을 이수해야 합니다. 교육 미이수 시 프로젝트 투입이 제한될 수 있습니다.',
    '{"tags":["FAQ","개인정보열람","주민등록번호","퇴사후처리","이메일유출","가족관계증명서"],"category":"개인정보보호","doc_category":"개인정보보호","importance":"medium"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- [문서 20] 개인정보보호 위반 시 제재
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '개인정보보호 위반 시 제재 기준',
    'regulation',
    'ko',
    '제1조(내부 징계) (1) 경미한 위반: ①개인정보보호 교육 미이수(1차: 경고, 2차: 인사고과 감점, 3차: 접근권한 정지). ②개인정보 포함 문서 잠금장치 미사용: 시정 요구 + 재교육. ③비밀번호 공유 등 부주의: 경고 + 재교육. (2) 중대한 위반: ①개인정보 무단 열람·유출: 정직 이상~해고. ②개인정보를 업무 외 목적으로 이용: 정직 이상. ③개인정보 유출 사실 은폐·축소: 해고 + 법적 조치. ④수집 동의 없이 개인정보 수집: 감봉 이상. (3) 고의적 범법: ①개인정보를 외부에 판매·제공: 즉시 해고 + 형사 고발. ②재식별 시도: 즉시 해고 + 형사 고발. 제2조(법적 제재) (1) 개인정보 보호법 위반 시 다음의 법적 제재를 받을 수 있다: ①개인정보 무단 수집·이용·제공: 5년 이하 징역 또는 5천만원 이하 벌금. ②안전조치 의무 위반으로 유출 발생: 2년 이하 징역 또는 2천만원 이하 벌금. ③개인정보 부정 사용(영리 목적): 10년 이하 징역 또는 1억원 이하 벌금. ④통지·신고 의무 미이행: 3천만원 이하 과태료. ⑤처리방침 미공개: 1천만원 이하 과태료. (2) 과징금: 매출액의 3% 이내(개인정보 보호법 제64조의2). 제3조(제재 절차) (1) 위반 사실 인지 → CPO 보고 → 인사위원회 회부 → 징계 결정 → 결과 통지. (2) 징계 대상자는 인사위원회에서 소명 기회를 부여받는다. (3) 징계 결정 후 7일 이내 이의 신청 가능(재심위원회). (4) 중대 위반의 경우, 징계와 별도로 수사기관에 고발할 수 있다.',
    '{"tags":["위반제재","징계","벌금","과징금","형사처벌","내부징계","해고"],"category":"개인정보보호","doc_category":"개인정보보호","importance":"high"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- original_content = content 동기화 (INSERT 후 실행)
UPDATE tb_docs SET original_content = content
WHERE source_type = 'sql_import' AND usage_type = 'rag_knowledge' AND original_content IS NULL;
