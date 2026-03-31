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
projects_data = [
    {'name': 'PPR管', 'materials': [
        {'material': 'PPR', 'purchase_price': 10.5, 'selling_price': 15.8, 'stock': 100, 'note': '家装常用水管'},
        {'material': 'PPR加厚', 'purchase_price': 12.5, 'selling_price': 18.8, 'stock': 80, 'note': '工程专用'}
    ]},
    {'name': '弯头', 'materials': [
        {'material': '15国标件', 'purchase_price': 2.5, 'selling_price': 4.8, 'stock': 200, 'note': '水管连接件'},
        {'material': '20国标件', 'purchase_price': 3.5, 'selling_price': 5.8, 'stock': 180, 'note': '大口径'}
    ]},
    {'name': '三通', 'materials': [
        {'material': '20国标件', 'purchase_price': 3.2, 'selling_price': 5.5, 'stock': 150, 'note': '水管分支件'},
        {'material': '25国标件', 'purchase_price': 4.2, 'selling_price': 6.5, 'stock': 120, 'note': '大口径分支'}
    ]},
    {'name': '截止阀', 'materials': [
        {'material': '铜', 'purchase_price': 25.8, 'selling_price': 38.5, 'stock': 50, 'note': '控制水流'},
        {'material': '不锈钢', 'purchase_price': 35.8, 'selling_price': 48.5, 'stock': 30, 'note': '耐腐蚀'}
    ]},
    {'name': '法兰', 'materials': [
        {'material': '不锈钢', 'purchase_price': 45.5, 'selling_price': 68.8, 'stock': 30, 'note': '管道连接'},
        {'material': '碳钢', 'purchase_price': 35.5, 'selling_price': 58.8, 'stock': 40, 'note': '普通管道'}
    ]},
    {'name': '球阀', 'materials': [
        {'material': '铜', 'purchase_price': 18.5, 'selling_price': 28.8, 'stock': 80, 'note': '开关阀门'},
        {'material': '不锈钢', 'purchase_price': 28.5, 'selling_price': 38.8, 'stock': 50, 'note': '耐腐蚀'}
    ]},
    {'name': '水龙头', 'materials': [
        {'material': '铜', 'purchase_price': 35.8, 'selling_price': 58.8, 'stock': 40, 'note': '厨房龙头'},
        {'material': '不锈钢', 'purchase_price': 45.8, 'selling_price': 68.8, 'stock': 30, 'note': '防生锈'}
    ]},
    {'name': '地漏', 'materials': [
        {'material': '不锈钢', 'purchase_price': 15.8, 'selling_price': 25.8, 'stock': 60, 'note': '卫生间排水'},
        {'material': '铜', 'purchase_price': 25.8, 'selling_price': 35.8, 'stock': 40, 'note': '高档地漏'}
    ]},
    {'name': '软管', 'materials': [
        {'material': 'PVC', 'purchase_price': 8.5, 'selling_price': 12.8, 'stock': 120, 'note': '连接软管'},
        {'material': '不锈钢', 'purchase_price': 18.5, 'selling_price': 25.8, 'stock': 80, 'note': '金属软管'}
    ]},
    {'name': '生料带', 'materials': [
        {'material': '聚四氟乙烯', 'purchase_price': 1.2, 'selling_price': 2.5, 'stock': 300, 'note': '密封材料'},
        {'material': '加厚型', 'purchase_price': 1.8, 'selling_price': 3.5, 'stock': 200, 'note': '优质密封'}
    ]}
]

