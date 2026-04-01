"""
数据库迁移脚本：为order_items表添加人工费和系统项目标识字段
"""
from db import get_db_connection

def migrate():
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            print("开始数据库迁移...")
            
            # 检查is_labor_fee字段是否已存在
            cursor.execute("""
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = 'order_items' AND COLUMN_NAME = 'is_labor_fee'
            """)
            
            if not cursor.fetchone():
                # 添加is_labor_fee字段
                cursor.execute("""
                    ALTER TABLE order_items 
                    ADD COLUMN is_labor_fee TINYINT(1) DEFAULT 0 COMMENT '是否为人工费项目'
                """)
                print("✓ 成功添加 is_labor_fee 字段")
            else:
                print("✓ is_labor_fee 字段已存在，跳过")
            
            # 检查is_system_item字段是否已存在
            cursor.execute("""
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = 'order_items' AND COLUMN_NAME = 'is_system_item'
            """)
            
            if not cursor.fetchone():
                # 添加is_system_item字段
                cursor.execute("""
                    ALTER TABLE order_items 
                    ADD COLUMN is_system_item TINYINT(1) DEFAULT 0 COMMENT '是否为系统项目'
                """)
                print("✓ 成功添加 is_system_item 字段")
            else:
                print("✓ is_system_item 字段已存在，跳过")
            
            # 为现有记录设置默认值
            cursor.execute("""
                UPDATE order_items 
                SET is_labor_fee = 0 
                WHERE is_labor_fee IS NULL
            """)
            cursor.execute("""
                UPDATE order_items 
                SET is_system_item = 0 
                WHERE is_system_item IS NULL
            """)
            print("✓ 已为现有记录设置默认值")
            
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
