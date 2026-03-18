-- ============================================================
-- RAG 문서 데이터 - Part 07: 조직문화/윤리경영/행동강령
-- 총 문서 수: 20개 (논리적 문서), 멀티청크 포함 총 28행
-- 생성일: 2026-02-27
-- 용도: RAG 검색 테스트 (RAGAS 평가용)
-- ============================================================

-- [문서 1] 핵심가치 및 조직문화 헌장 (멀티청크 3개)
DO $$
DECLARE parent_id BIGINT;
BEGIN
    INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
    VALUES (
        1,
        '핵심가치 및 조직문화 헌장',
        'regulation',
        'ko',
        '제1조(목적) 본 헌장은 당사의 핵심가치를 정의하고, 모든 임직원이 공유해야 할 조직문화의 방향을 설정함을 목적으로 한다. 제2조(핵심가치) 당사는 다음 5대 핵심가치를 경영의 근본으로 삼는다: (1) 신뢰(Trust): 고객, 파트너, 동료 간의 약속을 지키며, 투명한 소통으로 신뢰를 구축한다. (2) 혁신(Innovation): 현재에 안주하지 않고, 끊임없는 도전과 창의적 사고로 새로운 가치를 창출한다. (3) 협업(Collaboration): 부서·직급의 경계를 넘어 함께 일하며, 다양한 관점을 존중하고 시너지를 만든다. (4) 성장(Growth): 개인의 성장이 조직의 성장이며, 학습하는 조직문화를 통해 함께 발전한다. (5) 책임(Responsibility): 자신의 업무와 결정에 책임을 지며, 사회적 책임을 다하는 기업시민으로서의 역할을 이행한다. 제3조(문화 원칙) (1) 수평적 소통: 직급에 관계없이 자유롭게 의견을 개진하고 경청하는 문화를 지향한다. (2) 실패를 두려워하지 않는 문화: 도전과 실험을 장려하며, 실패에서 학습하는 것을 가치 있게 여긴다. (3) 워라밸(Work-Life Balance): 업무와 개인 생활의 균형을 존중하며, 장시간 근무를 미덕으로 여기지 않는다.',
        '{"tags":["핵심가치","조직문화","신뢰","혁신","협업","성장","책임"],"category":"조직문화","doc_category":"조직문화","importance":"critical"}',
        NULL, 'text-embedding-3-small', false, 0, 3, NULL, 'sql_import', 'rag_knowledge',
        NULL
    ) RETURNING id INTO parent_id;

    INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
    VALUES (
        1,
        '핵심가치 및 조직문화 헌장',
        'regulation',
        'ko',
        '제4조(일하는 방식) (1) 호칭: 전 직원 "님" 호칭 사용을 원칙으로 한다(예: 홍길동 님). 직급 호칭(부장님, 과장님)은 공식 대외 업무 시에만 사용한다. (2) 회의 문화: ①회의는 목적과 안건을 사전에 공유한다. ②1시간을 초과하지 않도록 하며, 45분 회의+15분 정리를 권장한다. ③참석 인원은 의사결정에 필요한 최소 인원으로 한정한다. ④회의록은 24시간 이내 공유하며, 결정 사항과 담당자를 명시한다. ⑤금요일 오후(14시 이후)에는 회의를 지양한다(집중 업무 시간). (3) 보고 문화: ①보고서는 A4 1매(또는 슬라이드 3장) 이내로 핵심만 작성한다. ②중간 보고를 활성화하여 방향 수정 비용을 줄인다. ③나쁜 소식일수록 빨리 공유하는 문화를 장려한다. (4) 피드백 문화: 칭찬은 공개적으로, 개선 피드백은 1:1로. SBI(Situation-Behavior-Impact) 모델을 활용한 구체적 피드백을 권장한다. (5) 업무 시간: 유연근무제를 운영하며, 코어타임(10:00~16:00)을 준수한다. 퇴근 후·주말 업무 연락을 자제하며, 긴급 시에만 예외로 한다.',
        '{"tags":["일하는방식","님호칭","회의문화","보고문화","피드백","유연근무"],"category":"조직문화","doc_category":"조직문화","importance":"critical"}',
        NULL, 'text-embedding-3-small', false, 1, 3, parent_id, 'sql_import', 'rag_knowledge', NULL
    );

    INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
    VALUES (
        1,
        '핵심가치 및 조직문화 헌장',
        'regulation',
        'ko',
        '제5조(조직문화 활동) (1) 타운홀 미팅: 분기 1회 전사 타운홀 미팅을 실시하며, CEO가 경영 현황을 투명하게 공유하고 직원 질의에 답변한다. (2) 팀 빌딩: 반기 1회 부서별 팀 빌딩 활동을 지원하며, 1인당 10만원의 예산을 배정한다. (3) 올핸즈(All-Hands): 월 1회 전사 조회를 실시하며, 우수 사례 공유, 신규 프로젝트 소개, 신입사원 환영을 진행한다. (4) 문화의 날: 매월 셋째 주 수요일을 "문화의 날"로 지정하여 17시 퇴근을 권장하고, 문화·예술·체육 활동을 장려한다. (5) 동호회: 5인 이상으로 구성된 동호회를 지원하며, 월 5만원/인 활동비를 지급한다. 제6조(문화 측정) (1) 연 1회 조직문화 진단(Great Place to Work 방법론 활용)을 실시하고 결과를 전 직원에게 공개한다. (2) 분기 1회 Pulse Survey(5문항 이내 간이 설문)를 실시하여 문화 변화를 추적한다. (3) 진단 결과를 바탕으로 개선 과제를 도출하고, 다음 분기 실행 계획을 수립한다. 제7조(시행일) 본 헌장은 2024년 1월 1일부터 시행한다.',
        '{"tags":["타운홀","팀빌딩","올핸즈","문화의날","동호회","조직문화진단","PulseSurvey"],"category":"조직문화","doc_category":"조직문화","importance":"critical"}',
        NULL, 'text-embedding-3-small', false, 2, 3, parent_id, 'sql_import', 'rag_knowledge', NULL
    );
END $$;

