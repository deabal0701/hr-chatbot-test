-- ============================================================
-- RAG 문서 데이터 - Part 08: 교육/연수/자격증/역량개발
-- 총 문서 수: 20개 (논리적 문서), 멀티청크 포함 총 28행
-- 생성일: 2026-02-27
-- 용도: RAG 검색 테스트 (RAGAS 평가용)
-- ============================================================

-- [문서 1] 연간 교육 계획 및 체계 (멀티청크 3개)
DO $$
DECLARE parent_id BIGINT;
BEGIN
    INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
    VALUES (
        1,
        '연간 교육 계획 및 체계',
        'plan',
        'ko',
        '제1조(목적) 본 계획은 임직원의 직무 역량 강화, 리더십 개발, 법정 의무 교육 이행을 통해 조직의 경쟁력을 확보하고 개인의 성장을 지원함을 목적으로 한다. 제2조(교육 체계) 당사의 교육 체계는 다음 4개 영역으로 구성된다: (1) 공통 역량 교육: 전 직원 대상, 핵심가치, 커뮤니케이션, 문제해결, 디지털 리터러시. (2) 직무 역량 교육: 직무별 전문 지식·기술 강화(개발, 마케팅, 영업, 재무, HR 등). (3) 리더십 교육: 관리자(팀장 이상) 대상, 코칭, 성과관리, 조직관리. (4) 법정 의무 교육: 개인정보보호, 성희롱예방, 직장내괴롭힘예방, 산업안전보건, 퇴직연금. 제3조(교육 예산) (1) 연간 교육 예산: 인건비의 2% 이상 편성. (2) 부서별 배분: 공통(30%), 직무(40%), 리더십(20%), 법정(10%). (3) 미집행 예산은 다음 분기로 이월할 수 있으나, 연말 미집행분은 소멸된다. 제4조(교육 이수 목표) (1) 전 직원: 연간 최소 40시간(법정 교육 포함). (2) 관리자(팀장 이상): 연간 최소 60시간. (3) 신입사원(1년 미만): 연간 최소 80시간(온보딩 교육 포함).',
        '{"tags":["교육계획","교육체계","교육예산","이수목표","공통역량","직무역량"],"category":"교육연수","doc_category":"교육연수","importance":"high"}',
        NULL, 'text-embedding-3-small', false, 0, 3, NULL, 'sql_import', 'rag_knowledge',
        NULL
    ) RETURNING id INTO parent_id;

    INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
    VALUES (
        1,
        '연간 교육 계획 및 체계',
        'plan',
        'ko',
        '제5조(교육 방법) (1) 집합 교육(오프라인): 사내 교육장(본사 5층 세미나실, 수용 60명)에서 실시. (2) 온라인 교육(LMS): 사내 학습관리시스템(LMS)을 통해 자기주도 학습. 콘텐츠: 동영상 강의, e-러닝, 마이크로 러닝(5~10분 단위). (3) 블렌디드 러닝: 온라인 사전학습 + 오프라인 실습·토론 병행. (4) OJT(On-the-Job Training): 부서 내 선배 직원이 직접 업무를 가르치는 현장 교육. (5) 액션 러닝: 실제 업무 과제를 팀 단위로 해결하며 학습. (6) 외부 교육: 사외 전문 교육기관 위탁 교육(사전 승인 필요). (7) 컨퍼런스·세미나: 국내외 업계 컨퍼런스 참석 지원(연 2회, 1인당 200만원 한도). 제6조(LMS 운영) (1) 접속: 사내 인트라넷 → 「교육센터」 또는 모바일 앱. (2) 콘텐츠: 자체 제작 + 외부 구매(LinkedIn Learning, Coursera for Business 연동). (3) 학습 기록: 이수 현황, 평가 결과, 수료증이 자동 기록. (4) 학습 추천: AI 기반 맞춤 학습 콘텐츠 추천(직무, 관심사, 이수 이력 기반). 제7조(교육 평가) (1) 반응 평가(Level 1): 교육 직후 만족도 설문(5점 척도, 평균 4.0 이상 목표). (2) 학습 평가(Level 2): 교육 내용 이해도 테스트(80점 이상 수료). (3) 행동 평가(Level 3): 교육 3개월 후 현업 적용도 조사(상사 평가). (4) 성과 평가(Level 4): 교육 투자 대비 업무 성과 변화 측정(핵심 교육 프로그램에 한함).',
        '{"tags":["교육방법","LMS","블렌디드러닝","OJT","액션러닝","교육평가","커크패트릭"],"category":"교육연수","doc_category":"교육연수","importance":"high"}',
        NULL, 'text-embedding-3-small', false, 1, 3, parent_id, 'sql_import', 'rag_knowledge', NULL
    );

    INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
    VALUES (
        1,
        '연간 교육 계획 및 체계',
        'plan',
        'ko',
        '제8조(교육 운영 프로세스) (1) 교육 니즈 분석(11~12월): 부서별 교육 수요 조사 + 개인 역량 진단 결과 분석 → 차년도 교육 계획 수립. (2) 교육 개발(1~2월): 커리큘럼 설계, 강사 섭외, 교재 개발, LMS 콘텐츠 탑재. (3) 교육 실행(연중): 월별 교육 일정에 따라 실행, 참석률 관리. (4) 교육 평가(수시): 각 교육 종료 후 즉시 평가, 분기별 종합 리포트. (5) 개선(연말): 연간 교육 성과를 분석하고 차년도 계획에 반영. 제9조(교육 이수 관리) (1) 법정 의무 교육 미이수: 1차 경고 → 2차 인사고과 감점 → 3차 승진 심사 제외. (2) 연간 최소 이수시간 미달: 역량 개발 면담 실시, 개인별 학습 계획 수립. (3) 우수 학습자: 연말 「Learning Star」 시상(개인상 3인, 팀상 1개 팀, 각 50만원 상품권). 제10조(교육 수료증) (1) 사내 교육: LMS에서 자동 발급(PDF). (2) 외부 교육: 수료증 사본을 인사팀에 제출하면 이수 이력에 등록. (3) 수료증은 승진 심사, 직무 전환 시 참고 자료로 활용한다.',
        '{"tags":["교육운영","니즈분석","이수관리","미이수처리","Learning Star","수료증"],"category":"교육연수","doc_category":"교육연수","importance":"high"}',
        NULL, 'text-embedding-3-small', false, 2, 3, parent_id, 'sql_import', 'rag_knowledge', NULL
    );
END $$;

