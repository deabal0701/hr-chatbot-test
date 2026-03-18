-- ============================================================
-- RAG 문서 데이터 - Part 05: 정보보안/IT보안/물리보안 정책
-- 총 문서 수: 20개 (논리적 문서), 멀티청크 포함 총 28행
-- 생성일: 2026-02-27
-- 용도: RAG 검색 테스트 (RAGAS 평가용)
-- ============================================================

-- [문서 1] 정보보안 정책 총칙 (멀티청크 3개)
DO $$
DECLARE parent_id BIGINT;
BEGIN
    INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
    VALUES (
        1,
        '정보보안 정책 총칙',
        'regulation',
        'ko',
        '제1조(목적) 본 정책은 당사의 정보 자산을 내·외부 위협으로부터 보호하고, 정보의 기밀성·무결성·가용성을 확보함을 목적으로 한다. 제2조(적용 범위) (1) 본 정책은 임직원, 계약직, 파견직, 인턴, 협력업체 직원 등 당사의 정보 자산에 접근하는 모든 인원에게 적용된다. (2) 적용 대상 자산: 전자 데이터, 종이 문서, 소프트웨어, 하드웨어, 네트워크, 사업장 시설. 제3조(기본 원칙) (1) 최소 권한 원칙(Least Privilege): 업무 수행에 필요한 최소한의 접근 권한만 부여한다. (2) 알 필요성 원칙(Need to Know): 업무상 필요한 정보에만 접근을 허용한다. (3) 심층 방어(Defense in Depth): 단일 보안 수단에 의존하지 않고, 다계층 보안을 적용한다. (4) 보안 책임: 모든 임직원은 자신이 접근·관리하는 정보의 보안에 대한 책임을 진다.',
        '{"tags":["정보보안","총칙","기밀성","무결성","가용성","최소권한"],"category":"보안정책","doc_category":"보안정책","importance":"critical"}',
        NULL, 'text-embedding-3-small', false, 0, 3, NULL, 'sql_import', 'rag_knowledge',
        NULL
    ) RETURNING id INTO parent_id;

    INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
    VALUES (
        1,
        '정보보안 정책 총칙',
        'regulation',
        'ko',
        '제4조(정보 분류) 당사의 정보 자산은 다음 4등급으로 분류한다: (1) 극비(Top Secret): 유출 시 회사에 치명적 손해. 예: 핵심 기술, M&A 계획, 고객 DB 전체. (2) 비밀(Confidential): 유출 시 심각한 손해. 예: 재무 정보, 인사 정보, 고객 계약 내용. (3) 대외비(Internal): 사내 공유 가능하나 외부 유출 금지. 예: 내부 업무 매뉴얼, 조직도. (4) 일반(Public): 공개 가능. 예: 채용 공고, 보도자료, 제품 카탈로그. 제5조(보안 조직) (1) CISO(Chief Information Security Officer): 정보보안 정책 총괄 책임자. (2) 정보보안팀: 정책 수립, 이행 점검, 사고 대응. (3) 부서 보안 담당자: 각 부서별 1인 지정, 부서 내 보안 관리. 제6조(위반 시 제재) (1) 경미한 위반(보안 교육 미이수, 비밀번호 미변경 등): 경고 + 재교육. (2) 중대한 위반(정보 유출, 무단 접근 등): 징계(정직~해고) + 민·형사 법적 조치. (3) 위반 사실 은폐: 위반 자체보다 중한 처분.',
        '{"tags":["정보분류","극비","비밀","대외비","CISO","보안조직","제재"],"category":"보안정책","doc_category":"보안정책","importance":"critical"}',
        NULL, 'text-embedding-3-small', false, 1, 3, parent_id, 'sql_import', 'rag_knowledge', NULL
    );

    INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
    VALUES (
        1,
        '정보보안 정책 총칙',
        'regulation',
        'ko',
        '제7조(정책 개정) (1) 정보보안 정책은 연 1회 이상 검토·개정한다. (2) 법규 변경, 보안 사고 발생, 신기술 도입 등 중대 변화 시 수시 개정한다. (3) 개정 절차: 정보보안팀 초안 → CISO 검토 → 경영회의 승인 → 전 직원 공지. 제8조(보안 서약) (1) 모든 임직원은 입사 시 「정보보안 서약서」에 서명한다. (2) 서약 내용: 정보 보호 의무, 비밀 유지, 위반 시 법적 책임 동의, 퇴직 후 2년간 비밀 유지 의무. (3) 협력업체 직원도 프로젝트 투입 전 별도 보안 서약서에 서명한다. 제9조(보안 감사) (1) 내부 보안 감사: 반기 1회 정보보안팀 주관. (2) 외부 보안 감사: 연 1회 독립 보안 전문 업체 위탁. (3) 감사 범위: 접근 권한 적정성, 로그 관리, 취약점 점검, 물리적 보안, 정책 준수도. (4) 감사 결과: 경영진에 보고하며, 미흡 사항은 30일 이내 시정 조치한다. 제10조(사고 보고 의무) 보안 사고 또는 의심 상황 발견 시 즉시 정보보안팀에 신고하여야 하며, 미신고 시 위반 행위에 준하여 처분한다.',
        '{"tags":["정책개정","보안서약","보안감사","사고보고","퇴직후의무","시정조치"],"category":"보안정책","doc_category":"보안정책","importance":"critical"}',
        NULL, 'text-embedding-3-small', false, 2, 3, parent_id, 'sql_import', 'rag_knowledge', NULL
    );
END $$;

