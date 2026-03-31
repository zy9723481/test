"""
数据库迁移脚本：添加 paid_at 字段到 orders 表
"""
from db import get_db_connection

def migrate():
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            print("开始数据库迁移...")
            
            # 检查 paid_at 字段是否已存在
            cursor.execute("""
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = 'orders' AND COLUMN_NAME = 'paid_at'
            """)
            
            if cursor.fetchone():
                print("✓ paid_at 字段已存在，跳过")
            else:
                # 添加 paid_at 字段
                cursor.execute("""
                    ALTER TABLE orders 
                    ADD COLUMN paid_at TIMESTAMP NULL COMMENT '结账时间'
                """)
                print("✓ 成功添加 paid_at 字段")
            
            # 为已结账的订单设置 paid_at 时间（如果没有的话）
            cursor.execute("""
                UPDATE orders 
                SET paid_at = created_at 
                WHERE is_paid = 1 AND paid_at IS NULL
            """)
            updated_rows = cursor.rowcount
            print(f"✓ 已更新 {updated_rows} 条已结账订单的 paid_at 时间")
            
            connection.commit()
            print("\n✅ 数据库迁移完成！")
            
    except Exception as e:
        print(f"\n❌ 迁移失败: {e}")
        connection.rollback()
        raise
    finally:
        connection.close()

if __name__ == '__main__':
    migrate()
