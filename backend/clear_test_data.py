from db import get_db_connection

# 清空测试数据
def clear_test_data():
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            print("开始清空测试数据...")
            
            # 1. 清空订单项目表（子表）
            cursor.execute('DELETE FROM order_items')
            print("已清空 order_items 表")
            
            # 2. 清空订单表（父表）
            cursor.execute('DELETE FROM orders')
            print("已清空 orders 表")
            
            # 3. 清空材质表
            cursor.execute('DELETE FROM materials')
            print("已清空 materials 表")
            
            # 4. 清空项目表
            cursor.execute('DELETE FROM projects')
            print("已清空 projects 表")
            
            # 5. 清空旧的项目表
            cursor.execute('DELETE FROM items')
            print("已清空 items 表")
            
            # 提交事务
            connection.commit()
            print("\n✅ 测试数据清空成功！")
            
    except Exception as e:
        print(f"❌ 清空测试数据失败: {e}")
        connection.rollback()
    finally:
        connection.close()

if __name__ == '__main__':
    clear_test_data()
