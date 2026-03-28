import mysql.connector
import random
from datetime import datetime

# 数据库连接信息
config = {
    'user': 'xiaoshouxitong',
    'password': '55p3knrBYPs8XJew',
    'host': '101.42.35.88',
    'database': 'xiaoshouxitong',
    'port': 3306
}

# 连接数据库
conn = mysql.connector.connect(**config)
cursor = conn.cursor()

# 生成测试项目数据
items_data = [
    {'name': 'PPR管', 'material': 'PPR', 'purchase_price': 10.5, 'selling_price': 15.8, 'stock': 100, 'note': '家装常用水管'},  
    {'name': '弯头', 'material': '15国标件', 'purchase_price': 2.5, 'selling_price': 4.8, 'stock': 200, 'note': '水管连接件'},  
    {'name': '三通', 'material': '20国标件', 'purchase_price': 3.2, 'selling_price': 5.5, 'stock': 150, 'note': '水管分支件'},  
    {'name': '截止阀', 'material': '铜', 'purchase_price': 25.8, 'selling_price': 38.5, 'stock': 50, 'note': '控制水流'},  
    {'name': '法兰', 'material': '不锈钢', 'purchase_price': 45.5, 'selling_price': 68.8, 'stock': 30, 'note': '管道连接'},  
    {'name': '球阀', 'material': '铜', 'purchase_price': 18.5, 'selling_price': 28.8, 'stock': 80, 'note': '开关阀门'},  
    {'name': '水龙头', 'material': '铜', 'purchase_price': 35.8, 'selling_price': 58.8, 'stock': 40, 'note': '厨房龙头'},  
    {'name': '地漏', 'material': '不锈钢', 'purchase_price': 15.8, 'selling_price': 25.8, 'stock': 60, 'note': '卫生间排水'},  
    {'name': '软管', 'material': 'PVC', 'purchase_price': 8.5, 'selling_price': 12.8, 'stock': 120, 'note': '连接软管'},  
    {'name': '生料带', 'material': '聚四氟乙烯', 'purchase_price': 1.2, 'selling_price': 2.5, 'stock': 300, 'note': '密封材料'}
]

# 插入测试项目
def insert_items():
    for item in items_data:
        sql = """
        INSERT INTO items (name, material, purchase_price, selling_price, stock, note, is_deleted, source)
        VALUES (%s, %s, %s, %s, %s, %s, 0, 'system')
        """
        values = (
            item['name'],
            item['material'],
            item['purchase_price'],
            item['selling_price'],
            item['stock'],
            item['note']
        )
        cursor.execute(sql, values)
    conn.commit()
    print(f"插入了 {len(items_data)} 个测试项目")

# 生成测试订单数据
customer_names = [
    '张三', '李四', '王五', '赵六', '钱七', 
    '孙八', '周九', '吴十', '郑一', '王二'
]

order_notes = [
    '常规采购', '紧急订单', '工程需求', '家庭装修', '更换配件',
    '批量采购', '零售客户', '长期合作', '新客户', '老客户'
]

# 获取所有项目ID
def get_item_ids():
    cursor.execute("SELECT id FROM items WHERE is_deleted = 0")
    return [row[0] for row in cursor.fetchall()]

# 生成测试订单
def insert_orders():
    item_ids = get_item_ids()
    if not item_ids:
        print("没有可用的项目，请先插入项目数据")
        return
    
    order_count = 20  # 生成20个测试订单
    for i in range(order_count):
        # 生成订单
        customer_name = random.choice(customer_names)
        note = random.choice(order_notes)
        
        # 计算订单总金额（先临时设为0，后续更新）
        total_amount = 0
        
        # 插入订单
        cursor.execute("""
            INSERT INTO orders (customer_name, note, total_amount)
            VALUES (%s, %s, %s)
        """, (customer_name, note, total_amount))
        order_id = cursor.lastrowid
        
        # 为每个订单添加2-5个项目
        item_count = random.randint(2, 5)
        for _ in range(item_count):
            item_id = random.choice(item_ids)
            # 获取项目信息
            cursor.execute("""
                SELECT name, material, purchase_price, selling_price, note 
                FROM items WHERE id = %s
            """, (item_id,))
            item_info = cursor.fetchone()
            if item_info:
                name, material, purchase_price, selling_price, item_note = item_info
                quantity = random.randint(1, 10)
                price = selling_price * quantity
                
                # 插入订单项目
                cursor.execute("""
                    INSERT INTO order_items 
                    (order_id, item_id, name, material, purchase_price, selling_price, note, quantity, price)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    order_id, item_id, name, material, 
                    purchase_price, selling_price, item_note, 
                    quantity, price
                ))
                
                # 累加订单总金额
                total_amount += price
        
        # 更新订单总金额
        cursor.execute("""
            UPDATE orders SET total_amount = %s WHERE id = %s
        """, (total_amount, order_id))
    
    conn.commit()
    print(f"生成了 {order_count} 个测试订单")

# 主函数
def main():
    print("开始生成测试数据...")
    try:
        insert_items()
        insert_orders()
        print("测试数据生成完成！")
    except Exception as e:
        print(f"发生错误: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    main()