-- [문서 2] 비밀번호 관리 정책
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '비밀번호 관리 정책',
    'policy',
    'ko',
    '제1조(복잡도 요구사항) (1) 최소 10자 이상. (2) 영문 대문자, 소문자, 숫자, 특수문자 중 3종류 이상 조합. (3) 연속 동일 문자 3회 이상 사용 금지(예: aaa, 111). (4) 사번, 이름, 생년월일 등 추측 가능한 정보 사용 금지. (5) 사전에 등재된 단어 그대로 사용 금지(패스워드 사전 공격 대비). 제2조(변경 주기) (1) 일반 사용자: 90일마다 변경 필수. (2) 시스템 관리자: 60일마다 변경 필수. (3) 최근 5회 사용한 비밀번호 재사용 금지. 제3조(비밀번호 공유 금지) (1) 비밀번호를 타인과 공유(구두, 메모, 이메일, 메신저)하는 것을 엄격히 금지한다. (2) 공용 계정 사용 시에도 개인 비밀번호가 아닌 별도 비밀번호를 설정하며, 담당자 변경 시 즉시 변경한다. 제4조(분실·유출 시 처리) (1) 비밀번호 분실 또는 유출 의심 시 즉시 IT헬프데스크에 신고하고 비밀번호를 재설정한다. (2) IT팀은 해당 계정의 접근 로그를 분석하여 비인가 접근 여부를 확인한다. 제5조(MFA) 핵심 시스템(HR, 재무, 개발서버, VPN)은 다단계 인증(MFA)을 필수 적용한다.',
    '{"tags":["비밀번호","패스워드","복잡도","변경주기","MFA","다단계인증"],"category":"접근관리","doc_category":"보안정책","importance":"high"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- [문서 3] 사내 네트워크 보안 정책
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '사내 네트워크 보안 정책',
    'policy',
    'ko',
    '제1조(네트워크 구성) (1) 사내 네트워크는 업무망, 인터넷망, DMZ, 개발망, 게스트망으로 분리 운영한다. (2) 업무망과 인터넷망 간 트래픽은 방화벽 및 프록시를 경유한다. 제2조(접속 방법) (1) 사내 접속: 사원증 기반 802.1X 인증 Wi-Fi 또는 유선 LAN. (2) 원격 접속: 회사 승인 VPN만 허용(SSL VPN, 클라이언트 필수 설치). (3) 개인 모바일 핫스팟(테더링)을 업무 PC에 연결하는 것은 금지한다. 제3조(네트워크 모니터링) (1) 전 구간 네트워크 트래픽을 IDS/IPS 및 SIEM으로 모니터링한다. (2) 임직원의 인터넷 사용은 URL 필터링으로 유해 사이트 접속을 차단하며, 모니터링 사실을 사전 고지한다. (3) P2P, 토렌트, 불법 스트리밍 사이트 접속은 차단되며, 우회 접속 시도(프록시, VPN 터널링)도 탐지·차단한다. 제4조(게스트 네트워크) 방문객은 게스트 Wi-Fi만 이용 가능하며, 사내 시스템 접근은 불가하다. 게스트 계정은 당일 만료로 설정한다. 제5조(위반 탐지) 비인가 네트워크 장비(개인 AP, 허브 등) 설치 시 NAC(Network Access Control)에 의해 자동 차단되며, 정보보안팀에 즉시 통보된다.',
    '{"tags":["네트워크","VPN","방화벽","IDS","모니터링","게스트","802.1X"],"category":"네트워크보안","doc_category":"보안정책","importance":"high"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- [문서 4] 외부 매체 및 장치 보안 (멀티청크 2개)
DO $$
DECLARE parent_id BIGINT;
BEGIN
    INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
    VALUES (
        1,
        '외부 매체 및 장치 보안',
        'policy',
        'ko',
        '제1조(USB 사용 통제) (1) 원칙적으로 모든 PC에서 USB 저장 장치(메모리, 외장 하드) 사용을 차단한다(DLP 솔루션 적용). (2) 업무상 불가피한 경우 정보보안팀에 「USB 사용 신청서」를 제출하고, 승인된 보안 USB만 사용할 수 있다. (3) 보안 USB: AES-256 암호화, 회사 관리 솔루션 탑재, 분실 시 원격 데이터 삭제 기능. (4) 승인된 USB에도 극비·비밀 등급 데이터 저장은 금지한다(별도 보안 승인 필요). 제2조(개인 노트북 반입) (1) 개인 노트북의 사내 네트워크 연결은 원칙적으로 금지한다. (2) 예외: 외부 강사, 협력업체 발표 등 업무 목적으로 부서장 승인 + IT팀 보안 점검 후 게스트망에 한해 허용. (3) 개인 노트북에 사내 자료를 저장하는 것은 엄격히 금지한다.',
        '{"tags":["USB","외부매체","DLP","보안USB","개인노트북","반입"],"category":"매체보안","doc_category":"보안정책","importance":"high"}',
        NULL, 'text-embedding-3-small', false, 0, 2, NULL, 'sql_import', 'rag_knowledge',
        NULL
    ) RETURNING id INTO parent_id;

    INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
    VALUES (
        1,
        '외부 매체 및 장치 보안',
        'policy',
        'ko',
        '제3조(BYOD 정책) (1) 개인 스마트폰, 태블릿의 업무 활용(이메일, 메신저, 일정)은 MDM(Mobile Device Management) 솔루션 설치 후 허용한다. (2) MDM 기능: 원격 잠금, 원격 초기화, 앱 설치 제한, 화면 캡처 제한(업무 앱 내). (3) MDM 설치를 거부할 경우 개인 기기에서 사내 시스템 접근이 불가하다. 제4조(프린터 및 복합기) (1) 프린터 출력 시 개인 인증(사원증 태깅)을 거치며, 출력 기록이 보관된다. (2) 극비·비밀 문서 출력 시 워터마크(출력자 사번, 일시)가 자동 삽입된다. (3) 스캔: USB 스캔은 차단, 이메일 스캔은 DLP 필터링 적용. 제5조(외장 저장 장치 폐기) (1) USB, 외장 하드, CD/DVD 등 데이터 저장 매체 폐기 시 물리적 파쇄 또는 디가우징(자기 소거) 처리한다. (2) IT팀이 폐기를 집행하며, 폐기 기록(일시, 매체 종류, 시리얼 번호, 파쇄 방법)을 3년간 보관한다.',
        '{"tags":["BYOD","MDM","프린터","워터마크","스캔","매체폐기","디가우징"],"category":"매체보안","doc_category":"보안정책","importance":"high"}',
        NULL, 'text-embedding-3-small', false, 1, 2, parent_id, 'sql_import', 'rag_knowledge', NULL
    );