-- [문서 2] 법정 의무 교육 안내
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '법정 의무 교육 안내',
    'policy',
    'ko',
    '제1조(법정 의무 교육 목록) 당사에서 실시하는 법정 의무 교육은 다음과 같다: (1) 성희롱 예방 교육: 연 1회, 1시간 이상(남녀고용평등법 제13조). 대상: 전 직원. 미실시 과태료: 500만원 이하. (2) 직장 내 괴롭힘 예방 교육: 연 1회, 1시간 이상(근로기준법 시행령). 대상: 전 직원. (3) 개인정보보호 교육: 연 1회, 2시간 이상(개인정보 보호법 제28조). 대상: 개인정보 취급자. (4) 산업안전보건 교육: 분기 1회, 사무직 3시간/비사무직 6시간(산업안전보건법 제29조). 미실시 과태료: 500만원 이하. (5) 퇴직연금 교육: 연 1회, 1시간 이상(근로자퇴직급여보장법 제32조). 대상: 퇴직연금 가입 직원. (6) 장애인 인식 개선 교육: 연 1회, 1시간 이상(장애인고용촉진법 제5조의2). 대상: 전 직원. 미실시 과태료: 300만원 이하. (7) 소방 안전 교육: 연 1회(소방기본법). 대상: 전 직원. 제2조(교육 시기) (1) 상반기(3~5월): 성희롱 예방, 괴롭힘 예방, 장애인 인식 개선. (2) 하반기(9~11월): 개인정보보호, 퇴직연금, 소방 안전. (3) 산업안전보건: 분기별(1월, 4월, 7월, 10월). 제3조(교육 방법) 온라인(LMS) 또는 집합 교육. 온라인 교육 시 학습 확인 테스트를 포함하여 실질적 교육 이수를 담보한다. 제4조(기록 보관) 교육 실시 기록(일시, 내용, 참석자, 강사)을 3년간 보관하며, 관할 관청 요청 시 제출한다.',
    '{"tags":["법정교육","성희롱예방","괴롭힘예방","산업안전","퇴직연금","장애인인식","과태료"],"category":"교육연수","doc_category":"교육연수","importance":"critical"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- [문서 3] 사내 교육 프로그램 카탈로그
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '사내 교육 프로그램 카탈로그',
    'guide',
    'ko',
    '제1조(공통 역량 교육) (1) 「소통의 기술」: 비폭력 대화(NVC), 경청, 효과적 프레젠테이션. 8시간, 반기 1회 개설. (2) 「문제해결 & 의사결정」: 로지컬 씽킹, 이슈 트리, MECE, 의사결정 매트릭스. 16시간, 연 1회. (3) 「프로젝트 관리 기초」: PM 방법론(워터폴/애자일), WBS, 리스크 관리. 16시간, 연 2회. (4) 「비즈니스 라이팅」: 보고서, 이메일, 제안서 작성법. 4시간, 분기 1회. (5) 「데이터 분석 기초」: Excel 고급(피벗, VBA), BI 도구(Tableau/Power BI 기초). 8시간, 반기 1회. 제2조(직무 역량 교육) (1) IT개발: Python 심화, 클라우드(AWS/Azure), DevOps, 보안 코딩. (2) 마케팅: 디지털 마케팅, 브랜드 전략, CRM, GA4 분석. (3) 영업: 협상 스킬, B2B 세일즈, 고객 관계 관리. (4) 재무: IFRS, 세무 실무, 관리회계, 내부통제. (5) HR: 노동법 실무, 채용 면접 기법, 조직개발(OD), 보상 설계. 각 직무별 연 2~4개 과정 개설, 부서장 추천 또는 개인 신청. 제3조(리더십 교육) (1) 신임 팀장: "New Leader Program"(24시간, 3일). 코칭, 성과관리, 노동법 기초, 조직문화. (2) 중간 관리자: "리더십 역량 강화"(16시간, 2일). 변화관리, 갈등조정, 전략적사고. (3) 임원: "경영 리더십 세미나"(8시간, 1일). 경영 환경, 전략, ESG, 위기관리. 제4조(수강 신청) LMS → 「교육 카탈로그」 → 원하는 과정 신청 → 부서장 승인 → 교육 확정 통보(이메일).',
    '{"tags":["교육카탈로그","공통역량","직무역량","리더십교육","LMS","수강신청"],"category":"교육연수","doc_category":"교육연수","importance":"medium"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- [문서 4] 사외 교육 및 위탁 교육
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '사외 교육 및 위탁 교육 정책',
    'policy',
    'ko',
    '제1조(사외 교육 지원) (1) 업무 관련 외부 교육기관 교육을 지원한다. (2) 지원 한도: 연 300만원/인(부서 예산 범위 내). (3) 신청 절차: 「사외 교육 신청서」(교육명, 기관, 기간, 비용, 업무 관련성) → 부서장 승인 → 인사팀 확인 → 교육비 사전 지급 또는 사후 정산. (4) 교육 종료 후 7일 이내 「교육 결과 보고서」(학습 내용, 현업 적용 계획)를 제출한다. 미제출 시 차기 사외 교육 신청이 제한된다. 제2조(위탁 교육) (1) 장기 위탁 교육(1개월 이상): 석사 과정, 전문 자격 과정, 해외 연수 등. (2) 지원 조건: 근속 3년 이상, 인사평가 B 이상. (3) 위탁 교육 중 급여 100% 지급, 교육비 회사 부담. (4) 의무 복무: 위탁 교육 기간의 2배(최소 1년, 최대 3년). 의무 복무 기간 내 자발적 퇴직 시 교육비를 반환한다(잔여 의무 기간 비례). 제3조(온라인 외부 학습 플랫폼) (1) LinkedIn Learning: 전 직원 무료 이용(회사 계정 제공). (2) Coursera for Business: 선별 과정 무료 수강(직무 관련 과정에 한함). (3) Udemy Business: IT 직군 대상 무료 이용. (4) 수료증은 LMS에 자동 연동되어 이수 기록에 반영된다. 제4조(학회·세미나·컨퍼런스) (1) 연 2회, 1인당 200만원 한도로 국내외 학회·컨퍼런스 참가비를 지원한다. (2) 참가 후 7일 이내 「참가 보고서」를 제출하고, 팀 내 지식 공유 세션(30분)을 실시한다.',
    '{"tags":["사외교육","위탁교육","LinkedIn Learning","Coursera","의무복무","컨퍼런스"],"category":"교육연수","doc_category":"교육연수","importance":"medium"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- [문서 5] 온라인 학습(LMS) 이용 가이드
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '온라인 학습(LMS) 이용 가이드',
    'guide',
    'ko',
    '제1조(접속 방법) (1) PC: 사내 인트라넷 → 「교육센터」 메뉴 → LMS 자동 로그인(SSO). (2) 모바일: 「MUREUM Learning」 앱 다운로드 → 사번/비밀번호 로그인. (3) VPN 접속 시에도 이용 가능(재택근무 시). 제2조(학습 콘텐츠) (1) 자체 제작 콘텐츠: 사내 강사 촬영 강의, 직무 매뉴얼, 사례 연구. (2) 외부 연동 콘텐츠: LinkedIn Learning(15,000+ 과정), Coursera(500+ 과정). (3) 마이크로 러닝: 5~10분 단위 짧은 학습 영상, 매주 월요일 새 콘텐츠 업로드. (4) 학습 경로(Learning Path): 직무별·레벨별로 추천 과정을 순서대로 배치(예: "프로젝트 관리 입문→중급→고급" 3단계). 제3조(학습 기능) (1) 북마크: 관심 과정 즐겨찾기. (2) 학습 노트: 강의 시청 중 메모 기능. (3) 퀴즈·평가: 각 과정 종료 후 이해도 테스트(자동 채점). (4) 수료증: 과정 완료 시 자동 발급(PDF 다운로드). (5) 학습 대시보드: 개인별 이수 현황, 남은 필수 과정, 추천 과정 확인. 제4조(이수 기준) (1) 동영상 강의: 전체 재생 시간의 90% 이상 시청. (2) 퀴즈: 80점 이상 통과(2회 재응시 가능). (3) 실습 과제: 제출 후 강사 확인(합격/불합격). 제5조(문의) LMS 이용 관련 문의: 인사팀 교육담당(내선 3456, training@company.com).',
    '{"tags":["LMS","온라인학습","마이크로러닝","학습경로","수료증","학습대시보드"],"category":"교육연수","doc_category":"교육연수","importance":"low"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- [문서 6] 해외 연수 프로그램 (멀티청크 2개)
