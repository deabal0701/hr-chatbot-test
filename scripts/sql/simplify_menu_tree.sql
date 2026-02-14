-- ============================================================
-- 메뉴 트리 단순화 마이그레이션
-- 3개 DIRECTORY 루트 (ADMIN, USER_AREA, API_ACCESS) 제거
-- 모든 PAGE/API 메뉴를 루트 레벨(depth=0)로 승격
--
-- 실행: psql -h 115.68.223.220 -U hermesuser -d hermesdb -f simplify_menu_tree.sql
-- ============================================================

BEGIN;

-- Step 1: 모든 PAGE/API 메뉴를 루트(depth=0)로 승격
UPDATE tb_menu
SET parent_menu_id = NULL,
    depth = 0,
    updated_at = NOW()
WHERE menu_type IN ('PAGE', 'API')
  AND parent_menu_id IS NOT NULL;

-- Step 2: DIRECTORY 메뉴의 사용자 권한 삭제
DELETE FROM tb_user_menu
WHERE menu_id IN (
    SELECT menu_id FROM tb_menu WHERE menu_code IN ('ADMIN', 'USER_AREA', 'API_ACCESS')
);

-- Step 3: 3개 DIRECTORY 루트 삭제
DELETE FROM tb_menu
WHERE menu_code IN ('ADMIN', 'USER_AREA', 'API_ACCESS');

-- Step 4: sort_order 재정렬 (PAGE 먼저, API 뒤)
WITH ranked AS (
    SELECT menu_id,
           ROW_NUMBER() OVER (ORDER BY
               CASE menu_type WHEN 'PAGE' THEN 0 WHEN 'API' THEN 1 ELSE 2 END,
               sort_order
           ) AS new_sort
    FROM tb_menu
    WHERE parent_menu_id IS NULL
)
UPDATE tb_menu m
SET sort_order = r.new_sort,
    updated_at = NOW()
FROM ranked r
WHERE m.menu_id = r.menu_id;

COMMIT;

-- 확인 쿼리
-- SELECT menu_id, menu_code, menu_name, menu_type, parent_menu_id, depth, sort_order
-- FROM tb_menu ORDER BY sort_order;