-- [문서 2] 임직원 행동강령
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '임직원 행동강령',
    'regulation',
    'ko',
    '제1조(적용 대상) 본 행동강령은 당사의 모든 임직원(정규직, 계약직, 파견직, 인턴)에게 적용된다. 제2조(법규 준수) 모든 업무 수행에 있어 관련 법률, 규정, 사내 규칙을 준수하며, 법률과 사내 규칙이 충돌할 경우 법률을 우선한다. 제3조(이해충돌 방지) (1) 임직원은 개인의 이익이 회사의 이익과 충돌하는 상황을 회피해야 한다. (2) 이해충돌이 발생하거나 발생 가능성이 있는 경우, 즉시 상급자 및 윤리경영팀에 신고한다. (3) 이해충돌 유형: ①본인 또는 가족이 경쟁사·거래처의 임직원인 경우, ②회사 거래에서 개인적 이익을 취하는 경우, ③사내 정보를 이용한 투자·거래. 제4조(선물·접대) (1) 직무와 관련된 선물·접대는 원칙적으로 수수하지 않는다. (2) 부득이하게 수수한 경우, 5만원 초과 시 3일 이내 윤리경영팀에 신고하고 처리 방법을 안내받는다. (3) 현금·상품권은 금액에 관계없이 수수 금지. (4) 경조사비: 5만원 이하, 화환·조화 10만원 이하만 수수 가능. 제5조(공정 경쟁) (1) 불공정 거래, 담합, 입찰 비리에 관여하지 않는다. (2) 경쟁사의 영업비밀을 부정하게 취득·이용하지 않는다. (3) 부당한 방법으로 거래처에 불이익을 주지 않는다. 제6조(회사 자산 보호) 회사의 유·무형 자산(시설, 장비, 정보, 지적재산권)을 사적으로 사용하거나 외부에 유출하지 않는다.',
    '{"tags":["행동강령","이해충돌","선물접대","공정경쟁","법규준수","자산보호"],"category":"윤리경영","doc_category":"조직문화","importance":"high"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- [문서 3] 직장 내 괴롭힘 예방 및 대응 (멀티청크 2개)
DO $$
DECLARE parent_id BIGINT;
BEGIN
    INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
    VALUES (
        1,
        '직장 내 괴롭힘 예방 및 대응 정책',
        'policy',
        'ko',
        '제1조(정의) "직장 내 괴롭힘"이란 사용자 또는 근로자가 직장에서의 지위 또는 관계 등의 우위를 이용하여 업무상 적정 범위를 넘어 다른 근로자에게 신체적·정신적 고통을 주거나 근무환경을 악화시키는 행위를 말한다(근로기준법 제76조의2). 제2조(금지 행위) (1) 신체적 괴롭힘: 때리기, 물건 던지기, 신체 접촉 강요. (2) 언어적 괴롭힘: 폭언, 욕설, 비하 발언, 험담, 반복적 비난. (3) 관계적 괴롭힘: 의도적 따돌림, 업무 배제, 정보 차단, 회식·회의 배제. (4) 업무적 괴롭힘: 과도한 업무 부여, 업무 미부여(직무 박탈), 능력 이하 단순 업무만 반복 지시, 사적 심부름. (5) 디지털 괴롭힘: 퇴근 후·주말 반복적 업무 연락, SNS 감시, 온라인 비방. 제3조(신고 절차) (1) 피해자 또는 목격자는 다음 채널로 신고한다: ①윤리경영팀(내선 5678, ethics@company.com). ②인사팀 괴롭힘 상담 창구. ③외부 신고 핫라인(02-XXXX-YYYY, 24시간 운영). ④사내 인트라넷 「익명 신고」 게시판. (2) 신고는 실명 또는 익명 모두 가능하다. (3) 신고 접수 시 즉시 피해자 보호 조치를 취한다(근무 장소 변경, 유급 휴가 등).',
        '{"tags":["직장내괴롭힘","예방","신고절차","금지행위","디지털괴롭힘","피해자보호"],"category":"윤리경영","doc_category":"조직문화","importance":"critical"}',
        NULL, 'text-embedding-3-small', false, 0, 2, NULL, 'sql_import', 'rag_knowledge',
        NULL
    ) RETURNING id INTO parent_id;

    INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
    VALUES (
        1,
        '직장 내 괴롭힘 예방 및 대응 정책',
        'policy',
        'ko',
        '제4조(조사 절차) (1) 신고 접수 후 7일 이내 조사에 착수한다. (2) 조사 주체: 윤리경영팀 + 외부 전문가(필요 시). (3) 조사 방법: 피해자·가해자·목격자 면담, 증거(메시지, 이메일, CCTV 등) 확인. (4) 조사 기간: 원칙적으로 30일 이내(복잡한 사안은 30일 연장 가능). (5) 조사 과정에서 피해자와 가해자를 분리하며, 피해자의 의사에 반하여 조정을 강요하지 않는다. 제5조(판정 및 조치) (1) 괴롭힘 인정 시: ①가해자: 경고, 감봉, 정직, 전보, 해고 등 징계(정도에 따라). ②피해자: 원상복구, 심리상담 지원, 불이익 방지. ③재발 방지 교육. (2) 괴롭힘 불인정 시: 신고자에게 결과와 사유를 통지하며, 신고 행위로 인한 불이익을 주지 않는다. 제6조(보복 금지) (1) 신고자, 피해자, 증인에게 어떠한 보복 행위도 금지한다. (2) 보복 행위가 확인될 경우, 원래 괴롭힘 행위보다 중한 징계를 부과한다. 제7조(예방 교육) (1) 연 1회(2시간) 전 직원 대상 직장 내 괴롭힘 예방 교육을 실시한다. (2) 관리자 대상 추가 교육(연 1회, 3시간): 괴롭힘 인지, 초기 대응, 피해자 보호 방법. (3) 교육 미이수 시 인사고과에 반영한다.',
        '{"tags":["괴롭힘조사","판정","징계","보복금지","예방교육","관리자교육"],"category":"윤리경영","doc_category":"조직문화","importance":"critical"}',
        NULL, 'text-embedding-3-small', false, 1, 2, parent_id, 'sql_import', 'rag_knowledge', NULL
    );
END $$;