DO $$
DECLARE parent_id BIGINT;
BEGIN
    INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
    VALUES (
        1,
        '해외 연수 프로그램',
        'policy',
        'ko',
        '제1조(목적) 글로벌 비즈니스 역량 강화, 선진 사례 벤치마킹, 해외 네트워크 구축을 목적으로 해외 연수 프로그램을 운영한다. 제2조(프로그램 유형) (1) 단기 연수(1~2주): 해외 기업 방문, 컨퍼런스 참석, 벤치마킹. 연 10명 선발. (2) 중기 연수(1~3개월): 해외 파트너사 파견 근무, 현지 교육기관 프로그램 수강. 연 5명 선발. (3) 장기 연수(6개월~1년): MBA, 석사 과정, 연구 프로젝트. 연 2명 선발. (4) 해외 법인 교환 근무(3~6개월): 해외 법인에서 실무 경험. 연 3명 선발. 제3조(선발 기준) (1) 공통 기준: 근속 3년 이상, 최근 2년 인사평가 평균 B+ 이상. (2) 어학 요건: 단기 TOEIC 700+/TOEFL 80+, 중기·장기 TOEIC 850+/TOEFL 95+. (3) 부서장 추천서 + 자기개발계획서(연수 목적, 현업 적용 계획) 제출. (4) 선발위원회(인사담당 임원, 해당 본부장, 인사팀장) 심사. 제4조(지원 내용) (1) 항공료: 이코노미 클래스(장기 연수: 비즈니스 클래스 가능). (2) 숙박: 실비 정산(도시별 상한액 적용, 예: 뉴욕 $200/일, 도쿄 ¥20,000/일). (3) 식비: 일비 $80/일. (4) 교육비: 전액 회사 부담. (5) 급여: 100% 지급(장기 연수 시 해외근무수당 추가). (6) 보험: 해외여행자보험 가입(회사 부담).',
        '{"tags":["해외연수","단기연수","MBA","해외법인","선발기준","어학요건"],"category":"교육연수","doc_category":"교육연수","importance":"high"}',
        NULL, 'text-embedding-3-small', false, 0, 2, NULL, 'sql_import', 'rag_knowledge',
        NULL
    ) RETURNING id INTO parent_id;

    INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
    VALUES (
        1,
        '해외 연수 프로그램',
        'policy',
        'ko',
        '제5조(의무) (1) 연수 종료 후 30일 이내 「연수 결과 보고서」를 제출하고, 전사 공유 세션(1시간)을 실시한다. (2) 의무 복무: 단기 1년, 중기 2년, 장기 3년. (3) 의무 복무 기간 내 퇴직 시 교육비(항공·숙박·교육비)를 반환한다. 반환 금액은 잔여 의무 기간에 비례하여 산정한다. 예: 의무 3년 중 2년 근무 후 퇴직 → 교육비의 1/3 반환. 제6조(안전 관리) (1) 출장국 안전 정보를 사전에 확인(외교부 해외안전여행 사이트). (2) 여행 경보 2단계(여행자제) 이상 국가는 연수 제한. (3) 연수 중 안전 사고 발생 시 즉시 인사팀에 보고하고, 해외여행자보험을 통해 처리한다. (4) 비상 연락망(인사팀 + 현지 담당자)을 출발 전 공유한다. 제7조(연수 후 관리) (1) 연수 경험을 현업에 적용하는 「실행 계획서」를 연수 종료 1개월 내 작성한다. (2) 분기 1회 부서장과 실행 현황을 점검한다. (3) 연수 경험을 사내 교육 콘텐츠(LMS 강의, 세미나)로 개발하는 것을 권장한다.',
        '{"tags":["의무복무","교육비반환","안전관리","연수결과보고","실행계획","지식공유"],"category":"교육연수","doc_category":"교육연수","importance":"high"}',
        NULL, 'text-embedding-3-small', false, 1, 2, parent_id, 'sql_import', 'rag_knowledge', NULL
    );
END $$;

