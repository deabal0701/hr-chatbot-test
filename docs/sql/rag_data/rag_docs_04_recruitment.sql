-- ============================================================
-- RAG 문서 데이터 - Part 04: 채용/온보딩/인턴십 제도
-- 총 문서 수: 20개 (논리적 문서), 멀티청크 포함 총 28행
-- 생성일: 2026-02-27
-- 용도: RAG 검색 테스트 (RAGAS 평가용)
-- ============================================================

-- [문서 1] 채용 프로세스 전체 흐름 (멀티청크 3개)
DO $$
DECLARE parent_id BIGINT;
BEGIN
    INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
    VALUES (
        1,
        '채용 프로세스 전체 흐름',
        'policy',
        'ko',
        '제1조(채용 절차 개요) 당사의 채용 프로세스는 7단계로 구성된다: ①채용 요청 → ②공고 게시 → ③서류 전형 → ④필기시험(해당 직군) → ⑤1차 면접(실무) → ⑥2차 면접(임원) → ⑦최종 합격·처우 협의·입사. 제2조(채용 요청) (1) 부서장이 인력 소요 계획서를 작성하여 인사팀에 제출한다. (2) 소요 계획서 포함 사항: 모집 직무, 인원, 자격 요건, 우대 사항, 희망 입사일, 예산. (3) 인사팀은 인력 계획 대비 적정성을 검토하고, 채용위원회(인사담당임원, 해당 부서장, 인사팀장) 승인을 득한다. 제3조(공고 게시) (1) 채용 공고는 자사 채용 사이트, 잡포털(사람인, 잡코리아, 원티드), LinkedIn에 동시 게시한다. (2) 공고 기간: 최소 14일(긴급 채용 시 7일). (3) 공고 내용: 회사 소개, 직무 설명, 자격 요건, 우대 사항, 근무 조건, 전형 절차, 접수 기간.',
        '{"tags":["채용","프로세스","전형","면접","서류","공고"],"category":"채용관리","doc_category":"채용","importance":"critical"}',
        NULL, 'text-embedding-3-small', false, 0, 3, NULL, 'sql_import', 'rag_knowledge',
        NULL
    ) RETURNING id INTO parent_id;

    INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
    VALUES (
        1,
        '채용 프로세스 전체 흐름',
        'policy',
        'ko',
        '제4조(서류 전형) (1) 지원서, 이력서, 자기소개서를 기반으로 평가한다. (2) 평가 항목: 직무 적합성(40%), 경력·학력(30%), 자기소개서 내용(20%), 기타 우대(10%). (3) 서류 전형 결과는 접수 마감 후 7영업일 이내에 이메일로 통보한다. 제5조(필기시험) (1) 기술직: 직무 지식 테스트(코딩 테스트 포함). (2) 사무직: 인·적성 검사(NCS 기반). (3) 온라인 프록터링 방식 허용, 부정행위 적발 시 영구 지원 불가. 제6조(1차 면접 - 실무 면접) (1) 면접관: 해당 팀장 + 실무자 1~2인. (2) 면접 시간: 40~60분. (3) 평가 항목: 직무 역량(40%), 문제 해결 능력(30%), 조직 적합성(20%), 커뮤니케이션(10%). (4) 기술직은 과제 발표(기술 PT) 또는 라이브 코딩을 추가 실시한다.',
        '{"tags":["서류전형","필기시험","1차면접","실무면접","코딩테스트","NCS"],"category":"채용관리","doc_category":"채용","importance":"critical"}',
        NULL, 'text-embedding-3-small', false, 1, 3, parent_id, 'sql_import', 'rag_knowledge', NULL
    );

    INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
    VALUES (
        1,
        '채용 프로세스 전체 흐름',
        'policy',
        'ko',
        '제7조(2차 면접 - 임원 면접) (1) 면접관: 담당 임원 + 인사담당 임원. (2) 면접 시간: 30~40분. (3) 평가 항목: 리더십 잠재력(30%), 조직 비전 공유(30%), 성장 가능성(20%), 인성(20%). (4) 과장급 이상 경력 채용은 대표이사가 최종 면접에 참여한다. 제8조(처우 협의) (1) 최종 합격자에게 연봉, 직급, 입사일을 포함한 오퍼 레터를 발송한다. (2) 경력직 연봉: 전 직장 급여 증빙(원천징수영수증) + 내부 페이밴드 기준으로 산정. (3) 오퍼 수락 기한: 발송 후 7일 이내. (4) 연봉 협상 범위: 제안 대비 ±10% 이내. 제9조(채용 소요 기간) (1) 표준 소요 기간: 공고 게시~입사까지 약 6~8주. (2) 긴급 채용: 3~4주(서류+면접 병행). (3) 임원 채용: 8~12주(헤드헌터 연계 포함). 제10조(합격 취소) 허위 서류 제출, 건강검진 부적합, 범죄 경력 확인 시 합격을 취소할 수 있다.',
        '{"tags":["임원면접","처우협의","오퍼레터","연봉협상","합격취소","채용기간"],"category":"채용관리","doc_category":"채용","importance":"critical"}',
        NULL, 'text-embedding-3-small', false, 2, 3, parent_id, 'sql_import', 'rag_knowledge', NULL
    );
END $$;