END $$;

-- [문서 5] 클라우드 서비스 이용 정책
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '클라우드 서비스 이용 정책',
    'policy',
    'ko',
    '제1조(허가된 클라우드) (1) 업무 목적으로 사용 가능한 클라우드 서비스: Microsoft 365(OneDrive, Teams, SharePoint), Google Workspace(G Suite), AWS, Azure(개발·운영). (2) 사용 전 정보보안팀의 보안 평가를 거쳐 허가 목록에 등재된 서비스만 이용 가능하다. 제2조(데이터 업로드 기준) (1) 일반 등급: 허가된 클라우드에 자유롭게 업로드 가능. (2) 대외비: 허가된 클라우드의 회사 테넌트 내에서만 공유 가능(외부 링크 공유 금지). (3) 비밀/극비: 클라우드 업로드 금지. 사내 보안 파일 서버만 이용. 제3조(개인 클라우드 금지) (1) 개인 계정의 Dropbox, Google Drive, iCloud, Naver Cloud 등에 업무 데이터를 저장하는 것을 금지한다. (2) DLP 솔루션으로 개인 클라우드로의 파일 업로드를 탐지·차단한다. 제4조(SaaS 도입 절차) 새로운 SaaS 도입 시 정보보안팀의 보안 평가(체크리스트 50개 항목), 법무팀의 계약 검토, IT팀의 기술 적합성 검토를 거쳐야 한다. 제5조(데이터 주권) 클라우드 서비스의 데이터 저장 위치는 대한민국 또는 회사가 지정한 국가여야 하며, 개인정보는 국내 리전에 저장한다.',
    '{"tags":["클라우드","SaaS","OneDrive","AWS","개인클라우드","DLP","데이터주권"],"category":"클라우드보안","doc_category":"보안정책","importance":"high"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- [문서 6] 이메일 보안 정책
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '이메일 보안 정책',
    'policy',
    'ko',
    '제1조(외부 발송 시 보안) (1) 비밀 이상 등급의 자료를 이메일로 외부 전송하는 것은 원칙적으로 금지한다. (2) 불가피한 경우: 부서장 승인 + 파일 암호화(AES-256) + 비밀번호 별도 전달(유선/문자). (3) DLP 시스템이 첨부파일의 주민등록번호, 신용카드번호, 기밀 키워드를 실시간 탐지하여 발송을 차단하거나 승인 요청을 생성한다. 제2조(첨부파일 제한) (1) 단일 첨부파일 최대 20MB, 총 첨부 용량 50MB. (2) 실행 파일(.exe, .bat, .cmd, .ps1 등) 첨부 금지. (3) 대용량 파일은 사내 파일 공유 시스템(WebDisk)을 이용한다. 제3조(피싱 메일 대응) (1) 의심스러운 이메일(알 수 없는 발신자, 긴급 요청, URL 클릭 유도)은 열지 말고 정보보안팀에 신고한다. (2) 피싱 신고 채널: 이메일 내 「피싱 신고」 버튼 클릭 또는 보안팀 내선번호. (3) 정보보안팀은 분기 1회 피싱 모의 훈련을 실시하며, 클릭률 10% 이상인 부서에 추가 교육을 실시한다. 제4조(이메일 보관) 이메일은 3년간 보관하며, 법적 분쟁 시 증거로 활용될 수 있음을 고지한다.',
    '{"tags":["이메일","피싱","DLP","첨부파일","암호화","피싱훈련","외부발송"],"category":"이메일보안","doc_category":"보안정책","importance":"high"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- [문서 7] 소프트웨어 설치 및 관리 정책
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '소프트웨어 설치 및 관리 정책',
    'policy',
    'ko',
    '제1조(허가된 소프트웨어) (1) IT팀이 관리하는 「허가 소프트웨어 목록(Whitelist)」에 등재된 소프트웨어만 설치 가능하다. (2) 목록에 없는 소프트웨어 설치가 필요한 경우 「소프트웨어 설치 요청서」를 IT팀에 제출하며, 보안 평가 후 승인/반려한다. (3) 오픈소스 소프트웨어: 라이선스 검토(법무팀) + 보안 취약점 검토(IT팀) 후 승인. 제2조(무단 설치 금지) (1) 승인 없이 소프트웨어를 설치하는 것을 금지하며, 엔드포인트 보안 솔루션(EDR)이 비인가 설치를 탐지·차단한다. (2) 적발 시 즉시 삭제 조치 + 보안 경고. 반복 적발 시 징계 대상. 제3조(라이선스 관리) (1) 모든 상용 소프트웨어는 적법한 라이선스를 보유하여야 한다. (2) IT팀이 라이선스 대장을 관리하며, 연 1회 실사를 통해 불법 소프트웨어를 점검한다. (3) 개인이 구매한 소프트웨어를 회사 PC에 설치하는 것도 라이선스 적합성 확인 후 허용한다. 제4조(패치 관리) 운영체제 및 주요 소프트웨어의 보안 패치는 배포 후 14일 이내에 적용하며, 긴급 취약점(CVSS 9.0 이상)은 72시간 이내에 적용한다.',
    '{"tags":["소프트웨어","설치","라이선스","EDR","패치","오픈소스","Whitelist"],"category":"SW보안","doc_category":"보안정책","importance":"high"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- [문서 8] 원격 근무 보안 요건
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '원격 근무 보안 요건',
    'policy',
    'ko',
    '제1조(VPN 필수 사용) (1) 사외에서 사내 시스템에 접근할 때는 반드시 회사 VPN을 통해 접속하여야 한다. (2) VPN 접속 시 MFA(다단계 인증)를 적용한다. (3) VPN 접속 로그는 1년간 보관한다. 제2조(공용 Wi-Fi 금지) (1) 카페, 호텔, 공항 등 공용(개방형) Wi-Fi 환경에서 업무 시스템에 접속하는 것을 금지한다. (2) 불가피한 경우 모바일 핫스팟(LTE/5G) + VPN 조합으로 접속한다. 제3조(화면 잠금) (1) 자리 비움 시 반드시 화면 잠금(Win+L 또는 Ctrl+Command+Q)을 실행한다. (2) 5분 이상 미사용 시 자동 화면 잠금이 활성화되어야 한다. 제4조(물리적 보안) (1) 업무 PC를 공공장소에 방치하지 않는다. (2) 이동 시 노트북은 잠금 장치가 있는 가방에 보관한다. (3) 도난·분실 시 즉시 IT팀에 신고하여 원격 잠금/초기화를 요청한다. 제5조(화상회의 보안) (1) 화상회의 시 공유 화면에 민감 정보가 노출되지 않도록 주의한다. (2) 비밀 이상 등급 논의 시 회의 녹화를 금지하며, 참석자를 사전 확인한다. (3) 회의 링크에 비밀번호를 설정하고, 대기실(Lobby) 기능을 활성화한다.',
    '{"tags":["원격근무","VPN","재택보안","화면잠금","공용WiFi","화상회의"],"category":"원격보안","doc_category":"보안정책","importance":"high"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- [문서 9] 물리적 보안 정책 (멀티청크 2개)