-- [문서 7] 직급별 필수 교육 과정
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '직급별 필수 교육 과정',
    'policy',
    'ko',
    '제1조(사원급) (1) 신입사원 입문 교육(80시간, 2주): 회사 소개, 핵심가치, 비즈니스 매너, 기본 업무 스킬, 보안/개인정보보호, OJT. (2) 1년차 역량 강화(16시간): 보고서 작성, 시간관리, 직무 기초. (3) 2년차 성장 과정(16시간): 문제해결, 프로젝트 참여, 협업 스킬. 제2조(대리급) (1) 승급 필수(8시간): 대리급 역할 인식, 셀프 리더십, 후배 OJT 지도법. (2) 직무 전문성(16시간/년): 직무별 심화 과정 1개 이상 이수. (3) 프로젝트 리딩(8시간): PM 기초, 업무 우선순위, 이해관계자 관리. 제3조(과장급) (1) 승급 필수(16시간): 중간 관리자 역할, 팀 관리 기초, 성과 관리, 코칭 입문. (2) 재무 이해(8시간): 재무제표 읽기, 예산 관리. (3) 직무 전문성(16시간/년): 직무별 고급 과정 1개 이상 이수. 제4조(차장~부장급) (1) 승급 필수(16시간): 전략적 사고, 조직 관리, 갈등 조정, 의사결정. (2) 리더십 코칭(8시간): 코칭 대화법, 피드백 스킬. (3) 경영 이해(8시간): 경영 전략, 마케팅, HR 기초. 제5조(팀장) (1) 신임 팀장 필수(24시간): New Leader Program. (2) 노동법 실무(4시간): 근로계약, 해고, 징계, 근로시간. (3) 성과 면담(4시간): MBO 면담, 피드백 대화, 저성과자 관리. 제6조(임원) 경영 리더십 세미나(8시간/년), ESG·컴플라이언스(4시간/년). 제7조(미이수 시) 승급 필수 과정 미이수 시 승진 심사 대상에서 제외된다.',
    '{"tags":["직급별교육","사원","대리","과장","팀장","임원","승급필수"],"category":"교육연수","doc_category":"교육연수","importance":"high"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- [문서 8] 자격증 취득 지원 제도
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '자격증 취득 지원 제도',
    'policy',
    'ko',
    '제1조(지원 대상 자격증) (1) A등급(핵심 직무): PMP, AWS Solutions Architect Professional, CFA Level 3, 변호사, 공인회계사(CPA), 정보관리기술사. 취득 축하금 200만원, 응시료+교재비 전액. (2) B등급(직무 관련): AWS Associate, CISA, CISSP, SHRM, SQLP, 빅데이터분석기사, 정보보안기사, 감정평가사. 취득 축하금 100만원, 응시료+교재비 전액. (3) C등급(업무 보조): 컴퓨터활용능력 1급, 한국사능력검정 1급, TOEIC 900+, JLPT N1, HSK 6급, 데이터분석 준전문가(ADsP), 리눅스마스터 1급. 취득 축하금 30만원, 응시료 전액. 제2조(지원 내용) (1) 응시료: 합격·불합격 무관하게 지원(동일 자격증 연 3회까지). (2) 교재비: A·B등급 자격증에 한하여 30만원 한도. (3) 학원비: A등급 자격증에 한하여 100만원 한도(사전 승인 필요). (4) 시험 당일 유급 특별휴가(0.5일) 부여. 제3조(신청 절차) (1) 응시 전: 「자격증 취득 지원 신청서」를 인사팀에 제출(자격증명, 등급, 예상 비용). (2) 합격 후: 자격증 사본 + 비용 영수증 제출 → 축하금 급여에 포함 지급 + 비용 정산. 제4조(자격증 관리) (1) 자격증 보유 현황을 인사 DB에 등록·관리한다. (2) 갱신이 필요한 자격증(PMP, CISSP 등)의 갱신 비용도 회사가 부담한다. (3) 자격증 보유는 승진 심사 시 가점(A등급 3점, B등급 2점, C등급 1점)으로 반영한다.',
    '{"tags":["자격증","PMP","AWS","CISSP","축하금","응시료","승진가점"],"category":"교육연수","doc_category":"교육연수","importance":"high"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- [문서 9] 사내 강사 제도
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '사내 강사 제도',
    'policy',
    'ko',
    '제1조(사내 강사란) 특정 분야의 전문 지식·경험을 보유한 임직원이 자발적으로 사내 교육 강사로 활동하는 것을 말한다. 제2조(선발) (1) 자격: 근속 2년 이상, 해당 분야 실무 경험 3년 이상 또는 관련 자격증 보유자. (2) 신청: 「사내 강사 지원서」(교육 주제, 경력, 교수 경험)를 인사팀에 제출. (3) 심사: 인사팀 + 해당 직무 전문가가 강의 시연(30분)을 평가. (4) 위촉: 1년 단위 위촉, 갱신 가능. 현재 위촉된 사내 강사: 약 30명. 제3조(보상) (1) 강의 수당: 1시간당 5만원(업무 시간 외 강의 시 10만원). (2) 연간 사내 강사 활동 10시간 이상 시 성과평가 역량 항목 가점. (3) 우수 사내 강사 시상: 연말 「Best Instructor」 선정(3인, 50만원 상품권). (4) 강의 개발 지원: 교안 작성, 교재 제작, 촬영 장비를 인사팀에서 지원. 제4조(의무) (1) 연간 최소 2개 과정(총 8시간 이상)을 개설한다. (2) 교육 만족도 평가에서 평균 3.5점(5점 만점) 미만 시 재교육 또는 강사 위촉 해제. (3) 강의 콘텐츠의 저작권은 회사에 귀속된다(사내 교육 목적 한정). 제5조(강의 스킬 교육) 사내 강사 위촉 후 3개월 이내 「교수법 워크숍」(8시간)을 이수하며, 성인 학습 원리, 교안 설계, 퍼실리테이션 기법을 학습한다.',
    '{"tags":["사내강사","강의수당","교수법","교안","Best Instructor","위촉"],"category":"교육연수","doc_category":"교육연수","importance":"medium"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- [문서 10] 코칭 및 멘토링 프로그램 (멀티청크 2개)