-- [문서 2] 직무기술서(JD) 작성 기준
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '직무기술서(JD) 작성 기준',
    'manual',
    'ko',
    '제1조(목적) 직무기술서(Job Description)는 채용 공고, 성과 평가, 직무 분석의 기초 문서로서 정확하고 일관되게 작성되어야 한다. 제2조(필수 포함 항목) (1) 직무명(Job Title): 사내 직무 분류체계에 부합하는 공식 명칭. (2) 소속 부서/팀. (3) 보고 라인: 직속 상사, 협업 부서. (4) 직무 요약: 2~3문장의 핵심 역할 설명. (5) 주요 업무(Key Responsibilities): 5~8개 항목, 각 항목에 비중(%) 표기. (6) 자격 요건(Requirements): 학력, 경력 연수, 필수 기술/자격증, 어학. (7) 우대 사항(Preferred): 추가 역량, 관련 경험, 산업 지식. (8) 역량 요구 수준: 직무 등급(J1~J7) 및 핵심 역량 기대 수준. (9) 근무 조건: 근무지, 근무 시간, 출장 빈도. 제3조(작성 원칙) (1) 성별, 연령, 출신 학교 등 차별 요소를 포함하지 않는다. (2) 실제 수행 업무를 기반으로 작성하며, 과장하거나 축소하지 않는다. (3) 연 1회 직무 분석을 통해 최신화하며, 부서장이 검토·승인한다.',
    '{"tags":["JD","직무기술서","채용공고","자격요건","주요업무","직무분석"],"category":"채용관리","doc_category":"채용","importance":"high"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- [문서 3] 서류 전형 평가 기준
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '서류 전형 평가 기준',
    'policy',
    'ko',
    '제1조(평가 항목 및 가중치) (1) 직무 적합성(40%): 지원 직무와 경력·기술의 매칭도. (2) 경력·학력(30%): 관련 경력 연수, 학력 수준, 전공 일치도. (3) 자기소개서(20%): 지원 동기의 진정성, 역량 근거 사례, 문장 구성력. (4) 우대 사항(10%): 관련 자격증, 포트폴리오, 수상 경력, 사회공헌 활동. 제2조(평가 방법) (1) 2인 이상의 평가자가 독립적으로 채점하며, 평균 점수를 산출한다. (2) 평가 척도: 1~5점(1: 매우 미흡, 5: 매우 우수). (3) 합격 기준: 평균 3.0점 이상이며, 모집 인원의 3~5배수를 서류 합격으로 선정한다. 제3조(블라인드 채용) (1) 이력서에서 사진, 출신 학교명, 가족 관계를 삭제하고 평가한다. (2) 평가자에게 지원자의 성별, 연령이 노출되지 않도록 시스템에서 블라인드 처리한다. 제4조(서류 보관) (1) 합격자: 입사일로부터 3년 보관. (2) 불합격자: 접수 마감일로부터 180일 보관 후 파기(개인정보보호법 준수). (3) 지원자가 반환을 요청하면 14일 이내에 반환한다.',
    '{"tags":["서류전형","블라인드채용","평가기준","자기소개서","서류보관","채점"],"category":"채용관리","doc_category":"채용","importance":"high"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- [문서 4] 필기시험 운영 방법
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '필기시험 운영 방법',
    'manual',
    'ko',
    '제1조(시험 종류) (1) 직무적성검사(NCS 기반): 사무직, 영업직 대상. 의사소통, 수리논리, 문제해결, 자원관리 영역. (2) 직무 지식 테스트: 기술직 대상. 해당 직무 전문 지식(SW개발, 네트워크, 보안 등). (3) 코딩 테스트: 개발직 대상. 알고리즘, 자료구조, 실무 코딩(Python/Java/JavaScript). (4) 외국어 시험: 해외 사업 관련 직군. 비즈니스 영어 독해·작문. 제2조(시행 방식) (1) 온라인: 자택 응시(프록터링 솔루션 활용, 웹캠·화면 공유 필수). (2) 오프라인: 본사 교육장(대규모 공채 시). (3) 시험 시간: 직무적성 90분, 직무지식 60분, 코딩테스트 120분. 제3조(합격 기준) (1) 직무적성: 영역별 40% 이상, 종합 60% 이상. (2) 코딩테스트: 출제 문제(3~4개) 중 2개 이상 통과. (3) 상위 N배수(면접 인원 기준)를 합격으로 선정. 제4조(부정행위) (1) 대리 응시, 자료 참조, 타인 도움 등 부정행위 적발 시 즉시 실격 + 향후 3년간 지원 불가. (2) 온라인 프록터링에서 이상 행동이 감지된 경우 AI 분석 + 인사팀 수동 확인 후 판정.',
    '{"tags":["필기시험","NCS","코딩테스트","프록터링","부정행위","직무적성"],"category":"채용관리","doc_category":"채용","importance":"medium"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- [문서 5] 면접 운영 가이드 (멀티청크 2개)