DO $$
DECLARE parent_id BIGINT;
BEGIN
    INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
    VALUES (
        1,
        '물리적 보안 정책',
        'policy',
        'ko',
        '제1조(출입 통제) (1) 사업장 출입은 사원증(RFID/NFC) 또는 생체 인증(지문, 안면)으로 통제한다. (2) 출입 등급: 일반 구역(전 직원), 제한 구역(해당 부서원), 보안 구역(인가자만). (3) 보안 구역: 서버룸, 금고, 경영진 회의실, R&D 연구소. 이중 인증(사원증 + 생체) 적용. 제2조(방문객 등록) (1) 모든 방문객은 1층 안내데스크에서 신분증 제시 후 방문증을 발급받는다. (2) 방문증에는 방문 일시, 방문 목적, 방문 대상자, 허용 구역이 명시된다. (3) 방문객은 반드시 직원의 에스코트를 받아야 하며, 단독 이동은 금지된다. (4) 방문 종료 시 방문증을 반납하고 퇴실 기록을 남긴다. 제3조(CCTV 운영) (1) 사업장 주요 구역(출입구, 복도, 주차장, 서버룸)에 CCTV를 설치·운영한다. (2) CCTV 영상은 30일간 보관하며, 보안 사고 발생 시 최대 1년까지 보관 연장.',
        '{"tags":["물리보안","출입통제","RFID","방문객","CCTV","보안구역"],"category":"물리보안","doc_category":"보안정책","importance":"high"}',
        NULL, 'text-embedding-3-small', false, 0, 2, NULL, 'sql_import', 'rag_knowledge',
        NULL
    ) RETURNING id INTO parent_id;

    INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
    VALUES (
        1,
        '물리적 보안 정책',
        'policy',
        'ko',
        '제4조(Clean Desk 정책) (1) 퇴근 시 책상 위에 문서, USB, 노트북 등을 방치하지 않는다. (2) 서류는 잠금 캐비닛에 보관하고, 노트북은 잠금 장치(켄싱턴 락)를 사용한다. (3) 화이트보드·모니터에 메모(비밀번호, IP 주소 등)를 부착하지 않는다. (4) 정보보안팀이 월 1회 야간 점검을 실시하며, 위반 부서에 경고를 발부한다. 제5조(서버룸 보안) (1) 서버룸 출입은 IT팀 및 인가된 엔지니어로 제한한다. (2) 서버룸 출입 시 사유, 작업 내용, 입퇴실 시간을 기록한다. (3) 서버룸 환경: 항온항습(22±2°C, 습도 45~55%), UPS, 소화 설비, 누수 감지. (4) 외부 업체(유지보수) 출입 시 IT팀 담당자가 동행하며, 작업 내용을 실시간 감시한다. 제6조(문서 보안) (1) 비밀 이상 등급 문서는 보안 캐비닛(잠금)에 보관하며, 문서 대장에 기록한다. (2) 불필요한 출력물은 보안 파쇄함에 투입하여 파쇄한다(일반 휴지통 투입 금지). (3) 문서 폐기 시 교차 절단 파쇄(4mm 이하)를 적용하며, 분기 1회 전문 업체 위탁 파쇄를 실시한다.',
        '{"tags":["CleanDesk","서버룸","문서보안","파쇄","캐비닛","야간점검"],"category":"물리보안","doc_category":"보안정책","importance":"high"}',
        NULL, 'text-embedding-3-small', false, 1, 2, parent_id, 'sql_import', 'rag_knowledge', NULL
    );
END $$;