DO $$
DECLARE parent_id BIGINT;
BEGIN
    INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
    VALUES (
        1,
        '코칭 및 멘토링 프로그램',
        'policy',
        'ko',
        '제1조(멘토링 프로그램) (1) 목적: 신입사원 및 직무 전환자의 조기 적응과 성장을 지원한다. (2) 유형: ①신입사원 멘토링: 입사 후 6개월간, 선배 직원(3년 이상)이 1:1 멘토. ②직무 전환 멘토링: 직무 변경 후 3개월간, 해당 직무 경험자가 멘토. ③여성 리더 멘토링: 여성 관리자 후보를 대상으로 여성 임원이 멘토(6개월). ④역멘토링: 주니어가 시니어에게 디지털 역량을 멘토링(세대간 협업 가이드 참조). (3) 매칭: 인사팀에서 직무, 관심사, 성향을 고려하여 매칭. 타 부서 간 매칭 우선. (4) 활동: 월 2회 이상 1:1 면담(1시간), 면담 기록 작성(LMS 등록). (5) 멘토 보상: 멘토링 완료 시 10만원 상품권 + 성과평가 역량 가점. 제2조(코칭 프로그램) (1) 대상: 팀장 이상 리더, 고성과자 중 차기 리더 후보. (2) 유형: ①외부 전문 코칭: 인증 코치(ICF ACC 이상)가 1:1 코칭(6회, 3개월). ②내부 코칭: 코칭 자격을 보유한 사내 리더가 코칭(격월 1회). ③그룹 코칭: 동일 레벨 리더 4~6명이 함께하는 그룹 코칭(월 1회, 2시간). (3) 비용: 외부 코칭 1인당 300만원(회사 전액 부담). (4) 신청: 인사팀 추천 또는 본인 신청 → 인사담당 임원 승인.',
        '{"tags":["멘토링","코칭","신입사원","역멘토링","ICF","그룹코칭"],"category":"교육연수","doc_category":"교육연수","importance":"high"}',
        NULL, 'text-embedding-3-small', false, 0, 2, NULL, 'sql_import', 'rag_knowledge',
        NULL
    ) RETURNING id INTO parent_id;

    INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
    VALUES (
        1,
        '코칭 및 멘토링 프로그램',
        'policy',
        'ko',
        '제3조(멘토링 운영 절차) (1) 매칭(1월, 7월): 인사팀이 멘토-멘티 매칭 후 통보. (2) 킥오프(매칭 후 1주 내): 멘토-멘티 첫 만남, 목표 설정, 활동 계획 수립. (3) 정기 면담(월 2회): 업무 적응, 고민 상담, 경력 조언, 학습 가이드. (4) 중간 점검(3개월 차): 인사팀이 멘토-멘티에게 만족도 설문, 필요 시 매칭 조정. (5) 종료(6개월 차): 멘토링 성과 보고서 제출(멘토·멘티 각각), 멘토 보상 지급. 제4조(코칭 성과 측정) (1) 코칭 시작 전 리더십 진단(자기 평가 + 부하 평가)을 실시한다. (2) 코칭 종료 후 동일 진단을 재실시하여 변화를 측정한다. (3) 코칭 만족도(5점 척도), 현업 적용도(3개월 후 자기 보고)를 평가한다. (4) 코칭 ROI: 코치 비용 대비 리더십 평가 점수 향상, 팀 성과 변화를 분석(연 1회, 전체 프로그램 대상). 제5조(코칭 문화 확산) (1) 전 리더가 "코칭 리더십"을 일상 업무에서 실천하도록 코칭 스킬 기본 과정(8시간)을 제공한다. (2) 코칭 대화 모델(GROW: Goal-Reality-Options-Will)을 사내 표준으로 채택하고, 1:1 면담 시 활용을 권장한다. (3) 코칭 우수 사례를 타운홀 미팅에서 공유하여 문화를 확산한다.',
        '{"tags":["멘토링절차","코칭성과","GROW모델","리더십진단","코칭ROI","코칭문화"],"category":"교육연수","doc_category":"교육연수","importance":"high"}',
        NULL, 'text-embedding-3-small', false, 1, 2, parent_id, 'sql_import', 'rag_knowledge', NULL
    );
END $$;