DO $$
DECLARE parent_id BIGINT;
BEGIN
    INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
    VALUES (
        1,
        '면접 운영 가이드',
        'guide',
        'ko',
        '제1조(면접관 자격) (1) 면접관은 해당 직무에 3년 이상 경험을 보유한 과장급 이상 직원으로 한다. (2) 면접관 교육(연 1회, 4시간)을 이수하여야 면접에 참여할 수 있다. (3) 면접관 교육 내용: 구조화 면접 기법, 평가 기준 이해, 질문 금지 사항, 무의식적 편향 인식. 제2조(질문 금지 사항) (1) 혼인 여부, 자녀 계획, 임신 여부. (2) 종교, 정치적 성향, 노조 가입 여부. (3) 키·몸무게 등 신체 조건(직무 관련 예외 시 사전 승인). (4) 출신 지역, 가족 구성원의 직업. (5) 성적 지향, 장애 유무(합리적 편의 제공 목적 외). 제3조(구조화 면접) (1) 모든 지원자에게 동일한 핵심 질문을 사용한다(질문 풀에서 선정). (2) 질문 유형: 경험 기반(STAR 기법), 상황 기반, 직무 지식, 가치관. (3) 핵심 질문 3~5개 + 후속 질문(Follow-up)으로 구성.',
        '{"tags":["면접","면접관","구조화면접","질문금지","STAR","편향"],"category":"채용관리","doc_category":"채용","importance":"high"}',
        NULL, 'text-embedding-3-small', false, 0, 2, NULL, 'sql_import', 'rag_knowledge',
        NULL
    ) RETURNING id INTO parent_id;

    INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
    VALUES (
        1,
        '면접 운영 가이드',
        'guide',
        'ko',
        '제4조(평가 기준 통일) (1) 면접 전 평가표를 배포하며, 항목별 5점 척도로 채점한다. (2) 면접 종료 직후(10분 이내) 개별 채점을 완료한 후 합의 회의를 진행한다. (3) 면접관 간 점수 차이가 2점 이상인 항목은 토론을 통해 조정한다. 제5조(면접 환경) (1) 면접실은 외부 소음이 차단된 독립 공간을 사용한다. (2) 화상 면접 시: 안정적 인터넷 환경, 카메라·마이크 사전 테스트, 녹화 동의. (3) 장애인 지원자: 수어 통역, 보조 기기 사용 등 합리적 편의를 제공한다. 제6조(면접 결과 통보) (1) 합격: 면접 후 5영업일 이내 유선 통보 → 이메일 오퍼 레터 발송. (2) 불합격: 면접 후 7영업일 이내 이메일 통보(불합격 사유 미공개 원칙, 요청 시 개괄적 피드백 제공). 제7조(면접 기록 보관) 면접 평가표, 메모, 녹화 자료는 채용 완료일로부터 1년간 보관 후 파기한다.',
        '{"tags":["면접평가","화상면접","장애인편의","결과통보","면접기록","채점"],"category":"채용관리","doc_category":"채용","importance":"high"}',
        NULL, 'text-embedding-3-small', false, 1, 2, parent_id, 'sql_import', 'rag_knowledge', NULL
    );
END $$;

-- [문서 6] 경력 채용 기준
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '경력 채용 기준',
    'policy',
    'ko',
    '제1조(경력 인정) (1) 지원 직무와 동일/유사 직무 경력은 100% 인정한다. (2) 관련 업종 내 유사 직무: 80% 인정. (3) 비관련 업종 또는 비유사 직무: 50% 인정. (4) 프리랜서/창업 경력: 계약서·매출 증빙으로 확인 후 50~80% 인정(인사위원회 심의). 제2조(호봉 산정) (1) 인정 경력 연수에 따라 내부 페이밴드(Pay Band) 내에서 연봉을 결정한다. (2) 전 직장 급여 대비 최대 15% 인상 범위 내에서 조정한다. (3) 특수 직무(AI, 보안, 반도체 등) 전문 인력은 시장 프리미엄을 추가 반영할 수 있다. 제3조(검증 절차) (1) 경력증명서: 전 직장에서 발급받아 제출(필수). (2) 원천징수영수증: 전년도 급여 검증. (3) 레퍼런스 체크: 전 직장 상사 또는 동료 2인에게 업무 수행 능력, 태도, 퇴사 사유를 확인(지원자 사전 동의 필수). (4) 학력 검증: 졸업증명서 원본 또는 학력인증서. 제4조(수습 기간) 경력 채용자도 3개월 수습 기간을 적용하되, 5년 이상 경력자는 수습 면제를 부서장이 요청할 수 있다.',
    '{"tags":["경력채용","경력인정","호봉","레퍼런스체크","급여","수습","페이밴드"],"category":"채용관리","doc_category":"채용","importance":"high"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- [문서 7] 인턴십 프로그램 운영 (멀티청크 2개)