-- [문서 10] 보안 사고 대응 절차 (멀티청크 2개)
DO $$
DECLARE parent_id BIGINT;
BEGIN
    INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
    VALUES (
        1,
        '보안 사고 대응 절차',
        'policy',
        'ko',
        '제1조(사고 분류) (1) Level 1(경미): 스팸 메일 수신, 악성코드 탐지·차단, 정책 위반 경고. (2) Level 2(보통): 악성코드 감염, 비인가 접근 시도, USB 분실. (3) Level 3(심각): 데이터 유출(의심), 시스템 해킹, 랜섬웨어 감염. (4) Level 4(위기): 대규모 데이터 유출 확정, 서비스 중단, 외부 공개. 제2조(신고 방법) (1) 전화: 정보보안팀 비상 연락처(내선 8282, 24시간). (2) 이메일: security@company.com. (3) 사내 메신저: 보안사고신고 채널. (4) 발견 즉시 신고하며, 최초 신고 시 ①발견 일시 ②사고 유형 ③영향 범위 ④초동 조치 사항을 보고한다. 제3조(초동 대응) (1) 감염 PC: 네트워크 분리(LAN 케이블 제거, Wi-Fi 끔) → 전원 유지(포렌식 증거 보존). (2) 계정 침해: 즉시 비밀번호 변경 + 세션 강제 종료. (3) 물리적 침입: 경비팀 보고 + CCTV 확보.',
        '{"tags":["보안사고","사고대응","랜섬웨어","데이터유출","초동대응","신고"],"category":"사고대응","doc_category":"보안정책","importance":"critical"}',
        NULL, 'text-embedding-3-small', false, 0, 2, NULL, 'sql_import', 'rag_knowledge',
        NULL
    ) RETURNING id INTO parent_id;

    INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
    VALUES (
        1,
        '보안 사고 대응 절차',
        'policy',
        'ko',
        '제4조(조사 절차) (1) 정보보안팀이 CERT(Computer Emergency Response Team)를 구성한다(보안팀장, IT팀, 해당 부서). (2) 디지털 포렌식: 감염 PC 이미지 수집, 로그 분석, 악성코드 분석, 타임라인 구성. (3) 영향 분석: 유출 데이터 범위, 피해 대상(고객, 직원), 법적 의무(신고, 통지) 확인. (4) 조사 기간: Level 3 이상은 24시간 이내 1차 보고, 7일 이내 최종 보고. 제5조(복구) (1) 감염 시스템 격리 → 클린 이미지 복원 → 보안 패치 적용 → 서비스 재개. (2) 랜섬웨어: 복호화 키 확보 시도(법 집행기관 협조) → 불가 시 백업 복원. (3) 계정 침해: 전사 비밀번호 리셋, MFA 강화, 접근 권한 재검토. 제6조(사후 분석) (1) 사고 후 14일 이내에 「사고 분석 보고서」를 작성한다(원인, 경과, 피해, 대응, 재발방지 대책). (2) 보고 대상: CISO → 경영진 → 이사회(Level 4). (3) 재발 방지: 정책 개정, 시스템 강화, 추가 교육 실시. 제7조(외부 신고) 개인정보 유출 시 개인정보보호위원회에 72시간 이내 신고하고, 정보주체에게 지체 없이 통지한다.',
        '{"tags":["CERT","포렌식","복구","사후분석","재발방지","외부신고","개인정보유출"],"category":"사고대응","doc_category":"보안정책","importance":"critical"}',
        NULL, 'text-embedding-3-small', false, 1, 2, parent_id, 'sql_import', 'rag_knowledge', NULL
    );
END $$;