-- [문서 11] 직무 전환 교육
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '직무 전환 교육 정책',
    'policy',
    'ko',
    '제1조(목적) 인사 이동, 부서 전환, 직무 변경 시 새로운 직무에 빠르게 적응할 수 있도록 체계적인 전환 교육을 제공한다. 제2조(대상) (1) 정기 인사 이동(매년 1월, 7월)에 따른 부서·직무 변경자. (2) 자발적 직무 전환(사내 공모) 선발자. (3) 프로젝트 파견 후 원소속 복귀자(장기 파견 6개월 이상). 제3조(교육 내용) (1) 직무 기초 교육(40시간): 새 직무의 핵심 지식, 프로세스, 도구, 시스템. 인사팀+전입 부서 공동 설계. (2) OJT(On-the-Job Training): 전입 부서에서 선임 직원이 2~4주간 현장 교육. (3) 멘토링: 전환 멘토 배정(3개월). (4) 자기 학습: LMS에서 해당 직무 Learning Path 이수. 제4조(일정) (1) 전환 교육 시작: 인사 발령일부터 1주 이내. (2) 직무 기초 교육: 발령 후 2주 이내 완료. (3) OJT: 발령 후 4주 이내 완료. (4) 적응도 확인 면담: 발령 후 1개월, 3개월 시점에 인사팀+부서장 면담. 제5조(평가) (1) 전환 교육 이수 후 직무 이해도 테스트(80점 이상 합격). (2) 3개월 후 직무 적응도 평가(상사 평가): 적응 양호/보통/미흡. (3) 미흡 시 추가 교육(2주) 또는 직무 재조정을 검토한다. 제6조(사내 공모 전환자 특별 지원) (1) 사내 공모로 직무 전환 시, 전입 부서의 교육 비용을 별도 예산으로 지원(100만원 한도). (2) 전환 후 6개월간 성과평가는 "전환 적응기"로 별도 평가(기존 평가와 병행하지 않음).',
    '{"tags":["직무전환","인사이동","OJT","사내공모","적응교육","전환멘토"],"category":"교육연수","doc_category":"교육연수","importance":"medium"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- [문서 12] 리더십 개발 프로그램
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '리더십 개발 프로그램',
    'policy',
    'ko',
    '제1조(리더십 파이프라인) 당사는 각 직급 단계에 맞는 리더십 역량을 체계적으로 개발한다: (1) Individual Contributor → Team Leader: 셀프 리더십 → 피플 리더십(코칭, 위임, 동기부여). (2) Team Leader → Department Head: 피플 리더십 → 비즈니스 리더십(전략, 재무, 변화관리). (3) Department Head → Executive: 비즈니스 리더십 → 경영 리더십(비전, 조직문화, 외부관계). 제2조(프로그램 상세) (1) 차기 리더 육성 과정(Future Leader Program): 대상: 대리~과장급 중 리더 잠재력이 높은 인원(연 15명 선발). 기간: 6개월, 월 2일(총 96시간). 내용: 리더십 진단, 전략적 사고, 재무 분석, 코칭 실습, 프로젝트 과제. (2) 신임 팀장 과정(New Leader Program): 대상: 팀장 승진자 전원. 기간: 3일(24시간). 내용: 리더 역할 인식, 성과관리, 코칭 대화, 노동법, 조직문화 실천. (3) 리더십 마스터 과정: 대상: 부장급 이상 리더(경력 리더 대상). 기간: 2일(16시간). 내용: 변화 리더십, 전략 실행, 조직 설계, 갈등 관리, 외부 특강. (4) 임원 리더십 세미나: 대상: 임원 전원. 기간: 1일(8시간). 내용: 경영 환경 분석, CEO 특강, ESG, 리스크 관리. 제3조(평가·후속) (1) 프로그램 전·후 리더십 역량 진단(360도 평가 연동). (2) 프로그램 종료 후 3개월 내 실행 계획 이행 점검. (3) Future Leader 수료자는 팀장 승진 심사 시 가점(3점).',
    '{"tags":["리더십개발","FutureLeader","NewLeader","리더십파이프라인","360도평가","승진가점"],"category":"교육연수","doc_category":"교육연수","importance":"high"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- [문서 13] 독서 토론 및 학습 동아리
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '독서 토론 및 학습 동아리 제도',
    'policy',
    'ko',
    '제1조(독서 경영) (1) CEO 추천 도서: 분기 1회 CEO가 추천하는 도서를 전 직원에게 배포(전자책 또는 종이책 선택). (2) 도서 구입비 지원: 업무 관련 도서 구입비 연 20만원 지원(영수증 정산). (3) 사내 도서관: 본사 3층에 도서관 운영(장서 2,000권, 신간 월 20권 입고). 대출: 1인 3권, 2주간. 제2조(독서 토론) (1) 부서별 독서 토론: 분기 1회, CEO 추천 도서 또는 직무 관련 도서를 선정하여 1시간 토론. (2) 전사 북클럽: 월 1회(마지막 주 금요일 16시), 자발적 참여, 주제별 도서 선정. (3) 독서 토론 참여 시 학습 시간(1시간/회)으로 인정. 제3조(학습 동아리, CoP) (1) "학습 동아리(Community of Practice)"란 공통 관심 분야의 직원 5~10인이 자발적으로 모여 정기적으로 학습하는 그룹이다. (2) 등록: 인사팀에 「학습 동아리 등록 신청서」(주제, 멤버, 활동 계획) 제출. (3) 지원: 월 10만원 활동비(도서, 간식, 장소 대여 등). (4) 활동: 월 2회 이상 정기 모임(1시간 이상). 모임 후 학습 기록을 LMS에 등록. (5) 운영 기간: 6개월 단위, 연장 가능. (6) 성과 발표: 반기 1회 학습 동아리 발표회를 개최하고, 우수 동아리를 시상(30만원 상품권). (7) 학습 시간 인정: 동아리 활동 시간을 연간 교육 이수시간에 포함(최대 16시간). 제4조(현재 운영 동아리) ①AI/ML 스터디(10명), ②프로젝트 관리 CoP(8명), ③디자인 씽킹(6명), ④Python 코딩(7명), ⑤영어 토론(5명), ⑥ESG 연구회(6명).',
    '{"tags":["독서토론","학습동아리","CoP","도서관","CEO추천도서","북클럽"],"category":"교육연수","doc_category":"교육연수","importance":"low"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- [문서 14] 어학 교육 지원
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '어학 교육 지원 제도',
    'policy',
    'ko',
    '제1조(지원 대상) 전 직원(정규직, 1년 이상 계약직). 해외 업무 관련 부서 우선 지원. 제2조(지원 프로그램) (1) 사내 영어 회화 수업: 원어민 강사, 주 2회(점심시간 12:30~13:20), 레벨별 반 운영(초급/중급/고급). 무료. (2) 전화/화상 영어: 외부 업체 위탁, 주 5회 25분, 월 비용의 50% 회사 지원(상한 10만원/월). (3) 어학시험 응시료: TOEIC, TOEFL, IELTS, JLPT, HSK 등 연 2회 응시료 전액 지원. (4) 어학 학원비: 연 120만원 한도 지원(업무 관련성 확인 후, 출석률 80% 이상 시 정산). (5) 해외 어학연수: 해외 연수 프로그램의 일부로 지원(별도 정책 참조). 제3조(인센티브) (1) 어학 성적 향상 인센티브: 6개월 내 TOEIC 100점 이상 향상 시 30만원, 200점 이상 50만원. (2) 고득점 축하금: TOEIC 950+, TOEFL 110+, IELTS 8.0+ 달성 시 50만원(최초 1회). (3) 제2외국어 축하금: JLPT N1, HSK 6급 취득 시 50만원. 제4조(어학 등급제) 직원의 어학 수준을 S/A/B/C 4등급으로 관리하며, 글로벌 직무 배치 시 참고한다. S등급(TOEIC 900+): 해외 파견 우선 대상. A등급(800~899): 해외 출장 가능. B등급(700~799): 기본 업무 가능. C등급(699 이하): 어학 향상 권장.',
    '{"tags":["어학교육","영어회화","TOEIC","어학연수","어학시험","인센티브"],"category":"교육연수","doc_category":"교육연수","importance":"medium"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- [문서 15] 교육 효과 측정 및 ROI
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '교육 효과 측정 및 ROI 분석',
    'policy',
    'ko',
    '제1조(측정 모델) 당사는 커크패트릭(Kirkpatrick) 4단계 모델을 기반으로 교육 효과를 측정한다: Level 1(Reaction), Level 2(Learning), Level 3(Behavior), Level 4(Results). 핵심 교육 프로그램에는 Phillips ROI 모델(Level 5)을 추가 적용한다. 제2조(Level 1: 반응) 모든 교육에 적용. 교육 직후 만족도 설문(강의 내용, 강사, 교재, 시설 5점 척도). 목표: 평균 4.0/5.0 이상. 3.5 미만 과정은 개선 또는 폐지 검토. 제3조(Level 2: 학습) 지식 습득이 중요한 과정에 적용. 사전/사후 테스트로 학습 전이율 측정. 목표: 사후 테스트 평균 80점 이상, 사전 대비 20% 이상 향상. 제4조(Level 3: 행동) 핵심 교육(리더십, 직무전환, 법정교육)에 적용. 교육 3개월 후 상사·동료 설문으로 현업 적용도 측정. 목표: "현업에 적용하고 있다" 응답 70% 이상. 제5조(Level 4: 성과) 투자 규모가 큰 프로그램(해외연수, 리더십 개발)에 적용. 교육 전·후 핵심 성과 지표(KPI) 비교. 예: 리더십 교육 → 팀 성과, 이직률, 직원 만족도 변화. 제6조(Level 5: ROI) 주요 프로그램에 선별 적용. ROI(%) = (교육으로 인한 순이익 / 교육 비용) × 100. 목표: ROI 100% 이상(투자 대비 2배 이상 효과). 제7조(보고) 교육 효과 측정 결과를 반기 1회 경영진에게 보고하며, 차기 교육 계획에 반영한다.',
    '{"tags":["교육효과","ROI","커크패트릭","Phillips","학습전이","성과측정"],"category":"교육연수","doc_category":"교육연수","importance":"medium"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- [문서 16] 학위 취득 지원
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '학위 취득 지원 정책',
    'policy',
    'ko',
    '제1조(대상 학위) (1) 석사: 업무 관련 분야(경영학, 컴퓨터공학, 데이터사이언스, 법학 등). (2) 박사: 연구 인력 한정(R&D, 기술 분야). (3) 학사: 비학위 소지자의 학사 취득 지원(방송통신대, 사이버대 등). 제2조(지원 조건) (1) 근속 3년 이상(박사: 5년 이상). (2) 최근 2년 인사평가 평균 B 이상. (3) 부서장 추천 + 자기개발계획서 제출. (4) 연간 선발 인원: 석사 5명, 박사 1명, 학사 10명. 제3조(지원 내용) (1) 등록금: 학기당 500만원 한도(석사), 700만원 한도(박사), 200만원 한도(학사). (2) 교재비: 학기당 20만원. (3) 학업 시간: 석사 주 4시간, 박사 주 8시간의 학습 시간을 업무 시간 중 사용 가능(부서장 승인). (4) 논문 휴가: 학위 논문 제출 전 5일 유급 특별휴가. 제4조(의무 복무) (1) 석사: 졸업 후 3년. (2) 박사: 졸업 후 5년. (3) 학사: 졸업 후 2년. (4) 의무 복무 기간 내 퇴직 시 지원 금액의 잔여 기간 비례분을 반환한다. 제5조(학점·졸업 관리) (1) 학기당 학점 유지 기준: B학점(3.0/4.5) 이상. (2) 기준 미달 시 다음 학기 지원을 중단하며, 연속 2학기 미달 시 지원을 종료한다. (3) 졸업 시 학위증 사본을 인사팀에 제출한다.',
    '{"tags":["학위취득","석사","박사","등록금","의무복무","학업시간"],"category":"교육연수","doc_category":"교육연수","importance":"medium"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- [문서 17] AI/디지털 역량 교육
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    'AI 및 디지털 역량 교육 정책',
    'policy',
    'ko',
    '제1조(배경) AI, 클라우드, 데이터 분석 등 디지털 기술이 모든 업무에 영향을 미치는 시대에, 전 직원의 디지털 역량 강화가 필수적이다. 제2조(디지털 역량 등급) (1) DL1(Digital Literacy 기초): MS Office 활용, 온라인 협업 도구(Teams, Slack, Notion). (2) DL2(데이터 활용): Excel 고급(피벗, 매크로), BI 도구(Power BI/Tableau), SQL 기초. (3) DL3(디지털 혁신): Python/R 프로그래밍, AI/ML 기초, 프로세스 자동화(RPA). (4) DL4(디지털 전문가): AI/ML 심화, 클라우드 아키텍처, 데이터 엔지니어링. 제3조(전사 필수 교육) (1) AI 리터러시(4시간, 연 1회): AI란 무엇인가, 생성형 AI 활용법(ChatGPT, Copilot), AI 윤리, 업무 적용 사례. 대상: 전 직원. (2) 데이터 기반 의사결정(4시간): 데이터 읽기, 대시보드 해석, A/B 테스트 기초. 대상: 과장급 이상. (3) 정보보안 & AI(2시간): AI 사용 시 보안 유의사항, 기밀정보 입력 금지, Shadow AI 방지. 대상: 전 직원. 제4조(전문 교육) (1) Python for Business(16시간): 비개발 직군 대상, 데이터 분석 자동화. (2) Prompt Engineering(8시간): AI 도구의 효과적 활용법. (3) RPA(Robotic Process Automation)(16시간): 반복 업무 자동화. (4) Cloud 기초(AWS/Azure)(16시간): IT 직군 대상. 제5조(AI 활용 가이드라인) (1) 회사 승인 AI 도구만 사용(Shadow AI 금지). (2) AI에 고객 개인정보, 영업비밀, 미공개 재무정보를 입력하지 않는다. (3) AI 생성 결과물은 반드시 사람이 검증한 후 업무에 사용한다.',
    '{"tags":["AI교육","디지털역량","ChatGPT","RPA","PromptEngineering","디지털리터러시"],"category":"교육연수","doc_category":"교육연수","importance":"high"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- [문서 18] 교육 이수 기록 관리 (멀티청크 2개)
