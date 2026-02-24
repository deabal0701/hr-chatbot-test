-- ============================================================
-- A테넌트(tenant_id=2) 샘플 조직 데이터 (본부→부서→팀→파트)
-- 실행 전: SELECT * FROM tb_department WHERE tenant_id = 2;
-- 롤백:   DELETE FROM tb_department WHERE tenant_id = 2;
-- ============================================================

BEGIN;

-- ── depth 0: 본부 (3개) ──
INSERT INTO tb_department (tenant_id, parent_dept_id, dept_code, dept_name, depth, sort_order)
VALUES
  (2, NULL, 'HQ_MGMT',  '경영본부', 0, 1),
  (2, NULL, 'HQ_DEV',   '개발본부', 0, 2),
  (2, NULL, 'HQ_SALES', '영업본부', 0, 3);

-- ── depth 1: 부서 (6개) ──
INSERT INTO tb_department (tenant_id, parent_dept_id, dept_code, dept_name, depth, sort_order)
VALUES
  (2, (SELECT dept_id FROM tb_department WHERE tenant_id=2 AND dept_code='HQ_MGMT'),
      'DEPT_HR',      '인사부',     1, 1),
  (2, (SELECT dept_id FROM tb_department WHERE tenant_id=2 AND dept_code='HQ_MGMT'),
      'DEPT_FIN',     '재무부',     1, 2),
  (2, (SELECT dept_id FROM tb_department WHERE tenant_id=2 AND dept_code='HQ_MGMT'),
      'DEPT_GA',      '총무부',     1, 3),
  (2, (SELECT dept_id FROM tb_department WHERE tenant_id=2 AND dept_code='HQ_DEV'),
      'DEPT_DEV1',    '개발1부',    1, 1),
  (2, (SELECT dept_id FROM tb_department WHERE tenant_id=2 AND dept_code='HQ_DEV'),
      'DEPT_DEV2',    '개발2부',    1, 2),
  (2, (SELECT dept_id FROM tb_department WHERE tenant_id=2 AND dept_code='HQ_SALES'),
      'DEPT_DOM',     '국내영업부', 1, 1),
  (2, (SELECT dept_id FROM tb_department WHERE tenant_id=2 AND dept_code='HQ_SALES'),
      'DEPT_GLB',     '해외영업부', 1, 2);

-- ── depth 2: 팀 (9개) ──
INSERT INTO tb_department (tenant_id, parent_dept_id, dept_code, dept_name, depth, sort_order)
VALUES
  (2, (SELECT dept_id FROM tb_department WHERE tenant_id=2 AND dept_code='DEPT_HR'),
      'TEAM_HR1',     '인사팀',       2, 1),
  (2, (SELECT dept_id FROM tb_department WHERE tenant_id=2 AND dept_code='DEPT_HR'),
      'TEAM_EDU',     '교육팀',       2, 2),
  (2, (SELECT dept_id FROM tb_department WHERE tenant_id=2 AND dept_code='DEPT_FIN'),
      'TEAM_ACC',     '회계팀',       2, 1),
  (2, (SELECT dept_id FROM tb_department WHERE tenant_id=2 AND dept_code='DEPT_DEV1'),
      'TEAM_FE',      '프론트엔드팀', 2, 1),
  (2, (SELECT dept_id FROM tb_department WHERE tenant_id=2 AND dept_code='DEPT_DEV1'),
      'TEAM_BE',      '백엔드팀',     2, 2),
  (2, (SELECT dept_id FROM tb_department WHERE tenant_id=2 AND dept_code='DEPT_DEV2'),
      'TEAM_AI',      'AI팀',         2, 1),
  (2, (SELECT dept_id FROM tb_department WHERE tenant_id=2 AND dept_code='DEPT_DEV2'),
      'TEAM_DATA',    '데이터팀',     2, 2),
  (2, (SELECT dept_id FROM tb_department WHERE tenant_id=2 AND dept_code='DEPT_DOM'),
      'TEAM_SALE1',   '영업1팀',      2, 1),
  (2, (SELECT dept_id FROM tb_department WHERE tenant_id=2 AND dept_code='DEPT_GLB'),
      'TEAM_SALE2',   '영업2팀',      2, 1);

-- ── depth 3: 파트 (4개) ──
INSERT INTO tb_department (tenant_id, parent_dept_id, dept_code, dept_name, depth, sort_order)
VALUES
  (2, (SELECT dept_id FROM tb_department WHERE tenant_id=2 AND dept_code='TEAM_FE'),
      'PART_UI',      'UI파트',   3, 1),
  (2, (SELECT dept_id FROM tb_department WHERE tenant_id=2 AND dept_code='TEAM_FE'),
      'PART_UX',      'UX파트',   3, 2),
  (2, (SELECT dept_id FROM tb_department WHERE tenant_id=2 AND dept_code='TEAM_BE'),
      'PART_API',     'API파트',  3, 1),
  (2, (SELECT dept_id FROM tb_department WHERE tenant_id=2 AND dept_code='TEAM_BE'),
      'PART_DB',      'DB파트',   3, 2);