-- [문서 11] 내부자 위협 방지 정책
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '내부자 위협 방지 정책',
    'policy',
    'ko',
    '제1조(최소 권한 부여) (1) 직원에게는 현재 직무 수행에 필요한 최소한의 시스템·데이터 접근 권한만 부여한다. (2) 권한 부여 시 부서장 + IT팀 승인을 거치며, 승인 기록을 보관한다. (3) 부서 이동, 직무 변경 시 기존 권한은 즉시 회수하고 신규 직무에 맞는 권한을 재부여한다. 제2조(이상 행위 탐지) (1) SIEM/UEBA(User and Entity Behavior Analytics) 솔루션으로 비정상 접근 패턴을 모니터링한다. (2) 탐지 대상: 대량 데이터 다운로드, 비업무 시간 접근, 비인가 시스템 접근 시도, USB 대량 복사. (3) 이상 행위 탐지 시 자동 알림이 정보보안팀에 전달되며, 48시간 이내 조사를 실시한다. 제3조(퇴직자 계정 처리) (1) 퇴직일 당일: 모든 시스템 계정 비활성화, 이메일 접근 차단, VPN 인증서 폐기. (2) 퇴직일 + 7일: 계정 완전 삭제(백업 제외). (3) 퇴직 전 1주간 데이터 접근 로그를 별도 보관(1년)하여 이상 행위를 사후 확인한다. 제4조(특권 계정 관리) 시스템 관리자, DBA 등 특권 계정은 PAM(Privileged Access Management) 솔루션으로 관리하며, 모든 작업을 녹화·감사한다.',
    '{"tags":["내부자위협","최소권한","UEBA","퇴직자계정","특권계정","PAM"],"category":"내부보안","doc_category":"보안정책","importance":"high"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- [문서 12] 보안 교육 이수 의무
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '보안 교육 이수 의무',
    'policy',
    'ko',
    '제1조(교육 대상) 전 임직원(정규직, 계약직, 파견직, 인턴)은 정보보안 교육을 의무적으로 이수하여야 한다. 제2조(교육 내용 및 시간) (1) 일반 직원: 연 2회, 회당 2시간(총 4시간). 내용: 보안 정책 개요, 피싱 대응, 비밀번호 관리, Clean Desk, 사회공학 방지. (2) IT/개발 직군: 연 4회, 회당 2시간(총 8시간). 추가 내용: 시큐어 코딩, 취약점 관리, 인시던트 대응, OWASP Top 10. (3) 관리자(팀장급 이상): 연 1회, 4시간. 내용: 리더의 보안 책임, 내부자 위협 인식, 사고 대응 의사결정. (4) 신규 입사자: 입사 1주일 이내 온라인 보안 교육(2시간) 이수 필수. 제3조(미이수 시 불이익) (1) 교육 기한 내 미이수: 1차 경고 메일 발송. (2) 경고 후 14일 이내 미이수: 시스템 접근 권한 일시 제한. (3) 30일 경과 미이수: 인사 경고 + 부서장 통보. 제4조(교육 방법) (1) 온라인: LMS(Learning Management System)에서 동영상 시청 + 퀴즈(80점 이상 합격). (2) 오프라인: 보안 세미나, 해킹 시연, 실습 워크숍. 제5조(기록) 교육 이수 기록은 3년간 보관하며, 보안 감사 시 증빙 자료로 제출한다.',
    '{"tags":["보안교육","의무교육","피싱","시큐어코딩","OWASP","LMS"],"category":"보안교육","doc_category":"보안정책","importance":"high"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- [문서 13] 취약점 관리 및 패치 정책
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '취약점 관리 및 패치 정책',
    'policy',
    'ko',
    '제1조(취약점 등급) CVSS(Common Vulnerability Scoring System) 기준: (1) Critical(9.0~10.0): 72시간 이내 패치 적용. (2) High(7.0~8.9): 7일 이내. (3) Medium(4.0~6.9): 30일 이내. (4) Low(0.1~3.9): 90일 이내 또는 다음 정기 패치. 제2조(취약점 스캔) (1) 외부 대면 시스템(웹서버, API): 주 1회 자동 스캔. (2) 내부 시스템: 월 1회 자동 스캔. (3) 스캔 도구: Nessus, Qualys, OpenVAS 중 지정 도구 사용. 제3조(패치 관리 절차) (1) 패치 공개 시 IT보안팀이 영향도 분석(48시간 이내). (2) 테스트 환경에서 패치 적용 테스트. (3) 변경 관리 절차에 따라 운영 환경 적용(변경 승인 → 적용 → 검증). (4) 긴급 패치는 CISO 승인 하에 변경 관리 절차를 축약할 수 있다. 제4조(예외 승인) 업무 시스템 호환성 등 이유로 패치를 지연해야 하는 경우 CISO 승인 후 보완 조치(네트워크 격리, 추가 모니터링)를 적용한다. 예외 기간은 최대 90일이며, 매 30일마다 재검토한다. 제5조(제로데이) 제로데이 취약점 발견 시 24시간 이내 비상 대응 체제를 가동하며, 임시 완화 조치(WAF 룰, 네트워크 격리)를 우선 적용한다.',
    '{"tags":["취약점","패치","CVSS","제로데이","스캔","긴급패치","보완조치"],"category":"취약점관리","doc_category":"보안정책","importance":"critical"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- [문서 14] 암호화 정책
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '암호화 정책',
    'policy',
    'ko',
    '제1조(전송 데이터 암호화) (1) 인터넷 구간: TLS 1.2 이상 필수(TLS 1.0/1.1 사용 금지). (2) 내부 네트워크: 비밀 이상 등급 데이터 전송 시 TLS 또는 IPsec VPN 적용. (3) 이메일: S/MIME 또는 PGP 암호화 지원(비밀 이상 등급 필수). 제2조(저장 데이터 암호화) (1) 데이터베이스: 개인정보, 금융 정보 컬럼은 AES-256으로 암호화. (2) 파일 서버: BitLocker(Windows), FileVault(Mac)로 디스크 전체 암호화. (3) 모바일 기기: 기기 자체 암호화 활성화 필수. (4) 백업 테이프/디스크: AES-256 암호화 적용. 제3조(암호화 알고리즘) (1) 대칭키: AES-256. (2) 비대칭키: RSA-2048 이상 또는 ECDSA P-256. (3) 해시: SHA-256 이상(MD5, SHA-1 사용 금지). (4) 알고리즘 선정은 국정원 또는 NIST 권고를 따른다. 제4조(키 관리) (1) 암호화 키는 HSM(Hardware Security Module)에 저장한다. (2) 키 생성, 배포, 갱신, 폐기 절차를 문서화하며, 키 관리 담당자를 지정한다. (3) 키 갱신 주기: 대칭키 연 1회, 비대칭키 2년. (4) 키 접근은 최소 2인 이상의 승인이 필요하다(분할 지식 원칙).',
    '{"tags":["암호화","TLS","AES-256","RSA","키관리","HSM","디스크암호화"],"category":"암호화","doc_category":"보안정책","importance":"critical"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- [문서 15] 접근 권한 관리 정책
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '접근 권한 관리 정책',
    'policy',
    'ko',
    '제1조(권한 부여 절차) (1) 신규 계정: 입사 시 인사팀 요청 → IT팀이 직무별 기본 권한 세트(Role) 부여. (2) 추가 권한: 「시스템 접근 권한 요청서」 작성 → 부서장 승인 → IT팀 설정. (3) 특권 권한(관리자): CISO 또는 IT팀장 최종 승인 필요. 제2조(정기 검토) (1) 분기 1회 전체 계정 및 권한을 검토한다(IT팀 + 부서 보안 담당자). (2) 미사용 계정(90일 이상 미접속): 비활성화 처리, 30일 후 삭제. (3) 과다 권한(직무 대비 불필요한 권한): 즉시 회수. 제3조(직무 변경 시) (1) 부서 이동·직무 변경 시 기존 권한을 즉시 회수하고, 새 직무에 맞는 권한을 부여한다. (2) 인사팀이 인사 발령 정보를 IT팀에 자동 연동하며, IT팀은 발령일 당일 권한을 변경한다. 제4조(공용 계정) (1) 공용 계정 사용을 최소화하며, 불가피한 경우 사용 기록(누가, 언제)을 별도 관리한다. (2) 공용 계정 비밀번호는 담당자 변경 시 즉시 변경한다. 제5조(감사 추적) 모든 권한 부여·변경·회수 이력은 3년간 보관하며, 보안 감사 시 증빙 자료로 제출한다.',
    '{"tags":["접근권한","RBAC","권한검토","미사용계정","특권권한","감사추적"],"category":"접근관리","doc_category":"보안정책","importance":"high"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- [문서 16] 보안 감사 및 로그 관리
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '보안 감사 및 로그 관리',
    'policy',
    'ko',
    '제1조(로그 수집 대상) (1) 시스템 로그: OS 이벤트, 서비스 시작/중지, 에러. (2) 접근 로그: 로그인/로그아웃, 파일 접근, DB 쿼리. (3) 네트워크 로그: 방화벽, IDS/IPS, VPN 접속. (4) 애플리케이션 로그: 웹서버, API 호출, 에러. (5) 물리 접근 로그: 출입 기록, CCTV. 제2조(로그 보관 기간) (1) 보안 관련 로그: 최소 1년(법적 요구사항에 따라 최대 5년). (2) 일반 시스템 로그: 6개월. (3) CCTV 영상: 30일(보안 사고 시 최대 1년 연장). 제3조(로그 무결성) (1) 로그는 변경 불가능한(immutable) 저장소에 보관한다. (2) 로그 전송 시 암호화(TLS)를 적용하며, 해시값으로 무결성을 검증한다. (3) 로그 삭제·변경 시도는 자동 탐지되어 경고를 발생시킨다. 제4조(감사 주기) (1) 내부 보안 감사: 반기 1회(정보보안팀 주관). (2) 외부 보안 감사: 연 1회(독립 보안 컨설팅 업체). (3) 특별 감사: 보안 사고, 임직원 신고, 규제 기관 요구 시 수시. 제5조(감사 결과) 감사 결과는 경영진에 보고하며, 지적 사항은 30일 이내에 시정 계획을 수립하고 60일 이내에 이행 완료한다.',
    '{"tags":["로그관리","보안감사","SIEM","로그보관","무결성","내부감사","외부감사"],"category":"감사","doc_category":"보안정책","importance":"high"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- [문서 17] 서드파티/협력업체 보안 관리
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '서드파티/협력업체 보안 관리',
    'policy',
    'ko',
    '제1조(보안 요구사항 계약) (1) 당사의 정보 자산에 접근하는 모든 협력업체와 보안 조항을 포함한 계약을 체결한다. (2) 계약 필수 조항: 비밀유지의무(NDA), 개인정보처리위탁 조항, 보안 사고 통보 의무, 감사 권한, 계약 종료 시 데이터 반환·파기. 제2조(접속 통제) (1) 협력업체에게는 업무에 필요한 최소 시스템만 접근을 허용한다(별도 계정, 별도 네트워크 세그먼트). (2) VPN 계정: 프로젝트 기간 한정 발급, 프로젝트 종료 즉시 폐기. (3) 원격 접속 시 MFA 필수, 화면 녹화(감사 목적). 제3조(보안 수준 평가) (1) 계약 전 보안 수준 체크리스트(30개 항목)로 평가한다. (2) 평가 항목: 정보보안 인증(ISMS, ISO 27001), 물리 보안, 인력 관리, 사고 대응 체계. (3) 평가 등급 C 미만인 업체와는 계약을 체결하지 않거나, 보완 조건부로 진행한다. 제4조(정기 감사) 연 1회 주요 협력업체를 대상으로 보안 감사를 실시하며, 미흡 사항 발견 시 30일 이내 시정을 요구한다. 미시정 시 계약 해지 사유가 된다.',
    '{"tags":["협력업체","서드파티","NDA","보안평가","ISMS","접속통제"],"category":"공급망보안","doc_category":"보안정책","importance":"high"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- [문서 18] 소셜 미디어 보안 정책
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '소셜 미디어 보안 정책',
    'policy',
    'ko',
    '제1조(회사 정보 게시 금지) (1) 소셜 미디어(Facebook, Instagram, Twitter/X, LinkedIn, 블로그, 커뮤니티)에 회사 기밀 정보, 미공개 제품 정보, 내부 문서 사진을 게시하는 것을 금지한다. (2) 사무실 내부 사진 촬영·게시 시 화이트보드, 모니터 화면, 문서가 노출되지 않도록 주의한다. (3) 고객사 관련 정보(프로젝트명, 계약 내용, 고객 담당자 이름)를 소셜 미디어에 언급하지 않는다. 제2조(개인 계정 사용 기준) (1) 소셜 미디어에서 회사 소속을 밝히고 의견을 표명할 경우 "개인 의견이며 회사를 대표하지 않음"을 명시한다. (2) 회사의 경쟁사, 고객, 파트너에 대한 부정적 언급을 자제한다. (3) 채용, 투자, 실적 등 미공개 정보를 소셜 미디어에 게시하면 내부자 거래법 위반이 될 수 있다. 제3조(공식 계정 관리) 회사 공식 소셜 미디어 계정은 홍보팀만 운영하며, 게시 전 법무팀·보안팀 검토를 거친다. 제4조(위반 처리) (1) 경미한 위반: 경고 + 게시물 삭제 요청. (2) 중대한 위반(기밀 유출, 악의적 게시): 징계 + 법적 조치.',
    '{"tags":["소셜미디어","SNS","게시금지","개인계정","기밀유출","홍보"],"category":"소셜보안","doc_category":"보안정책","importance":"medium"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- [문서 19] 보안 정책 FAQ
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '보안 정책 FAQ',
    'faq',
    'ko',
    'Q1. 비밀번호를 잊어버렸으면 어떻게 하나요? A1. IT헬프데스크(내선 5555)에 전화하거나 SSO 포털의 "비밀번호 재설정"을 이용하세요. 본인 확인 후 임시 비밀번호를 발급받습니다.