DO $$
DECLARE parent_id BIGINT;
BEGIN
    INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
    VALUES (
        1,
        '교육 이수 기록 관리',
        'policy',
        'ko',
        '제1조(기록 대상) 모든 교육 활동(사내, 사외, 온라인, 자격증, 학위, 학습동아리, 멘토링 등)의 이수 기록을 관리한다. 제2조(기록 시스템) (1) LMS(학습관리시스템): 온라인·사내 교육의 이수 기록이 자동 저장된다. (2) HRIS(인사정보시스템): LMS 데이터가 일일 배치로 HRIS에 연동된다. 자격증, 학위, 사외 교육은 인사팀이 수동 등록. (3) 기록 항목: 교육명, 교육기관, 교육 유형, 이수 일자, 이수 시간, 평가 점수, 수료 여부, 수료증 번호. 제3조(기록 열람) (1) 본인: LMS 또는 HRIS 마이페이지에서 자신의 전체 교육 이수 이력을 열람할 수 있다. (2) 부서장: 소속 팀원의 이수 현황을 열람할 수 있다(개인 평가 점수는 열람 불가). (3) 인사팀: 전사 교육 이수 현황을 관리·분석한다. 제4조(기록 활용) (1) 승진 심사: 필수 교육 이수 여부, 총 이수시간, 자격증 보유 확인. (2) 인사 이동: 직무 관련 교육 이수 이력 참고. (3) 성과평가: 역량 개발 노력 평가 시 참고. (4) 개인 역량 진단: 이수 이력 기반 약점 분석 → 맞춤 학습 추천.',
        '{"tags":["이수기록","LMS","HRIS","기록관리","열람권한","승진심사"],"category":"교육연수","doc_category":"교육연수","importance":"medium"}',
        NULL, 'text-embedding-3-small', false, 0, 2, NULL, 'sql_import', 'rag_knowledge',
        NULL
    ) RETURNING id INTO parent_id;

    INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
    VALUES (
        1,
        '교육 이수 기록 관리',
        'policy',
        'ko',
        '제5조(보관 기간) (1) 법정 의무 교육 기록: 3년(관련 법령 요구). (2) 일반 교육 기록: 재직 기간 + 퇴직 후 1년. (3) 자격증·학위 기록: 영구 보관. (4) 보관 기간 경과 시 개인정보보호 정책에 따라 파기한다. 제6조(외부 교육 기록 등록) (1) 사외 교육, 컨퍼런스, 자격증 취득 등 LMS에 자동 기록되지 않는 교육은 본인이 직접 등록하거나 인사팀에 증빙을 제출하여 등록한다. (2) 등록 시 필요 서류: 수료증 또는 참가 확인서 사본. (3) 미등록 교육은 이수시간에 포함되지 않으며, 승진 심사 시 인정되지 않는다. 제7조(통계·보고) (1) 인사팀은 월별 교육 이수 현황(이수율, 총 시간, 만족도)을 집계한다. (2) 분기별 교육 KPI 보고서를 경영진에게 보고한다: ①전사 1인당 평균 교육시간, ②법정교육 이수율, ③교육 만족도, ④교육 예산 집행률. (3) 연말 교육 성과 보고서: 교육 ROI, 우수 학습자, 프로그램별 성과를 종합 보고한다. 제8조(개인정보) 교육 이수 기록은 개인정보에 해당하므로, 개인정보보호 정책에 따라 안전하게 관리하며, 본인 동의 없이 제3자에게 제공하지 않는다.',
        '{"tags":["보관기간","외부교육등록","통계보고","교육KPI","1인당교육시간","개인정보"],"category":"교육연수","doc_category":"교육연수","importance":"medium"}',
        NULL, 'text-embedding-3-small', false, 1, 2, parent_id, 'sql_import', 'rag_knowledge', NULL
    );