-- [문서 4] 직장 내 성희롱 예방 및 처리
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '직장 내 성희롱 예방 및 처리 정책',
    'policy',
    'ko',
    '제1조(정의) "직장 내 성희롱"이란 사업주·상급자 또는 근로자가 직장 내의 지위를 이용하거나 업무와 관련하여 다른 근로자에게 성적 언동 등으로 성적 굴욕감 또는 혐오감을 느끼게 하거나, 성적 언동에 대한 불응을 이유로 고용상 불이익을 주는 것을 말한다(남녀고용평등법 제2조). 제2조(유형) (1) 육체적: 불필요한 신체 접촉, 포옹·키스 등 강요, 특정 신체 부위를 만지거나 응시. (2) 언어적: 성적 농담, 외모에 대한 성적 비유, 음란한 내용의 전화·문자·이메일, 성적 경험·관계 질문. (3) 시각적: 음란한 사진·영상 게시·유포, 외설적 행위를 고의로 노출, 성적 의미가 담긴 이모티콘·밈 전송. (4) 기타: 회식 시 음주·춤 강요, 노래방에서 듀엣 강요, 성별을 이유로 한 업무 배제("여자니까 커피 타와"). 제3조(신고·처리) (1) 남녀고용평등법에 따른 고충 처리 위원(인사팀장)에게 신고. (2) 조사 절차는 직장 내 괴롭힘과 동일하게 적용. (3) 가해자 징계: 경고~해고(수준에 따라). 반복 시 가중 징계. (4) 사업주의 의무: 피해자에게 해고·전보 등 불이익 조치를 취하면 3년 이하 징역 또는 3천만원 이하 벌금. 제4조(예방 교육) (1) 연 1회(1시간 이상) 전 직원 성희롱 예방 교육 실시(법정 의무). (2) 교육 내용: 성희롱 정의·유형, 판례, 신고 절차, 제재, 피해자 보호. (3) 교육 미실시 과태료: 500만원 이하. (4) 교육 자료를 사내 인트라넷에 상시 게시한다.',
    '{"tags":["성희롱","예방교육","법정의무","신고처리","남녀고용평등","유형"],"category":"윤리경영","doc_category":"조직문화","importance":"critical"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- [문서 5] 다양성·형평성·포용(DEI) 정책
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '다양성·형평성·포용(DEI) 정책',
    'policy',
    'ko',
    '제1조(목적) 당사는 성별, 연령, 인종, 국적, 종교, 장애, 성적 지향, 학력, 출신 지역 등에 관계없이 모든 임직원이 존중받고 공정한 기회를 부여받는 일터를 만들고자 한다. 제2조(다양성, Diversity) (1) 채용: 다양한 배경의 인재를 적극 채용하며, 특정 대학·지역·성별 편중을 지양한다. (2) 블라인드 채용: 서류 전형 시 사진, 출신 학교, 출신 지역을 배제하여 평가한다. (3) 장애인 고용: 법정 의무 고용률(3.1%) 이상을 유지하며, 합리적 편의를 제공한다. (4) 여성 관리자: 2026년까지 관리자(팀장급 이상) 중 여성 비율 30% 달성을 목표로 한다. 제3조(형평성, Equity) (1) 동일 가치 노동에 대한 동일 보수를 보장한다(성별 임금 격차 해소). (2) 승진·평가 시 객관적 기준을 적용하며, 비가시적 편견(unconscious bias)을 방지하기 위한 교육을 실시한다. (3) 임산부, 장애인, 고령 직원 등에 대한 합리적 배려(업무 조정, 시설 개선)를 제공한다. 제4조(포용, Inclusion) (1) 모든 직원의 의견이 존중받는 심리적 안전감(Psychological Safety)을 보장한다. (2) DEI 위원회를 운영하며, 반기 1회 DEI 현황(성별·연령·장애 분포, 임금 격차 등)을 전사에 공개한다. (3) DEI 관련 고충은 윤리경영팀을 통해 접수하며, 차별 행위에 대해 징계를 부과한다. 제5조(교육) 연 1회 무의식적 편견(Unconscious Bias) 교육을 전 직원에게 실시한다.',
    '{"tags":["DEI","다양성","형평성","포용","블라인드채용","성별임금격차","장애인고용"],"category":"조직문화","doc_category":"조직문화","importance":"high"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- [문서 6] 수평적 소통 및 커뮤니케이션 가이드
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '수평적 소통 및 커뮤니케이션 가이드',
    'guide',
    'ko',
    '제1조(소통 채널) (1) 공식 채널: ①이메일(업무 기록이 필요한 소통). ②사내 메신저(Slack/Teams)(실시간 소통, 간단 업무 조율). ③화상회의(원격 미팅). ④사내 게시판(공지, 정보 공유). (2) 비공식 채널: ①CEO Office Hour(월 1회, 직원 누구나 CEO와 30분 면담). ②Skip-Level Meeting(분기 1회, 차상위 리더와 직접 대화). ③익명 건의함(사내 인트라넷, 월 1회 경영진 답변 공개). ④점심 런치룰렛(무작위 타 부서 동료와 점심식사). 제2조(소통 원칙) (1) 존중의 원칙: 상대방의 의견을 경청하고, 다른 의견에도 인격을 존중한다. (2) 투명성의 원칙: 업무 관련 정보는 가능한 한 공개·공유하며, 정보의 독점을 지양한다. (3) 적시성의 원칙: 질문·요청에 대해 24시간(영업일 기준) 이내 최초 응답한다. (4) 건설적 비판: 문제를 지적할 때 대안을 함께 제시하며, 개인이 아닌 업무·프로세스에 초점을 맞춘다. 제3조(커뮤니케이션 매너) (1) 이메일: 제목에 [요청/공유/참고/긴급] 태그를 붙여 목적을 명확히 한다. 수신자를 최소화하고, CC는 정보 공유 목적으로만 사용. (2) 메신저: 업무 시간 외 알림을 자제하며, 예약 발송 기능 활용. 이모지 리액션으로 간단한 확인·동의를 표현. (3) 회의: 시작 시간과 종료 시간을 엄수하며, 불참 시 사전에 알린다.',
    '{"tags":["수평소통","커뮤니케이션","CEO면담","SkipLevel","익명건의함","이메일매너"],"category":"조직문화","doc_category":"조직문화","importance":"medium"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- [문서 7] 워라밸(Work-Life Balance) 정책
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '워라밸(Work-Life Balance) 정책',
    'policy',
    'ko',
    '제1조(근무시간) (1) 기본 근무시간: 주 40시간, 1일 8시간. (2) 유연근무제: 시차출퇴근제를 시행하며, 출근 시간을 07:00~10:00 사이에서 선택할 수 있다. 코어타임(10:00~16:00)은 반드시 근무한다. (3) 선택적 근로시간제: R&D 부서는 월 단위로 총 근무시간을 충족하면 일일 근무시간을 자유롭게 조정할 수 있다. 제2조(초과근무 관리) (1) 연장근무는 사전 승인제(팀장 승인)로 운영한다. (2) 주당 연장근무 12시간을 초과하지 않는다(근로기준법 준수). (3) 특별한 사유 없는 야근(21시 이후)이 월 3회 이상 발생하면 해당 부서장에게 경고를 발송한다. (4) 만성적 초과근무 부서에 대해 인원 보충 또는 업무 재배분을 검토한다. 제3조(퇴근 후 연락) (1) 퇴근 후, 주말, 공휴일에는 업무 연락을 자제한다. (2) 긴급 상황(시스템 장애, 안전사고 등)에 한하여 예외로 하며, 이 경우에도 핵심 담당자에게만 연락한다. (3) 메신저 예약 발송 기능을 적극 활용한다. (4) 「연결되지 않을 권리」를 존중하며, 퇴근 후 미응답에 대해 불이익을 주지 않는다. 제4조(휴가 사용 장려) (1) 연차 사용률 80% 이상을 권장하며, 미사용 시 상반기·하반기 사용 계획을 제출하도록 안내한다. (2) 리프레시 휴가: 근속 3년마다 연속 5일의 유급 리프레시 휴가를 부여한다. (3) 안식월: 근속 10년 차에 1개월 유급 안식월을 부여한다.',
    '{"tags":["워라밸","유연근무","초과근무","퇴근후연락","연결되지않을권리","리프레시","안식월"],"category":"조직문화","doc_category":"조직문화","importance":"high"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- [문서 8] 윤리서약 및 이해충돌 관리
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '윤리서약 및 이해충돌 관리 정책',
    'policy',
    'ko',
    '제1조(윤리서약) (1) 모든 임직원은 입사 시 「윤리경영 서약서」에 서명한다. (2) 서약 내용: ①행동강령 준수, ②이해충돌 발생 시 즉시 보고, ③부정행위 금지, ④비밀정보 보호, ⑤위반 시 징계 수용. (3) 매년 1월 윤리서약을 갱신하며, 미서약 시 HRIS 접근이 제한된다. (4) 관리자(팀장 이상)는 추가 서약(관리자 윤리 의무, 부하직원 윤리 감독 책임)에 서명한다. 제2조(이해충돌 신고) (1) 신고 대상: ①가족(배우자, 직계 혈족, 형제자매)이 경쟁사·거래처에 근무. ②본인 또는 가족이 거래처의 주식 5% 이상 보유. ③회사 업무와 관련된 외부 활동(강연, 자문, 겸직). ④전직 직장이 현재 거래처인 경우. (2) 신고 절차: 「이해충돌 신고서」를 윤리경영팀에 제출(연 1회 자진 신고 + 변동 시 즉시 신고). (3) 심사: 윤리경영팀이 이해충돌 여부를 심사하고, 필요 시 업무 조정(거래 배제, 담당 변경)을 권고한다. 제3조(미신고 시 제재) (1) 이해충돌 상황을 인지하고도 신고하지 않은 경우: 감봉 이상 징계. (2) 이해충돌을 이용하여 부당 이익을 취한 경우: 해고 + 법적 조치 + 이익 환수. 제4조(사후 관리) (1) 이해충돌 신고 건은 연 1회 재검토하여 상황 변화를 반영한다. (2) 퇴직 시에도 이해충돌 관련 비밀유지 의무는 2년간 지속된다.',
    '{"tags":["윤리서약","이해충돌","신고","겸직","가족관계","미신고제재"],"category":"윤리경영","doc_category":"조직문화","importance":"high"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- [문서 9] 내부 고발(공익 신고) 제도
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '내부 고발(공익 신고) 제도',
    'policy',
    'ko',
    '제1조(목적) 본 제도는 사내의 부정·비위·불법 행위를 조기에 발견하고 시정하여, 건전한 기업 경영과 사회적 책임을 이행하기 위함이다. 제2조(신고 대상) (1) 횡령, 배임, 사기 등 재무 부정. (2) 뇌물 수수, 부당 거래. (3) 법률 위반(환경법, 노동법, 공정거래법 등). (4) 안전·보건 규정 위반. (5) 개인정보 침해, 정보보안 위반. (6) 직장 내 괴롭힘·성희롱 은폐. (7) 기타 공익을 해치는 행위. 제3조(신고 방법) (1) 윤리경영팀 직접 신고(내선 5678, ethics@company.com). (2) 외부 독립 신고센터(제3자 운영, 24시간): 전화(02-XXXX-YYYY), 웹사이트(ethics.company.com). (3) 서면 신고(윤리경영팀 사서함). (4) 익명 신고 가능(신고자 보호를 위해 신원 확인을 강제하지 않음). 제4조(신고자 보호) (1) 신고자의 신원은 본인 동의 없이 공개하지 않는다. (2) 신고를 이유로 한 해고, 전보, 감봉, 평가 불이익 등 보복 행위를 엄격히 금지한다. (3) 보복 행위가 확인될 경우 해고를 포함한 중징계를 부과한다. (4) 신고자가 보복을 우려할 경우, 부서 전환 또는 재택근무 등 보호 조치를 지원한다. (5) 공익신고자보호법에 따른 보호를 적용한다. 제5조(조사 및 조치) (1) 신고 접수 후 14일 이내 예비 조사에 착수한다. (2) 조사 결과에 따라 징계, 법적 조치, 프로세스 개선 등을 시행한다. (3) 신고자에게 조사 결과를 통보한다(익명 신고의 경우 웹사이트를 통해 결과 확인 가능).',
    '{"tags":["내부고발","공익신고","신고자보호","보복금지","횡령","비위"],"category":"윤리경영","doc_category":"조직문화","importance":"high"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- [문서 10] ESG 경영 및 사회적 책임
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    'ESG 경영 및 사회적 책임 정책',
    'policy',
    'ko',
    '제1조(ESG 경영 선언) 당사는 환경(Environment), 사회(Social), 지배구조(Governance)를 핵심 경영 원칙으로 삼고, 지속 가능한 성장을 추구한다. 제2조(환경, E) (1) 탄소중립: 2030년까지 Scope 1·2 탄소배출량 50% 감축, 2050년 넷제로 달성. (2) 에너지: 사옥 전력 소비의 RE100(재생에너지 100%)를 2035년까지 달성. (3) 자원순환: 사무용품 재활용률 90% 이상, 페이퍼리스(Paperless) 오피스 추진. (4) 친환경 구매: 친환경 인증 제품 우선 구매 정책. 제3조(사회, S) (1) 인권 존중: UN 글로벌 콤팩트 10대 원칙 준수. (2) 지역사회 공헌: 매출의 1%를 사회공헌 기금으로 적립. (3) 직원 봉사활동: 연간 16시간(유급) 봉사활동 참여 권장. (4) 공급망 관리: 협력업체 ESG 평가를 연 1회 실시하고, 미달 업체에 개선 권고. 제4조(지배구조, G) (1) 이사회 다양성: 사외이사 40% 이상, 여성 이사 1인 이상. (2) 투명한 공시: ESG 보고서를 연 1회 발간하고 홈페이지에 공개. (3) 윤리경영 체계 유지: 행동강령, 내부 고발 제도, 반부패 정책 상시 운영. 제5조(임직원 참여) (1) ESG 아이디어 공모전: 반기 1회, 우수 아이디어 포상(100만원). (2) 에코 챌린지: 월별 친환경 실천 캠페인(텀블러 사용, 대중교통 이용 등). (3) ESG 교육: 연 1회 전 직원 대상(1시간).',
    '{"tags":["ESG","탄소중립","RE100","사회공헌","지배구조","SDGs","공급망"],"category":"윤리경영","doc_category":"조직문화","importance":"medium"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- [문서 11] 겸직·부업 및 영업비밀 관리
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '겸직·부업 및 영업비밀 관리 정책',
    'policy',
    'ko',
    '제1조(겸직 원칙) (1) 당사 임직원은 회사의 사전 승인 없이 타 기업·기관에 취업하거나 영리 활동에 종사할 수 없다. (2) 승인 대상: 타사 임직원 겸직, 프리랜서 활동, 개인 사업 운영, 유튜브·블로그 등 수익형 콘텐츠 활동(월 50만원 초과 수익 시). (3) 예외(승인 불요): 대학 강의(학기당 주 3시간 이내, 비경쟁 분야), 비영리 단체 봉사활동, 저작·번역 활동(경쟁사 관련 아닌 경우). 제2조(승인 절차) (1) 「겸직 승인 신청서」를 인사팀에 제출. (2) 심사 기준: ①본업에 지장 여부, ②경쟁사 관련 여부, ③이해충돌 여부, ④회사 자산·정보 이용 여부. (3) 인사팀 → 부서장 → 인사담당 임원 승인. (4) 승인 기간: 최대 1년, 갱신 시 재신청. 제3조(영업비밀 보호) (1) "영업비밀"이란 공연히 알려져 있지 않고, 독립된 경제적 가치를 가지며, 비밀로 관리되는 기술·경영 정보를 말한다. (2) 모든 임직원은 재직 중은 물론 퇴직 후 2년간 영업비밀을 누설·사용할 수 없다. (3) 영업비밀 자료에는 「Confidential」 등급 표시를 하며, 반출·복사·전송 시 부서장 승인이 필요하다. (4) 위반 시: 해고 + 민·형사 법적 조치(부정경쟁방지법). 제4조(경업 금지) (1) 퇴직 후 1년간 경쟁사(동종 업종)에 취업하거나 동종 사업을 영위할 수 없다(별도 경업 금지 약정 체결 시). (2) 경업 금지 기간 중 월 기본급의 50%를 보상금으로 지급한다.',
    '{"tags":["겸직","부업","영업비밀","경업금지","승인절차","비밀유지"],"category":"윤리경영","doc_category":"조직문화","importance":"high"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- [문서 12] 사회공헌 및 봉사활동 (멀티청크 2개)