DO $$
DECLARE parent_id BIGINT;
BEGIN
    INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
    VALUES (
        1,
        '인턴십 프로그램 운영',
        'policy',
        'ko',
        '제1조(인턴십 유형) (1) 체험형 인턴: 4~8주, 직무 체험 및 멘토링 중심. 정규직 전환 대상 아님. (2) 채용연계형 인턴: 8~12주, 실무 수행 및 프로젝트 참여. 평가 후 정규직 전환 심사. (3) 산학협력 인턴: 대학 학점 인정 프로그램 연계, 16주. 제2조(선발 기준) (1) 국내외 대학 재학생 또는 졸업 예정자(졸업 후 2년 이내 포함). (2) 서류 전형(자기소개서 + 성적증명서) → 1차 면접(실무). (3) 채용연계형은 코딩테스트 또는 직무 과제를 추가 실시. 제3조(급여) (1) 체험형: 월 200만원(세전). (2) 채용연계형: 월 250만원(세전). (3) 교통비 월 10만원 별도 지급. (4) 4대보험 가입(고용보험, 산재보험 필수).',
        '{"tags":["인턴십","체험형","채용연계","산학협력","급여","선발"],"category":"채용관리","doc_category":"채용","importance":"high"}',
        NULL, 'text-embedding-3-small', false, 0, 2, NULL, 'sql_import', 'rag_knowledge',
        NULL
    ) RETURNING id INTO parent_id;

    INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
    VALUES (
        1,
        '인턴십 프로그램 운영',
        'policy',
        'ko',
        '제4조(프로그램 구성) (1) 1주차: 오리엔테이션(회사 소개, 부서 투어, 멘토 배정, IT 환경 세팅). (2) 2~4주차: OJT(On-the-Job Training), 실무 업무 보조. (3) 5주차~: 개인/팀 프로젝트 수행. (4) 최종 주: 프로젝트 발표, 동료 피드백, 최종 평가. 제5조(정규직 전환 조건) (1) 채용연계형 인턴만 전환 심사 대상. (2) 평가 항목: 업무 성과(40%), 직무 적합성(30%), 팀 적응도(20%), 태도(10%). (3) 전환율: 통상 60~70%(연도별 인력 계획에 따라 변동). (4) 전환 심사: 멘토 평가 + 팀장 평가 + HR 면담 결과 종합. 제6조(평가 방법) (1) 멘토가 주 1회 면담 기록을 작성하고 인사팀에 공유한다. (2) 중간 평가(4주차): 적응 상황 점검, 목표 조정. (3) 최종 평가(종료 시): 종합 평가표 작성, 전환 추천 여부 결정. 제7조(인턴 복리후생) 구내식당 이용, 연차(주 15시간 이상 시 비례 발생), 단체보험(산재) 적용.',
        '{"tags":["인턴프로그램","정규직전환","OJT","멘토","프로젝트발표","평가"],"category":"채용관리","doc_category":"채용","importance":"high"}',
        NULL, 'text-embedding-3-small', false, 1, 2, parent_id, 'sql_import', 'rag_knowledge', NULL
    );
END $$;

-- [문서 8] 채용 합격 취소 기준
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '채용 합격 취소 기준',
    'policy',
    'ko',
    '제1조(합격 취소 사유) 다음 각 호에 해당하는 경우 최종 합격을 취소할 수 있다: (1) 이력서·자기소개서에 허위 사실을 기재한 경우(학력, 경력, 자격증 위조). (2) 채용 건강검진 결과 직무 수행에 중대한 지장이 있는 경우(의사 소견 기준). (3) 범죄 경력 조회 결과 중대 범죄(금고 이상 실형)가 확인된 경우. (4) 오퍼 수락 기한(7일) 내 미회신 또는 거부 후 재요청. (5) 입사 예정일에 정당한 사유 없이 미출근한 경우. (6) 전 직장 레퍼런스 체크 결과 중대한 비위(횡령, 성범죄 등)가 확인된 경우. 제2조(절차) (1) 인사팀이 합격 취소 사유를 서면으로 확인한다. (2) 법무팀 검토를 거쳐 채용위원회 승인을 받는다. (3) 지원자에게 합격 취소 사유와 이의 제기 방법을 서면 통보한다. 제3조(이의 제기) 합격 취소 통보를 받은 지원자는 7일 이내에 서면으로 이의를 제기할 수 있으며, 채용위원회가 재심의한다. 제4조(건강검진) 입사 전 건강검진은 회사 지정 의료기관에서 실시하며, 비용은 회사가 부담한다. 검진 항목: 일반 검사, 혈액 검사, 흉부 X선, 소변 검사, 간 기능 검사.',
    '{"tags":["합격취소","허위기재","건강검진","범죄경력","이의제기","오퍼"],"category":"채용관리","doc_category":"채용","importance":"high"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- [문서 9] 입사 전 제출 서류 목록
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '입사 전 제출 서류 목록',
    'manual',
    'ko',
    '제1조(필수 서류) (1) 주민등록등본 1통(최근 3개월 이내 발급). (2) 졸업증명서(최종 학력). (3) 경력증명서(경력직, 전 직장 모두). (4) 원천징수영수증(경력직, 연봉 검증용). (5) 건강검진 결과서(회사 지정 기관 발급). (6) 통장 사본(급여 이체용). (7) 사진 2매(3×4cm, 최근 6개월 이내). (8) 비밀유지서약서(서명). (9) 개인정보 수집·이용 동의서(서명). 제2조(선택 서류) (1) 자격증 사본(보유 시). (2) 포트폴리오(디자인/개발직). (3) 추천서(경력직, 있을 경우). (4) 병역 관련 서류(남성, 군필/면제 증빙). 제3조(외국인 추가 서류) (1) 외국인등록증 사본. (2) 취업 비자(E-7, F-2, F-5 등) 사본. (3) 학력 인증 서류(아포스티유 또는 영사 인증). 제4조(제출 기한) 입사일 3영업일 전까지 이메일 또는 직접 제출. 제5조(미제출 시) 필수 서류 미제출 시 입사가 연기될 수 있으며, 입사 후 30일 이내 미보완 시 수습 평가에 부정적으로 반영된다.',
    '{"tags":["입사서류","주민등록","경력증명","건강검진","외국인","비밀유지"],"category":"채용관리","doc_category":"채용","importance":"medium"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- [문서 10] 신입사원 수습 기간 제도
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '신입사원 수습 기간 제도',
    'policy',
    'ko',
    '제1조(수습 기간) (1) 모든 신규 채용자(신입/경력)에 대해 입사일로부터 3개월간 수습 기간을 적용한다. (2) 수습 기간 중 급여: 정규 급여의 100%(수습 감액 없음). (3) 수습 기간은 근속 연수에 포함된다. 제2조(수습 평가) (1) 수습 종료 2주 전에 수습 평가를 실시한다. (2) 평가 항목: 직무 적응도(30%), 업무 이해도(30%), 근무 태도(20%), 팀 협업(20%). (3) 평가 등급: 적합(정규 전환)/조건부 적합(1개월 연장)/부적합(계약 해지). 제3조(정규 전환) (1) 적합 판정: 수습 종료일 익일부로 정규 전환 확정(별도 통보). (2) 조건부 적합: 부족 항목을 명시하고 1개월 추가 수습 후 재평가. 재평가에서도 부적합 시 계약 해지. (3) 부적합: 수습 기간 만료일에 계약 해지. 근로기준법에 따라 14일 전 사전 통보 또는 30일분 해고예고수당 지급. 제4조(수습 기간 중 퇴사) 수습 기간 중 본인 의사에 의한 퇴사는 사직서 제출 후 즉시 또는 합의된 일자에 퇴사 가능하다(30일 전 통보 의무 면제). 제5조(수습 면제) 5년 이상 동종 업계 경력자로서 부서장이 요청하고 인사팀이 승인한 경우 수습 기간을 면제할 수 있다.',
    '{"tags":["수습기간","수습평가","정규전환","조건부적합","부적합","해고예고"],"category":"채용관리","doc_category":"채용","importance":"high"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- [문서 11] 온보딩 프로그램 전체 커리큘럼 (멀티청크 2개)