END $$;

-- [문서 19] 교육/연수 FAQ
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '교육 및 연수 FAQ',
    'faq',
    'ko',
    'Q1: 연간 최소 교육 이수시간은 몇 시간인가요? A1: 일반 직원 40시간, 관리자(팀장 이상) 60시간, 신입사원(1년 미만) 80시간입니다. 법정 의무 교육 시간도 포함됩니다. Q2: 사외 교육비 지원은 어떻게 신청하나요? A2: 「사외 교육 신청서」를 인사팀에 제출하여 부서장+인사팀 승인 후 교육비를 사전 지급받거나 사후 정산합니다. 연 300만원 한도입니다. 교육 후 7일 이내 결과 보고서를 제출해야 합니다. Q3: 자격증 시험 떨어지면 응시료는 지원 안 되나요? A3: 합격·불합격 무관하게 동일 자격증에 대해 연 3회까지 응시료를 전액 지원합니다. Q4: 해외 연수는 누가 갈 수 있나요? A4: 근속 3년 이상, 최근 2년 평가 B+ 이상이면 신청 가능합니다. 어학 요건(단기 TOEIC 700+, 중장기 850+)도 충족해야 합니다. 연 약 20명 선발됩니다. Q5: LMS에서 강의를 듣다가 중단하면 어떻게 되나요? A5: 학습 진도가 자동 저장되므로, 다음 접속 시 중단한 지점부터 이어서 학습할 수 있습니다. 단, 수료 기준은 전체 재생 시간의 90% 이상 시청입니다. Q6: 학위 과정 중 학점이 B 미만이면 어떻게 되나요? A6: 다음 학기 지원이 중단됩니다. 연속 2학기 미달 시 지원이 종료됩니다. 이미 지원받은 금액은 반환 의무가 없으나, 의무 복무 기간은 유지됩니다.',
    '{"tags":["FAQ","교육이수","사외교육","자격증","해외연수","LMS","학위"],"category":"교육연수","doc_category":"교육연수","importance":"medium"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- [문서 20] 신입사원 온보딩 교육 상세
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '신입사원 온보딩 교육 상세',
    'guide',
    'ko',
    '제1조(교육 기간) 입사일로부터 2주간(10영업일, 총 80시간). 제2조(1주차: 공통 과정) Day 1: 입사 오리엔테이션(인사팀). 사원증 발급, IT 장비 수령, 시스템 계정 생성, 사내 투어, 조직도·핵심가치 안내. Day 2: 회사 소개. 사업 영역, 주요 제품·서비스, 재무 현황, 경영 전략(경영기획팀 특강). Day 3: 핵심가치 & 조직문화. 행동강령, 일하는 방식, 호칭 문화, 회의·보고 문화(조직문화팀). Day 4: 보안 & 개인정보보호. 정보보안 정책, 개인정보보호, 보안 서약서 서명(보안팀+개인정보보호팀). Day 5: 법정 교육 & HR 제도. 성희롱예방, 괴롭힘예방, 산업안전, 인사제도(연차, 복지, 평가 등). 제3조(2주차: 직무 과정) Day 6~8: 직무별 기초 교육. 배속 부서의 업무 프로세스, 시스템, 도구, 주요 프로젝트 소개. 부서 선배(OJT 담당자)가 진행. Day 9: 팀 프로젝트. 동기 입사자 팀으로 미니 프로젝트 수행(직무와 관련된 실전 과제). Day 10: 수료식 & 네트워킹. 교육 소감 발표, 임원 격려사, 동기 네트워킹 시간, 멘토 매칭 안내. 제4조(온보딩 버디) (1) 배속 부서에서 "온보딩 버디"(입사 2년 이상 선배)를 1인 배정한다. (2) 버디 역할: 업무 외 궁금증 해소(사내 문화, 식당, 편의시설 등), 사내 네트워크 소개, 적응 지원. (3) 버디 활동 기간: 입사 후 3개월. 제5조(적응 점검) (1) 1개월 차: 인사팀 면담(적응 현황, 고충 상담). (2) 3개월 차: 부서장+인사팀 면담(수습 평가 연계). (3) 6개월 차: 멘토 면담(성장 계획 수립).',
    '{"tags":["온보딩","신입사원","OJT","온보딩버디","수료식","적응점검"],"category":"교육연수","doc_category":"교육연수","importance":"high"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- original_content = content 동기화 (INSERT 후 실행)
UPDATE tb_docs SET original_content = content
WHERE source_type = 'sql_import' AND usage_type = 'rag_knowledge' AND original_content IS NULL;
