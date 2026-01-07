"""Phase 3 Cleanup Script - Remove unnecessary settings"""
import sys
sys.path.insert(0, '.')

from app.utils.database import db_manager

def main():
    print('=== Executing Phase 3 Cleanup ===')
    print()

    # 1. Remove embedding.provider (unnecessary - only OpenAI supports embeddings)
    print('1. Removing embedding.provider setting...')
    with db_manager.get_cursor(commit=True) as cur:
        cur.execute("DELETE FROM app_settings WHERE category = 'embedding' AND key = 'provider'")
        deleted_count = cur.rowcount
        print(f'   Deleted {deleted_count} row(s)')
    print()

    # 2. Verify current provider settings
    print('2. Current provider settings:')
    with db_manager.get_cursor() as cur:
        cur.execute("""
            SELECT category, key, value, description
            FROM app_settings
            WHERE key LIKE '%provider%'
            ORDER BY category, key
        """)
        for row in cur.fetchall():
            print(f'   {row[0]}.{row[1]} = {row[2]}')
            print(f'      Description: {row[3]}')
    print()

    # 3. Show all settings summary
    print('3. All settings by category:')
    with db_manager.get_cursor() as cur:
        cur.execute("""
            SELECT
                category,
                COUNT(*) as setting_count,
                COUNT(CASE WHEN is_secret THEN 1 END) as secret_count
            FROM app_settings
            GROUP BY category
            ORDER BY category
        """)
        for row in cur.fetchall():
            print(f'   {row[0]}: {row[1]} settings ({row[2]} secret)')

    print()
    print('=== Cleanup Complete ===')

if __name__ == '__main__':
    main()