DO $$
DECLARE parent_id BIGINT;
BEGIN
    INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
    VALUES (
        1,
        '사회공헌 및 봉사활동 정책',
        'policy',
        'ko',
        '제1조(목적) 당사는 기업시민으로서 사회적 책임을 이행하고, 임직원의 자발적 사회공헌 활동을 장려하여 더 나은 사회 구현에 기여한다. 제2조(사회공헌 체계) (1) 사회공헌위원회: 경영지원본부장 주관, 분기 1회 개최. 위원: 각 본부 대표 1인, 윤리경영팀, 홍보팀. (2) 중점 분야: ①교육(장학금, 멘토링), ②환경(탄소중립, 자원순환), ③지역사회(소외계층 지원, 재난 구호). (3) 연간 사회공헌 기금: 매출의 1%(전년 매출 기준, 최소 1억원). 제3조(봉사활동) (1) 유급 봉사시간: 연간 16시간(2일)까지 유급 처리. (2) 활동 범위: 임직원이 자유롭게 선택하되, 사내 추천 프로그램을 우선 안내한다. ①정기 봉사: 매월 셋째 토요일 지역아동센터 학습 멘토링. ②환경 봉사: 분기 1회 한강/산 정화 활동. ③재능 기부: IT 교육(코딩, 엑셀), 법률 상담, 세무 상담. ④헌혈: 연 2회 사내 헌혈 캠페인(참여 시 봉사시간 4시간 인정). (3) 봉사 시간 기록: 사내 인트라넷 「사회공헌」 메뉴에 직접 등록(증빙 첨부). (4) 우수 봉사자 포상: 연말 시상(개인상, 팀상, CEO 특별상).',
        '{"tags":["사회공헌","봉사활동","장학금","멘토링","유급봉사","헌혈"],"category":"조직문화","doc_category":"조직문화","importance":"medium"}',
        NULL, 'text-embedding-3-small', false, 0, 2, NULL, 'sql_import', 'rag_knowledge',
        NULL
    ) RETURNING id INTO parent_id;

    INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
    VALUES (
        1,
        '사회공헌 및 봉사활동 정책',
        'policy',
        'ko',
        '제4조(매칭 기부) (1) 임직원 개인 기부 시 회사가 동일 금액을 매칭 기부한다(1:1 매칭, 연 100만원 한도). (2) 재난 구호 시 긴급 매칭 기부를 실시하며, 이 경우 한도를 초과할 수 있다(경영진 승인). (3) 매칭 기부 신청: 사내 인트라넷 → 기부 증빙 업로드 → 사회공헌위원회 확인 → 매칭 기부 실행. 제5조(장학 사업) (1) OO장학재단: 매년 대학생 20명에게 등록금 전액 장학금 지급. (2) 선발 기준: 소득 8분위 이하, 학업 성적 B+ 이상, 사회공헌 활동 실적. (3) 장학생 멘토링: 임직원 자원 봉사자가 장학생 1인당 1인의 멘토 역할 수행(월 1회 면담). 제6조(프로보노) (1) 전문 인력(IT, 법률, 회계, HR)의 재능 기부를 활성화한다. (2) 프로보노 활동 시 봉사시간으로 인정하며, 업무 시간 중 활동 시 팀장 승인을 받는다. (3) 비영리 단체, 사회적 기업, 소상공인 등을 대상으로 한다. 제7조(성과 보고) (1) 연 1회 사회공헌 성과 보고서를 발간한다(ESG 보고서에 통합 가능). (2) 보고 내용: 기부 총액, 봉사 참여율, 수혜 인원, 환경 성과(탄소 감축량 등).',
        '{"tags":["매칭기부","장학사업","프로보노","재능기부","성과보고","ESG보고서"],"category":"조직문화","doc_category":"조직문화","importance":"medium"}',
        NULL, 'text-embedding-3-small', false, 1, 2, parent_id, 'sql_import', 'rag_knowledge', NULL
    );