# 插入测试项目和材质
def insert_projects():
    inserted_projects = 0
    inserted_materials = 0
    
    for project in projects_data:
        # 检查项目是否已存在
        cursor.execute("""
            SELECT id FROM projects WHERE name = %s AND is_deleted = 0
        """, (project['name'],))
        existing_project = cursor.fetchone()
        
        if existing_project:
            print(f"项目 '{project['name']}' 已存在，跳过")
            project_id = existing_project[0]
        else:
            # 插入项目
            cursor.execute("""
                INSERT INTO projects (name, is_deleted)
                VALUES (%s, 0)
            """, (project['name'],))
            project_id = cursor.lastrowid
            inserted_projects += 1
        
        # 插入材质
        for material in project['materials']:
            # 检查材质是否已存在
            cursor.execute("""
                SELECT id FROM materials 
                WHERE project_id = %s AND material = %s AND is_deleted = 0
            """, (project_id, material['material']))
            existing_material = cursor.fetchone()
            
            if existing_material:
                print(f"材质 '{material['material']}' 已存在，跳过")
            else:
                cursor.execute("""
                    INSERT INTO materials 
                    (project_id, material, purchase_price, selling_price, stock, note, is_deleted, source)
                    VALUES (%s, %s, %s, %s, %s, %s, 0, 'system')
                """, (
                    project_id,
                    material['material'],
                    material['purchase_price'],
                    material['selling_price'],
                    material['stock'],
                    material['note']
                ))
                inserted_materials += 1
    
    conn.commit()
    print(f"插入了 {inserted_projects} 个测试项目，共 {inserted_materials} 个材质")

# 生成测试订单数据
customer_names = [
    '张三', '李四', '王五', '赵六', '钱七', 
    '孙八', '周九', '吴十', '郑一', '王二'
]

order_notes = [
    '常规采购', '紧急订单', '工程需求', '家庭装修', '更换配件',
    '批量采购', '零售客户', '长期合作', '新客户', '老客户'
]

# 获取所有材质ID（兼容旧系统）
def get_material_ids():
    cursor.execute("SELECT id, project_id FROM materials WHERE is_deleted = 0")
    return cursor.fetchall()

# 生成测试订单
def insert_orders():
    materials = get_material_ids()
    if not materials:
        print("没有可用的材质，请先插入项目数据")
        return
    
    order_count = 20  # 生成20个测试订单
    for i in range(order_count):
        # 生成订单
        customer_name = random.choice(customer_names)
        note = random.choice(order_notes)
        phone = f"138{random.randint(10000000, 99999999)}"
        
        # 计算订单总金额（先临时设为0，后续更新）
        total_amount = 0
        paid_amount = random.choice([total_amount * 0.5, total_amount * 0.8, total_amount, None])
        is_paid = 1 if paid_amount else 0
        
        # 插入订单
        cursor.execute("""
            INSERT INTO orders (customer_name, phone, note, total_amount, paid_amount, is_paid)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (customer_name, phone, note, total_amount, paid_amount, is_paid))
        order_id = cursor.lastrowid
        
        # 为每个订单添加2-5个项目
        item_count = random.randint(2, 5)
        for _ in range(item_count):
            material_id, project_id = random.choice(materials)
            # 获取材质信息
            cursor.execute("""
                SELECT m.material, m.purchase_price, m.selling_price, m.note, p.name 
                FROM materials m
                JOIN projects p ON m.project_id = p.id
                WHERE m.id = %s
            """, (material_id,))
            material_info = cursor.fetchone()
            if material_info:
                material_name, purchase_price, selling_price, material_note, project_name = material_info
                quantity = random.randint(1, 10)
                price = selling_price * quantity
                
                # 插入订单项目
                cursor.execute("""
                    INSERT INTO order_items 
                    (order_id, name, material, purchase_price, selling_price, note, quantity, price)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    order_id, project_name, material_name, 
                    purchase_price, selling_price, material_note, 
                    quantity, price
                ))
                
                # 累加订单总金额
                total_amount += price
        
        # 更新订单总金额和支付状态
        if total_amount > 0:
            paid_amount = random.choice([float(total_amount) * 0.5, float(total_amount) * 0.8, total_amount, None])
        else:
            paid_amount = None
        is_paid = 1 if paid_amount else 0
        cursor.execute("""
            UPDATE orders SET total_amount = %s, paid_amount = %s, is_paid = %s WHERE id = %s
        """, (total_amount, paid_amount, is_paid, order_id))
    
    conn.commit()
    print(f"生成了 {order_count} 个测试订单")

# 主函数
def main():
    print("开始生成测试数据...")
    try:
        insert_projects()
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