DO $$
DECLARE parent_id BIGINT;
BEGIN
    INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
    VALUES (
        1,
        '온보딩 프로그램 전체 커리큘럼',
        'guide',
        'ko',
        '제1조(온보딩 목적) 신규 입사자가 빠르게 조직에 적응하고 직무 역량을 발휘할 수 있도록 체계적인 온보딩 프로그램을 운영한다. 제2조(1주차 - 입사 오리엔테이션) (1) Day 1: 인사팀 환영, 사원증 발급, IT 장비 세팅, 보안 서약, 급여/복지 안내. (2) Day 2: 회사 소개(비전·미션·핵심가치), 조직 구조, 주요 사업 소개(동영상 + 강의). (3) Day 3: 사내 시스템 교육(이메일, 메신저, HR시스템, 전자결재, VPN). (4) Day 4: 부서 배치, 팀원 소개, 멘토 배정, 부서 OJT 시작. (5) Day 5: 법정 의무 교육(성희롱 예방, 개인정보보호, 직장 내 괴롭힘 예방). 제3조(2~4주차 - OJT) (1) 멘토와 함께 실무 학습(업무 프로세스, 도구 사용법, 주요 담당자 소개). (2) 주 1회 멘토와 1:1 면담(적응 상황, 어려움 공유, 피드백). (3) 2주차 말: 팀장과 1개월 목표 설정.',
        '{"tags":["온보딩","오리엔테이션","OJT","멘토","입사","신규채용"],"category":"채용관리","doc_category":"채용","importance":"high"}',
        NULL, 'text-embedding-3-small', false, 0, 2, NULL, 'sql_import', 'rag_knowledge',
        NULL
    ) RETURNING id INTO parent_id;

    INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
    VALUES (
        1,
        '온보딩 프로그램 전체 커리큘럼',
        'guide',
        'ko',
        '제4조(1~3개월 - 실무 적응) (1) 1개월차: 기본 업무 독립 수행 시작, 멘토 감독 하 업무 처리. (2) 2개월차: 프로젝트 참여, 협업 부서 미팅 참석, 자율적 업무 수행 확대. (3) 3개월차: 수습 평가 준비, 자기 평가서 작성, 멘토 최종 평가. 제5조(온보딩 체크리스트) 인사팀이 관리하는 체크리스트 항목(30개): ①사원증 발급 ②이메일 계정 활성화 ③보안 교육 이수 ④사내 시스템 접근 권한 ⑤법정 교육 이수 ⑥멘토 배정 확인 ⑦1주차 면담 ⑧2주차 면담 ⑨1개월 목표 설정 ⑩ ... (이하 부서별 맞춤 항목). 제6조(멘토 역할) (1) 멘토는 입사자와 같은 팀의 대리~과장급 직원 1인을 배정한다. (2) 멘토 기간: 3개월(필요 시 6개월까지 연장). (3) 멘토 수당: 월 5만원(멘토링 기간 중). (4) 멘토는 주 1회 면담 기록을 인사팀에 공유한다. 제7조(온보딩 만족도 조사) 입사 3개월 시점에 온보딩 만족도 설문을 실시하며, 결과를 반영하여 프로그램을 개선한다.',
        '{"tags":["온보딩","체크리스트","멘토","수습평가","만족도","실무적응"],"category":"채용관리","doc_category":"채용","importance":"high"}',
        NULL, 'text-embedding-3-small', false, 1, 2, parent_id, 'sql_import', 'rag_knowledge', NULL
    );
END $$;