END $$;

-- [문서 13] 혁신문화 및 제안 제도
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '혁신문화 및 제안 제도',
    'policy',
    'ko',
    '제1조(혁신 지향) 당사는 현재에 안주하지 않고 지속적으로 혁신하는 문화를 추구한다. 모든 임직원은 업무 프로세스, 제품, 서비스의 개선 아이디어를 자유롭게 제안할 수 있다. 제2조(제안 제도) (1) 누구나 제안: 직급, 부서, 근속에 관계없이 모든 임직원이 제안할 수 있다. (2) 제안 방법: 사내 인트라넷 「혁신 제안」 게시판에 제안서(제목, 현황, 개선안, 기대효과) 작성. (3) 심사: 월 1회 혁신위원회(각 본부장)에서 심사. (4) 포상: ①채택 제안: 10만원 상품권. ②우수 제안(연 12건): 50만원. ③최우수 제안(연 3건): 100만원 + 승진 심사 가점. ④제안이 실제 적용되어 비용 절감·매출 증대 효과가 검증된 경우: 효과 금액의 5%(최대 500만원) 인센티브. 제3조(혁신 프로그램) (1) 해커톤: 반기 1회, 2일간 부서 혼합 팀으로 신규 아이디어 프로토타이핑. (2) 20% 타임: R&D 부서는 업무 시간의 20%를 자유 프로젝트에 투입할 수 있다. (3) 이노베이션 랩: 사내 별도 공간에서 신기술(AI, IoT, 블록체인 등) PoC(Proof of Concept)를 진행한다. (4) 실패 공유회: 분기 1회 "실패에서 배우기" 세션을 개최하여 도전의 가치를 공유한다. 제4조(성과 관리) 혁신 제안 및 참여 실적을 성과평가에 반영한다(역량 평가 항목 "혁신" 10% 배점).',
    '{"tags":["혁신문화","제안제도","해커톤","20%타임","이노베이션랩","실패공유회"],"category":"조직문화","doc_category":"조직문화","importance":"medium"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- [문서 14] 세대 간 협업 및 역멘토링
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '세대 간 협업 및 역멘토링 가이드',
    'guide',
    'ko',
    '제1조(배경) 당사는 20대부터 60대까지 다양한 세대의 임직원이 함께 근무하고 있다. 각 세대의 강점을 활용하고 세대 간 이해를 증진하여 시너지를 창출하는 것이 중요하다. 제2조(세대별 특성 이해) (1) 베이비부머(1955~1964): 조직 충성도 높음, 경험과 네트워크 풍부, 대면 소통 선호. (2) X세대(1965~1980): 독립적, 효율 중시, 워라밸 선구자, 현실적. (3) 밀레니얼(1981~1996): 의미 추구, 성장 욕구, 수평적 소통 선호, 디지털 네이티브. (4) Z세대(1997~): 디지털 최적화, 개인주의, 공정성 민감, 짧은 콘텐츠 선호, 부업·사이드 프로젝트 관심. 제3조(역멘토링 프로그램) (1) 목적: 주니어(5년 미만)가 시니어(15년 이상)에게 디지털 기술, 트렌드, 소셜미디어 등을 멘토링한다. (2) 매칭: 반기 1회 자발적 신청 기반, 타 부서 간 매칭 우선. (3) 활동: 월 1~2회 1시간 세션(비대면 가능). 주제: AI 활용, 협업 도구(Notion, Slack), SNS 트렌드, 디지털 마케팅 등. (4) 시니어 멘티 혜택: 디지털 역량 향상, 젊은 세대 이해. 주니어 멘토 혜택: 리더십 경험, 비즈니스 인사이트 습득, 성과평가 가점(역량 "협업" 항목). 제4조(세대 공감 워크숍) 연 1회 "세대 대화" 워크숍을 개최하여 세대별 업무 스타일, 소통 선호도를 공유하고 상호 이해를 증진한다. 제5조(갈등 중재) 세대 간 갈등 발생 시 HR BP(비즈니스 파트너)가 중재하며, 구조적 문제는 조직문화팀에서 개선안을 마련한다.',
    '{"tags":["세대간협업","역멘토링","밀레니얼","Z세대","디지털역량","세대공감"],"category":"조직문화","doc_category":"조직문화","importance":"medium"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- [문서 15] 글로벌 문화 다양성 가이드
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '글로벌 문화 다양성 가이드',
    'guide',
    'ko',
    '제1조(적용 대상) 해외 법인 직원, 국내 근무 외국인 직원, 해외 파견 직원, 글로벌 프로젝트 참여자 등 다문화 환경에서 근무하는 모든 임직원에게 적용된다. 제2조(문화적 감수성) (1) 국적, 인종, 종교, 문화에 대한 비하·조롱·편견적 발언을 하지 않는다. (2) 외국인 직원에게 한국 문화를 강요하지 않으며, 문화적 차이를 존중한다. (3) 종교적 실천(예: 기도 시간, 식이 제한)에 대한 합리적 배려를 제공한다. 제3조(언어) (1) 글로벌 미팅(외국인 참석): 공용어(영어) 사용을 원칙으로 하며, 한국어 사용 시 통역을 제공한다. (2) 외국인 직원 지원: 한국어 교육 지원(연 200만원), 업무 문서 영어 병기. (3) 외국인 직원 안내 자료(사내 규정, 복리후생, 비상 연락망)를 영어로 제공한다. 제4조(해외 파견) (1) 파견 전 현지 문화 교육(3시간 이상)을 실시한다: 비즈니스 에티켓, 법적 유의사항, 생활 정보. (2) 파견 기간 중 현지 문화 적응을 지원하며, 분기 1회 HR과 면담한다. (3) 귀임 후 리인테그레이션 프로그램(2주)을 운영한다. 제5조(종교·명절 존중) (1) 외국인 직원의 본국 주요 명절에 대해 연차 사용을 우선 배려한다. (2) 사내 식당에서 할랄, 비건 등 다양한 식이 옵션을 제공하도록 노력한다. (3) 사내 종교 활동 공간(다목적 명상실)을 제공한다.',
    '{"tags":["글로벌문화","다양성","외국인직원","해외파견","문화감수성","언어지원"],"category":"조직문화","doc_category":"조직문화","importance":"medium"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- [문서 16] 음주·회식 문화 가이드라인
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '음주·회식 문화 가이드라인',
    'guide',
    'ko',
    '제1조(회식 원칙) (1) 회식은 팀워크 강화와 소통을 위한 자율적 활동이며, 참석을 강요하지 않는다. (2) 불참에 대해 어떠한 불이익도 주지 않으며, 불참 사유를 묻지 않는다. (3) 회식은 업무 시간 내(17~20시) 또는 점심시간을 활용하는 것을 권장한다. (4) 회식은 월 1회 이내, 2시간 이내를 권장하며, 2차를 강요하지 않는다. 제2조(음주 관련) (1) 음주를 강요하지 않으며, "한 잔만"이라도 강권하지 않는다. (2) 비음주자(건강, 종교, 개인 신념 등)의 선택을 존중하며, 비음주 음료를 반드시 준비한다. (3) 러브샷, 건배사 강요, 원샷 강요 등 구시대적 음주 문화를 금지한다. (4) 음주 후 업무 연락, 음주 후 비상 호출은 엄격히 금지한다(안전 사고 방지). 제3조(회식비 지원) (1) 팀 회식비: 분기 1회, 1인당 5만원 지원(세금 포함). (2) 점심 회식: 별도 예산(1인당 2만원) 지원하며, 저녁 회식 대신 점심 회식을 장려한다. (3) 비알코올 활동(볼링, 영화, 보드게임 등)도 회식비 사용 가능하다. 제4조(위반 시 조치) (1) 음주·참석 강요: 직장 내 괴롭힘에 해당할 수 있으며, 신고 시 조사·징계. (2) 회식 중 성희롱: 직장 내 성희롱 처리 절차 적용. (3) 음주 후 음주운전: 즉시 해고 사유(무관용 원칙).',
    '{"tags":["회식문화","음주강요금지","2차금지","비알코올활동","점심회식","음주운전"],"category":"조직문화","doc_category":"조직문화","importance":"medium"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- [문서 17] 갈등 해결 및 고충 처리
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '갈등 해결 및 고충 처리 절차',
    'procedure',
    'ko',
    '제1조(고충 처리 위원) (1) 남녀고용평등법에 따라 고충 처리 위원을 지정한다(인사팀장, 임기 2년). (2) 고충 처리 위원은 직원의 고충을 접수하고 10일 이내 처리 결과를 통보한다. (3) 고충 유형: ①인사·급여 관련, ②직장 내 괴롭힘·성희롱, ③부서 간 업무 갈등, ④상사·동료 관계 갈등, ⑤복리후생·근무환경 불만. 제2조(갈등 해결 절차) (1) 1단계(자율 해결): 당사자 간 직접 대화를 통해 해결을 시도한다. SBI(Situation-Behavior-Impact) 모델을 활용하여 구체적으로 소통한다. (2) 2단계(팀장 중재): 자율 해결이 어려운 경우, 팀장이 양 당사자의 이야기를 듣고 중재한다. (3) 3단계(HR 중재): 팀장 중재로 해결되지 않은 경우, HR BP(비즈니스 파트너)가 개입하여 전문적으로 중재한다. (4) 4단계(고충 처리 위원): HR 중재로도 해결되지 않는 경우, 고충 처리 위원회(고충 처리 위원 + 노사 협의회 위원)에서 심의·의결한다. (5) 5단계(외부 기관): 사내 해결이 불가한 경우, 노동위원회 등 외부 기관에 의뢰할 수 있다. 제3조(비밀 보장) 고충 상담 내용은 비밀이 보장되며, 관련자 외 공유하지 않는다. 제4조(EAP 연계) 심리적 갈등, 스트레스, 번아웃 등의 경우 EAP(Employee Assistance Program) 전문 상담을 연계한다(연 8회 무료, 가족 포함).',
    '{"tags":["갈등해결","고충처리","SBI모델","HR중재","고충처리위원","EAP"],"category":"조직문화","doc_category":"조직문화","importance":"medium"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- [문서 18] 리더십 행동 기준 (멀티청크 2개)