COMMIT;

COMMIT;

-- ============================================================
-- B테넌트(tenant_id=5) 샘플 조직 데이터 (본부→팀, 8개)
-- 기존 데이터 교체: 먼저 tb_user.dept_id NULL 처리 후 삭제
-- 롤백: 수동 복원 필요
-- ============================================================

BEGIN;

-- 기존 B테넌트 부서 참조 해제 및 삭제
UPDATE tb_user SET dept_id = NULL WHERE dept_id IN (SELECT dept_id FROM tb_department WHERE tenant_id = 5);
DELETE FROM tb_department WHERE tenant_id = 5;

-- depth 0: 본부 (2개)
INSERT INTO tb_department (tenant_id, parent_dept_id, dept_code, dept_name, depth, sort_order)
VALUES
  (5, NULL, 'B_HQ_PROD',  '생산본부', 0, 1),
  (5, NULL, 'B_HQ_MGMT',  '관리본부', 0, 2);

-- depth 1: 부서 (3개)
INSERT INTO tb_department (tenant_id, parent_dept_id, dept_code, dept_name, depth, sort_order)
VALUES
  (5, (SELECT dept_id FROM tb_department WHERE tenant_id=5 AND dept_code='B_HQ_PROD'),
      'B_DEPT_MFG',   '제조부',   1, 1),
  (5, (SELECT dept_id FROM tb_department WHERE tenant_id=5 AND dept_code='B_HQ_PROD'),
      'B_DEPT_QA',    '품질부',   1, 2),
  (5, (SELECT dept_id FROM tb_department WHERE tenant_id=5 AND dept_code='B_HQ_MGMT'),
      'B_DEPT_ADM',   '경영지원부', 1, 1);

-- depth 2: 팀 (3개)
INSERT INTO tb_department (tenant_id, parent_dept_id, dept_code, dept_name, depth, sort_order)
VALUES
  (5, (SELECT dept_id FROM tb_department WHERE tenant_id=5 AND dept_code='B_DEPT_MFG'),
      'B_TEAM_MFG1',  '제조1팀',   2, 1),
  (5, (SELECT dept_id FROM tb_department WHERE tenant_id=5 AND dept_code='B_DEPT_QA'),
      'B_TEAM_QA1',   '검사팀',    2, 1),
  (5, (SELECT dept_id FROM tb_department WHERE tenant_id=5 AND dept_code='B_DEPT_ADM'),
      'B_TEAM_HR',    '인사총무팀', 2, 1);

COMMIT;

-- ============================================================
-- C테넌트(tenant_id=6) 샘플 조직 데이터 (본부→팀, 7개)
-- 롤백: DELETE FROM tb_department WHERE tenant_id = 6;
-- ============================================================

BEGIN;

-- depth 0: 본부 (2개)
INSERT INTO tb_department (tenant_id, parent_dept_id, dept_code, dept_name, depth, sort_order)
VALUES
  (6, NULL, 'C_HQ_BIZ',   '사업본부', 0, 1),
  (6, NULL, 'C_HQ_TECH',  '기술본부', 0, 2);

-- depth 1: 부서 (3개)
INSERT INTO tb_department (tenant_id, parent_dept_id, dept_code, dept_name, depth, sort_order)
VALUES
  (6, (SELECT dept_id FROM tb_department WHERE tenant_id=6 AND dept_code='C_HQ_BIZ'),
      'C_DEPT_MKT',   '마케팅부', 1, 1),
  (6, (SELECT dept_id FROM tb_department WHERE tenant_id=6 AND dept_code='C_HQ_BIZ'),
      'C_DEPT_CS',    '고객지원부', 1, 2),
  (6, (SELECT dept_id FROM tb_department WHERE tenant_id=6 AND dept_code='C_HQ_TECH'),
      'C_DEPT_RND',   '연구개발부', 1, 1);

-- depth 2: 팀 (2개)
INSERT INTO tb_department (tenant_id, parent_dept_id, dept_code, dept_name, depth, sort_order)
VALUES
  (6, (SELECT dept_id FROM tb_department WHERE tenant_id=6 AND dept_code='C_DEPT_MKT'),
      'C_TEAM_DIG',   '디지털마케팅팀', 2, 1),
  (6, (SELECT dept_id FROM tb_department WHERE tenant_id=6 AND dept_code='C_DEPT_RND'),
      'C_TEAM_LAB',   '기술연구팀',     2, 1);

COMMIT;

-- ============================================================
-- 전체 확인 쿼리
-- ============================================================
SELECT t.tenant_name, d.dept_id, d.parent_dept_id, d.dept_code, d.dept_name, d.depth, d.sort_order
FROM tb_department d
JOIN tb_tenant t ON t.tenant_id = d.tenant_id
WHERE d.tenant_id IN (2, 5, 6)
ORDER BY d.tenant_id, d.depth, d.sort_order, d.dept_id;