-- [문서 12] 내부 추천 채용 제도
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '내부 추천 채용 제도',
    'policy',
    'ko',
    '제1조(추천 방법) (1) 재직 직원은 HR시스템 > 채용 > 사내 추천에서 추천서를 제출한다. (2) 추천 시 피추천자의 이력서와 추천 사유(직무 적합성, 인성, 관계 등)를 기재한다. (3) 추천자는 피추천자에게 추천 사실을 사전에 알려야 한다. 제2조(포상금 지급 조건) (1) 피추천자가 최종 합격하여 입사한 후 수습 기간(3개월)을 통과하면 추천 포상금을 지급한다. (2) 포상금 금액: 일반직 100만원, 전문직(IT개발, AI, 보안 등) 200만원, 임원급 500만원. (3) 포상금은 수습 통과 확정 후 익월 급여에 합산 지급한다. 제3조(추천인 책임) (1) 추천인은 피추천자의 경력·인성에 대한 신뢰를 기반으로 추천하며, 허위 추천 시 포상금 반환 + 인사 경고. (2) 추천인이 피추천자의 면접에 면접관으로 참여할 수 없다. 제4조(추천 금지 관계) (1) 직계 가족(부모, 자녀, 배우자). (2) 추천인의 직속 부하가 될 예정인 경우. (3) 동일 부서 내 추천(이해충돌 방지). 제5조(적용 제외) 인턴십, 파견 근로, 일용직 채용에는 사내 추천 제도를 적용하지 않는다.',
    '{"tags":["내부추천","사내추천","포상금","추천채용","전문직","추천금지"],"category":"채용관리","doc_category":"채용","importance":"medium"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- [문서 13] 장애인 의무 고용 이행 정책
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '장애인 의무 고용 이행 정책',
    'policy',
    'ko',
    '제1조(법적 근거) 장애인고용촉진 및 직업재활법에 따라 상시 근로자 50인 이상 사업장은 전체 근로자의 3.1% 이상을 장애인으로 고용하여야 한다. 제2조(채용 목표) (1) 당사 연간 장애인 고용 목표: 법정 의무 고용률 충족 + 추가 0.5%p(자발적 목표). (2) 미달 시 부담금을 납부하므로, 적극적 채용을 통해 의무를 이행한다. 제3조(채용 경로) (1) 한국장애인고용공단 취업 알선. (2) 장애인 특화 채용 박람회 참가(연 2회 이상). (3) 특수학교·직업훈련원 연계 채용. (4) 자사 채용 사이트 장애인 전형 별도 안내. 제4조(직무 배치) (1) 장애 유형에 적합한 직무를 배치한다(시각장애→음성 기반 업무, 지체장애→사무직 등). (2) 합리적 편의 제공: 보조 기기(확대 모니터, 음성 인식 소프트웨어), 접근 가능한 사무 환경, 근무 시간 유연화. (3) 직무 코치(Job Coach) 배치: 입사 후 3개월간 직무 적응을 지원하는 전담 코치를 배정한다. 제5조(고용 유지) (1) 장애인 직원의 이직률을 모니터링하고, 근무 만족도 설문을 연 1회 실시한다. (2) 직무 전환이 필요한 경우 우선적으로 사내 공모에 지원할 수 있도록 지원한다.',
    '{"tags":["장애인","의무고용","채용","편의제공","직무코치","고용공단"],"category":"채용관리","doc_category":"채용","importance":"high"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- [문서 14] 외국인 고용 절차
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '외국인 고용 절차',
    'policy',
    'ko',
    '제1조(비자 유형별 채용 가능 여부) (1) E-7(특정활동): 전문 인력 채용 가능. 고용노동부 허가 필요. (2) F-2(거주): 제한 없이 취업 가능. (3) F-4(재외동포): 단순노무 제외 전 직종 가능. (4) F-5(영주): 제한 없음. (5) F-6(결혼이민): 제한 없음. (6) D-10(구직): 인턴 가능, 정규직은 E-7 전환 필요. 제2조(고용 절차) (1) 외국인 채용 시 「외국인 고용 사전 심사」를 인사팀과 법무팀이 공동으로 실시한다. (2) E-7 비자 발급 소요: 약 4~8주. 고용노동부 내국인 구인 노력 증명(2주 이상 공고)이 필요하다. (3) 입사 확정 후 비자 초청장 발급 → 재외공관 비자 신청 → 입국 → 외국인등록. 제3조(비자 지원) 회사는 비자 발급·갱신에 필요한 서류를 지원하며, 행정사 비용은 회사가 부담한다. 제4조(언어 지원) (1) 사내 문서의 영문 버전 제공(취업규칙, 복지 안내 등). (2) 한국어 학습비 연 100만원 지원. (3) 통역 지원: 주요 미팅 시 영어 통역 제공. 제5조(출국 시 처리) 퇴직 후 비자 만료 전 출국을 지원하며, 퇴직금·급여 정산, 4대보험 반환금 안내를 실시한다.',
    '{"tags":["외국인","비자","E-7","고용절차","언어지원","채용"],"category":"채용관리","doc_category":"채용","importance":"medium"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- [문서 15] 채용 공고 작성 및 게시 규정
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '채용 공고 작성 및 게시 규정',
    'manual',
    'ko',
    '제1조(필수 기재 사항) (1) 모집 직무 및 인원. (2) 자격 요건(학력, 경력, 기술). (3) 우대 사항. (4) 근무 조건(근무지, 근무 시간, 계약 유형). (5) 전형 절차 및 일정. (6) 접수 기간 및 방법. (7) 담당자 연락처. (8) 개인정보 수집·이용 동의 안내. 제2조(금지 표현) (1) 성별 제한: "남성 우대", "여군 출신" 등. (2) 연령 제한: "만 35세 이하", "젊은" 등(법정 예외 제외). (3) 출신 학교: "SKY 출신", "서울 소재 대학" 등. (4) 외모 기준: "단정한 외모", "키 170cm 이상" 등. (5) 가족 상황: "미혼 우대", "자녀 없는 분" 등. 제3조(게시 채널) (1) 자사 채용 사이트: 필수. (2) 잡포털(사람인, 잡코리아): 주요 채용 시. (3) 원티드, LinkedIn: IT/글로벌 직군. (4) 대학 취업지원센터: 신입 공채 시. 제4조(게시 기간) 최소 14일 이상 게시하며, 긴급 채용 시 7일까지 단축 가능(인사팀장 승인 필요). 제5조(비용 관리) 유료 채용 공고 비용은 인사팀 채용 예산에서 집행하며, 건당 100만원 초과 시 인사담당임원 승인이 필요하다.',
    '{"tags":["채용공고","금지표현","게시채널","잡포털","채용사이트","차별금지"],"category":"채용관리","doc_category":"채용","importance":"medium"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- [문서 16] 부서 채용 요청 절차
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '부서 채용 요청 절차',
    'manual',
    'ko',
    '제1조(요청 시기) (1) 정기 요청: 매년 10월, 익년도 인력 계획 수립 시 부서별 소요 인원을 집계. (2) 수시 요청: 퇴직, 업무량 증가, 신규 프로젝트 등으로 긴급 채용이 필요한 경우 수시 요청 가능. 제2조(요청 양식) 「인력 채용 요청서」에 다음을 기재한다: (1) 요청 부서/팀. (2) 모집 직무 및 인원. (3) 채용 사유(충원/증원/신규). (4) 필요 자격 요건. (5) 희망 입사일. (6) 채용 예산(연봉 범위). (7) 업무 설명(JD 첨부). 제3조(승인 단계) (1) 1차: 부서장 승인. (2) 2차: 인사팀 검토(인력 계획 대비 적정성, 예산 확인). (3) 3차: 인사담당임원 승인(과장급 이상 또는 3인 이상 채용 시). (4) 4차: 대표이사 승인(부장급 이상 또는 10인 이상 대규모 채용 시). 제4조(처리 기간) 인사팀은 요청 접수 후 3영업일 이내에 검토 결과를 회신하며, 승인 완료 후 5영업일 이내에 공고를 게시한다. 제5조(반려 사유) 인력 계획 초과, 예산 부족, 기존 인력 재배치 가능 등의 사유로 반려될 수 있으며, 반려 시 대안을 함께 제시한다.',
    '{"tags":["채용요청","인력계획","승인절차","예산","인력충원","증원"],"category":"채용관리","doc_category":"채용","importance":"medium"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- [문서 17] 사내 공모(경력 개발 채용)
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '사내 공모(경력 개발 채용)',
    'policy',
    'ko',
    '제1조(사내 공모 목적) 직원의 경력 개발과 조직 내 인재 활용을 촉진하기 위해 빈 직위를 사내 공모로 우선 충원한다. 제2조(공모 대상 직위) (1) 신규 프로젝트 TF 인력. (2) 타 부서 빈 직위(퇴직·이동에 의한 결원). (3) 해외 주재원 선발. (4) 신설 부서/팀 인력. 제3조(지원 자격) (1) 현 직무에서 최소 1년 이상 근무(수습 기간 포함). (2) 최근 1년 성과평가 C등급 이상. (3) 진행 중인 징계 처분이 없을 것. 제4조(지원 절차) (1) 사내 게시판에 공모 공고 게시(14일 이상). (2) HR시스템에서 지원서 제출. (3) 현 부서장 동의: 원칙적으로 필요하나, 미동의 시에도 지원 가능(인사팀 중재). (4) 전형: 서류 심사 + 수요 부서장 면접. (5) 확정 후 이동 시기: 현 부서 인수인계 기간(최대 1개월)을 거쳐 이동. 제5조(이동 후 처리) (1) 직급·호봉 변동 없이 이동(직무 등급 변경 시 직무 수당 조정). (2) 이동 후 6개월간 적응 기간, 부적응 시 원 부서 복귀 가능(1회 한정).',
    '{"tags":["사내공모","경력개발","부서이동","전환배치","해외주재","인수인계"],"category":"인사관리","doc_category":"채용","importance":"medium"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- [문서 18] 채용 브랜딩 및 후보자 경험 관리
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '채용 브랜딩 및 후보자 경험 관리',
    'guide',
    'ko',
    '제1조(채용 브랜딩 목표) 우수 인재가 당사를 선호하는 고용주(Employer of Choice)로 인식하도록 채용 브랜드를 관리한다. 제2조(주요 활동) (1) 채용 사이트: 회사 문화, 직원 인터뷰, 복지 소개 콘텐츠를 분기별 업데이트. (2) SNS 채용 채널: 인스타그램, 유튜브에 직원 브이로그, 사무실 투어 영상 게시. (3) 대학 캠퍼스 리크루팅: 주요 대학 취업 박람회 참가, 기업 설명회(연 4회 이상). (4) 테크 블로그: IT 직군 채용을 위한 기술 블로그 운영(월 2회 이상 게시). 제3조(후보자 경험 관리) (1) 지원 접수 확인 메일: 지원 후 24시간 이내 자동 발송. (2) 전형 진행 상황 안내: 각 전형 단계별 5영업일 이내 결과 통보. (3) 불합격 통지: 정중한 불합격 메일 + 향후 재지원 안내. 불합격 사유는 구체적으로 공개하지 않되, 요청 시 개괄적 피드백 제공. (4) 합격자 환영: 합격 축하 메시지, 입사 안내 키트(회사 소개서, 체크리스트) 발송. 제4조(후보자 피드백 수집) 전형 참여자 대상 채용 프로세스 만족도 설문을 분기별 실시하여 개선에 반영한다.',
    '{"tags":["채용브랜딩","후보자경험","SNS","캠퍼스","불합격통지","만족도"],"category":"채용관리","doc_category":"채용","importance":"low"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- [문서 19] 채용 관련 FAQ
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '채용 관련 FAQ',
    'faq',
    'ko',
    'Q1. 불합격 후 재지원이 가능한가요? A1. 네, 불합격일로부터 6개월 경과 후 동일 또는 다른 직무에 재지원할 수 있습니다.