Q2. USB를 꼭 사용해야 하는데 어떻게 하나요? A2. 정보보안팀에 "USB 사용 신청서"를 제출하면 보안 USB를 대여받을 수 있습니다. 일반 USB는 사용 불가합니다.
Q3. 재택근무 시 개인 PC를 사용해도 되나요? A3. MDM 설치 + VPN 사용 조건으로 허용됩니다. 단, 회사 지급 노트북 사용을 권장합니다.
Q4. 피싱 메일을 받았는데 이미 링크를 클릭했습니다. A4. 즉시 정보보안팀(내선 8282)에 신고하고, 비밀번호를 변경하세요. IT팀이 PC를 점검합니다.
Q5. 집에서 공용 Wi-Fi로 접속해도 되나요? A5. 금지입니다. 반드시 모바일 핫스팟(LTE/5G) + VPN으로 접속하세요.
Q6. 소프트웨어를 설치하고 싶은데 목록에 없습니다. A6. IT팀에 "소프트웨어 설치 요청서"를 제출하면 보안 평가 후 승인/반려됩니다.
Q7. 퇴직 후 사내 자료를 사용해도 되나요? A7. 절대 안 됩니다. 퇴직 시 서명한 보안 서약에 따라 2년간 비밀유지 의무가 있으며, 위반 시 법적 조치 대상입니다.
Q8. 보안 교육을 놓쳤는데 어떻게 하나요? A8. LMS에서 온라인 교육을 수강할 수 있습니다. 기한 내 미이수 시 시스템 접근이 제한될 수 있습니다.
Q9. CCTV 영상 열람을 요청할 수 있나요? A9. 정당한 사유(분실물 확인, 사고 확인)가 있는 경우 총무팀에 요청하면 검토 후 제한적으로 열람 가능합니다.
Q10. 회사 메신저로 주고받은 내용도 모니터링되나요? A10. 업무용 메신저(Teams, Slack)의 내용은 보안 감사 목적으로 보관될 수 있으며, 이 사실은 입사 시 고지됩니다.
Q11. Clean Desk 점검에서 위반되면 어떤 불이익이 있나요? A11. 1차 경고, 2차 부서장 통보, 3차 이상 인사 경고 처분됩니다.
Q12. 개인 클라우드(구글 드라이브 등)에 업무 파일을 백업해도 되나요? A12. 금지입니다. 업무 데이터는 회사 승인 클라우드(M365, 사내 파일서버)에만 저장하세요.',
    '{"tags":["보안","FAQ","비밀번호","USB","피싱","재택근무","CleanDesk"],"category":"보안전체","doc_category":"FAQ","importance":"high"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- [문서 20] 개인 정보기기 보안 관리