DO $$
DECLARE parent_id BIGINT;
BEGIN
    INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
    VALUES (
        1,
        '리더십 행동 기준',
        'regulation',
        'ko',
        '제1조(적용 대상) 본 기준은 팀장, 실장, 본부장, 임원 등 1인 이상의 부하직원을 관리·감독하는 모든 리더에게 적용된다. 제2조(리더의 책무) (1) 방향 제시: 팀의 비전과 목표를 명확히 설정하고 공유한다. (2) 코칭: 부하직원의 성장을 적극 지원하며, 정기적(월 1회 이상) 1:1 면담을 실시한다. (3) 권한 위임: 업무에 필요한 권한을 위임하고, 마이크로매니지먼트를 지양한다. (4) 공정한 평가: 객관적 기준에 의한 공정한 평가를 실시하며, 근거를 투명하게 공유한다. (5) 솔선수범: 핵심가치와 행동강령을 스스로 실천하며, 팀원에게 모범이 된다. (6) 심리적 안전감: 팀원이 실수를 두려워하지 않고 의견을 자유롭게 개진할 수 있는 환경을 만든다. 제3조(금지 행위) (1) 인격 모독, 폭언, 비하. (2) 사적 심부름, 개인 용무 지시. (3) 회식·음주·야근 강요. (4) 승진·평가를 이용한 부당 요구. (5) 보고 누락·지연에 대한 과도한 질책(건설적 피드백으로 전환). (6) 특정 팀원 편애 또는 차별. (7) 팀원의 아이디어를 자신의 것으로 발표.',
        '{"tags":["리더십","행동기준","코칭","권한위임","심리적안전감","금지행위"],"category":"조직문화","doc_category":"조직문화","importance":"high"}',
        NULL, 'text-embedding-3-small', false, 0, 2, NULL, 'sql_import', 'rag_knowledge',
        NULL
    ) RETURNING id INTO parent_id;

    INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
    VALUES (
        1,
        '리더십 행동 기준',
        'regulation',
        'ko',
        '제4조(리더 평가) (1) 리더십 다면평가: 연 1회 부하직원, 동료, 상위 리더가 참여하는 360도 리더십 평가를 실시한다. (2) 평가 항목: ①소통·경청, ②코칭·육성, ③공정성, ④전략적 사고, ⑤변화 관리, ⑥조직문화 실천. (3) 평가 결과: 리더에게 개인별 피드백 리포트를 제공하며, 약점 영역에 대해 리더십 코칭을 연계한다. (4) 리더십 평가 결과가 하위 10%에 해당하는 경우, 6개월간 집중 리더십 코칭 프로그램에 참여하며, 개선되지 않을 경우 보직 변경을 검토한다. 제5조(리더십 개발) (1) 신임 팀장 교육: 승진 후 3개월 이내 "New Leader Program"(24시간, 3일 과정) 이수 필수. (2) 중간 관리자 교육: 연 1회 리더십 역량 강화 교육(16시간). (3) 임원 교육: 연 1회 경영 리더십 세미나(8시간). (4) 코칭 스킬: 모든 리더는 3년 내 코칭 기본 과정(8시간)을 이수한다. (5) 리더 간 학습: 분기 1회 "리더 커뮤니티 오브 프랙티스(CoP)"를 운영하여 리더십 사례를 공유한다. 제6조(보직 해임 사유) (1) 리더십 평가 2년 연속 하위 10%. (2) 직장 내 괴롭힘·성희롱 가해 확인. (3) 부서 이직률이 전사 평균의 2배 이상 지속(2분기 연속). (4) 윤리 위반(행동강령 중대 위반).',
        '{"tags":["리더평가","360도평가","리더십개발","신임팀장","코칭스킬","보직해임"],"category":"조직문화","doc_category":"조직문화","importance":"high"}',
        NULL, 'text-embedding-3-small', false, 1, 2, parent_id, 'sql_import', 'rag_knowledge', NULL
    );