Q2. 지원서를 수정할 수 있나요? A2. 접수 마감 전까지 지원서 수정이 가능합니다. 마감 후에는 수정 불가합니다.
Q3. 면접 일정을 변경할 수 있나요? A3. 불가피한 사유 발생 시 면접일 2일 전까지 채용 담당자에게 연락하면 1회 변경 가능합니다.
Q4. 서류를 반환받을 수 있나요? A4. 불합격 통보 후 14일 이내에 요청하면 등기 우편으로 반환합니다.
Q5. 채용 건강검진 비용은 누가 부담하나요? A5. 회사 지정 기관 이용 시 전액 회사가 부담합니다.
Q6. 추천 채용 포상금은 언제 받나요? A6. 피추천자가 수습(3개월)을 통과한 후 익월 급여에 합산 지급됩니다.
Q7. 인턴에서 정규직으로 전환되면 수습이 또 있나요? A7. 채용연계형 인턴을 거친 경우 수습 기간이 면제됩니다.
Q8. 경력직 연봉은 어떻게 결정되나요? A8. 전 직장 급여 증빙과 내부 페이밴드를 기준으로 산정하며, 전 직장 대비 최대 15% 인상 범위입니다.
Q9. 장애인 전형은 별도로 운영되나요? A9. 별도 전형은 없으나, 서류·면접 시 합리적 편의를 제공하며, 장애인 채용 박람회도 활용합니다.
Q10. 외국인도 지원할 수 있나요? A10. 비자 유형에 따라 지원 가능합니다. E-7, F-2, F-4, F-5, F-6 비자 소지자가 대상입니다.
Q11. 사내 공모에 지원하면 현 부서장에게 알려지나요? A11. 원칙적으로 부서장 동의가 필요하나, 미동의 시에도 지원 가능하며 인사팀이 중재합니다.
Q12. 채용 과정에서 개인정보는 어떻게 처리되나요? A12. 불합격자 정보는 180일 보관 후 완전 파기됩니다. 동의 철회 시 즉시 삭제합니다.',
    '{"tags":["채용","FAQ","재지원","면접변경","건강검진","추천채용","인턴전환"],"category":"채용관리","doc_category":"FAQ","importance":"high"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- [문서 20] 채용 데이터 보관 및 파기 규정
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '채용 데이터 보관 및 파기 규정',
    'policy',
    'ko',
    '제1조(보관 기간) (1) 합격자(입사자): 입사일로부터 재직 기간 + 퇴직 후 3년. (2) 불합격자: 최종 전형 결과 통보일로부터 180일(6개월). (3) 면접 녹화 자료: 채용 완료일로부터 1년. (4) 필기시험 결과: 채용 완료일로부터 1년. (5) 인재풀 동의자: 동의 시점으로부터 2년(재동의 시 갱신). 제2조(보관 항목) (1) 이력서, 자기소개서, 포트폴리오. (2) 전형별 평가 결과(서류 채점표, 면접 평가표). (3) 필기시험 답안지 및 결과. (4) 합격자 제출 서류(졸업증명서, 경력증명서 등). (5) 채용 관련 커뮤니케이션 기록(이메일, 문자). 제3조(파기 방법) (1) 전자 데이터: 복구 불가능한 방식으로 영구 삭제(DOD 5220.22-M 또는 동등 기준). (2) 종이 서류: 파쇄기를 이용한 완전 파쇄(교차 절단, 4mm 이하). (3) 파기 기록: 파기 일시, 파기 대상, 파기 방법, 파기 담당자를 기록하고 3년간 보관. 제4조(개인정보 주체의 권리) (1) 지원자는 본인의 채용 데이터 열람, 정정, 삭제를 요청할 수 있다. (2) 삭제 요청 시 14일 이내에 처리하며, 법정 보존 의무가 있는 데이터는 예외. (3) 채용 시 「개인정보 수집·이용 동의서」를 통해 보관 기간 및 파기 방법을 사전 고지한다.',
    '{"tags":["채용데이터","보관","파기","개인정보","이력서","인재풀","삭제"],"category":"채용관리","doc_category":"채용","importance":"high"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- original_content = content 동기화 (INSERT 후 실행)
UPDATE tb_docs SET original_content = content
WHERE source_type = 'sql_import' AND usage_type = 'rag_knowledge' AND original_content IS NULL;