INSERT INTO tb_docs (tenant_id, title, doc_type, language, content, metadata, embedding, embedding_model, indexed, chunk_index, total_chunks, parent_doc_id, source_type, usage_type, original_content)
VALUES (
    1,
    '개인 정보기기 보안 관리',
    'policy',
    'ko',
    '제1조(스마트폰 업무 활용) (1) 개인 스마트폰으로 사내 이메일, 메신저, 일정을 이용하려면 MDM 앱을 설치하여야 한다. (2) MDM이 관리하는 영역: 업무 앱 컨테이너(이메일, 메신저, 문서 뷰어). 개인 영역(사진, SNS 등)은 관리하지 않는다. (3) 분실 시: 즉시 IT팀에 신고 → 업무 컨테이너만 원격 초기화(개인 데이터는 보존). 제2조(태블릿·노트북) (1) 개인 태블릿으로 업무 문서를 열람하는 것은 MDM 설치 후 허용하되, 극비·비밀 등급 문서는 열람 불가. (2) 개인 노트북의 사내 네트워크 연결은 금지(게스트망 예외). 제3조(웨어러블 기기) (1) 스마트워치의 이메일 알림 기능은 허용하되, 이메일 전문 열람은 차단한다. (2) 보안 구역 내 촬영 기능이 있는 웨어러블 기기(스마트 안경 등) 반입은 금지한다. 제4조(기기 분실 대응) (1) 분실 즉시 IT팀에 신고(업무 시간 외: 비상 연락처). (2) IT팀은 30분 이내에 원격 잠금을 실행하고, 4시간 이내에 상황을 파악한다. (3) 24시간 내 미회수 시 원격 업무 데이터 삭제를 실행한다. 제5조(폐기·교체) 개인 기기 교체 시 기존 기기의 MDM을 해제하고, 업무 데이터가 완전히 삭제되었음을 IT팀에서 확인받는다.',
    '{"tags":["스마트폰","MDM","BYOD","웨어러블","기기분실","원격초기화"],"category":"모바일보안","doc_category":"보안정책","importance":"medium"}',
    NULL, 'text-embedding-3-small', false, 0, 1, NULL, 'sql_import', 'rag_knowledge',
    NULL
);

-- original_content = content 동기화 (INSERT 후 실행)
UPDATE tb_docs SET original_content = content
WHERE source_type = 'sql_import' AND usage_type = 'rag_knowledge' AND original_content IS NULL;