END $$;

-- [문서 19] 조직문화/윤리경영 FAQ
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '조직문화 및 윤리경영 FAQ',
    'faq',
    'ko',
    'Q1: 직장 내 괴롭힘을 당하고 있는데 어디에 신고하나요? A1: 윤리경영팀(내선 5678, ethics@company.com), 외부 신고센터(02-XXXX-YYYY), 또는 사내 인트라넷 익명 신고 게시판으로 신고할 수 있습니다. 실명·익명 모두 가능하며, 신고 즉시 피해자 보호 조치가 이루어집니다. Q2: 거래처에서 선물을 받았는데 어떻게 해야 하나요? A2: 5만원 이하의 선물은 수수 가능하나, 5만원 초과 시 3일 이내 윤리경영팀에 신고해야 합니다. 현금·상품권은 금액과 무관하게 수수 금지입니다. 부득이하게 받은 경우 즉시 반환하거나 윤리경영팀에 제출해 주세요. Q3: 부업(유튜브 수익)을 하고 싶은데 가능한가요? A3: 월 50만원 이하 수익이면 별도 승인 없이 가능합니다. 50만원 초과 시 「겸직 승인 신청서」를 인사팀에 제출하여 승인받아야 합니다. 단, 경쟁사 관련 콘텐츠나 회사 정보를 활용한 콘텐츠는 불가합니다. Q4: 회식에 불참해도 불이익이 없나요? A4: 네, 회식 참석은 완전히 자율적이며, 불참에 대한 어떠한 불이익도 금지됩니다. 불참 사유를 묻는 것도 부적절합니다. Q5: 퇴근 후에도 상사가 계속 카톡으로 업무 지시를 합니다. A5: 「연결되지 않을 권리」에 따라 퇴근 후 업무 연락은 긴급 상황(시스템 장애, 안전사고)에 한하여 허용됩니다. 지속적인 퇴근 후 업무 지시는 직장 내 괴롭힘에 해당할 수 있으므로, 팀장에게 건의하거나 HR에 상담해 주세요. Q6: 내부 고발(공익 신고) 시 보복을 당하지 않을까 걱정됩니다. A6: 신고자 보호는 법적으로 보장(공익신고자보호법)되며, 회사 내부 정책으로도 신원 비공개, 보복 금지, 보호 조치(부서 전환 등)를 보장합니다. 보복 행위 확인 시 가해자에게 중징계가 부과됩니다.',
    '{"tags":["FAQ","괴롭힘신고","선물접대","겸직부업","회식불참","퇴근후연락","내부고발"],"category":"조직문화","doc_category":"조직문화","importance":"medium"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- [문서 20] 소셜미디어 사용 가이드라인
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '소셜미디어 사용 가이드라인',
    'guide',
    'ko',
    '제1조(적용 범위) 본 가이드라인은 임직원이 개인 자격으로 소셜미디어(Facebook, Instagram, X(Twitter), LinkedIn, YouTube, TikTok, 블로그, 온라인 커뮤니티 등)를 사용할 때 적용된다. 제2조(기본 원칙) (1) 개인 의견임을 명시: 회사에 대한 의견을 게시할 때 "개인적인 견해이며, 회사를 대표하지 않는다"는 점을 밝힌다. (2) 비밀 정보 금지: 미공개 경영 정보, 재무 정보, 고객 정보, 제품 개발 정보를 게시하지 않는다. (3) 존중: 동료, 고객, 경쟁사, 파트너에 대한 비방·명예훼손·차별적 발언을 하지 않는다. (4) 저작권 준수: 회사의 로고, 상표, 저작물을 무단 사용하지 않는다. 제3조(회사 공식 계정) (1) 회사 공식 소셜미디어 계정은 홍보팀에서만 운영한다. (2) 임직원이 회사를 대표하여 외부 소통(인터뷰, 기고, 강연, SNS 공식 발언)을 하려면 홍보팀의 사전 승인을 받는다. 제4조(금지 사항) (1) 사내 회의, 문서, 이메일 내용의 스크린샷 게시. (2) 사업장 내부(서버실, 생산동 등 보안 구역) 촬영 및 게시. (3) 동료의 동의 없이 사진·영상을 게시하는 행위. (4) 회사의 주가에 영향을 줄 수 있는 미공개 정보 게시(내부자거래 위반 가능). 제5조(모니터링) (1) 회사는 공개된 소셜미디어에서 회사 관련 게시물을 모니터링할 수 있다. (2) 위반 사항 발견 시 게시물 삭제를 요청하며, 중대 위반 시 징계 조치한다. 제6조(위기 대응) 소셜미디어에서 회사 관련 위기(부정적 바이럴, 허위 정보 등) 발생 시, 개인적으로 대응하지 않고 홍보팀에 즉시 알린다.',
    '{"tags":["소셜미디어","SNS","가이드라인","비밀정보","공식계정","모니터링"],"category":"조직문화","doc_category":"조직문화","importance":"medium"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- original_content = content 동기화 (INSERT 후 실행)
UPDATE tb_docs SET original_content = content
WHERE source_type = 'sql_import' AND usage_type = 'rag_knowledge' AND original_content IS NULL;
