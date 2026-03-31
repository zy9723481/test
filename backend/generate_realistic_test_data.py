import mysql.connector
import random
from datetime import datetime, timedelta

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

# 真实的水暖管件产品数据
projects_data = [
    {
        'name': 'PPR冷水管',
        'materials': [
            {'material': '20*2.0mm', 'purchase_price': 8.50, 'selling_price': 12.80, 'stock': 500, 'note': '家装常用，耐压1.0MPa'},
            {'material': '25*2.3mm', 'purchase_price': 12.50, 'selling_price': 18.80, 'stock': 400, 'note': '工程专用，耐压1.25MPa'},
            {'material': '32*2.9mm', 'purchase_price': 18.50, 'selling_price': 28.00, 'stock': 300, 'note': '大流量管道'},
            {'material': '40*3.7mm', 'purchase_price': 28.50, 'selling_price': 42.00, 'stock': 200, 'note': '主管道使用'}
        ]
    },
    {
        'name': 'PPR热水管',
        'materials': [
            {'material': '20*2.8mm', 'purchase_price': 12.50, 'selling_price': 18.80, 'stock': 450, 'note': '耐高温70°C'},
            {'material': '25*3.5mm', 'purchase_price': 18.50, 'selling_price': 28.00, 'stock': 350, 'note': '耐高温95°C'},
            {'material': '32*4.4mm', 'purchase_price': 28.50, 'selling_price': 42.00, 'stock': 250, 'note': '工程专用热水管'}
        ]
    },
    {
        'name': '90°弯头',
        'materials': [
            {'material': '20mm', 'purchase_price': 1.20, 'selling_price': 2.50, 'stock': 1000, 'note': '等径弯头'},
            {'material': '25mm', 'purchase_price': 1.80, 'selling_price': 3.50, 'stock': 800, 'note': '等径弯头'},
            {'material': '32mm', 'purchase_price': 3.20, 'selling_price': 5.80, 'stock': 600, 'note': '等径弯头'},
            {'material': '20*25mm', 'purchase_price': 1.50, 'selling_price': 3.00, 'stock': 500, 'note': '异径弯头'}
        ]
    },
    {
        'name': '等径三通',
        'materials': [
            {'material': '20mm', 'purchase_price': 1.50, 'selling_price': 3.00, 'stock': 800, 'note': 'T型三通'},
            {'material': '25mm', 'purchase_price': 2.20, 'selling_price': 4.50, 'stock': 700, 'note': 'T型三通'},
            {'material': '32mm', 'purchase_price': 4.50, 'selling_price': 8.00, 'stock': 500, 'note': 'T型三通'}
        ]
    },
    {
        'name': '内丝直接',
        'materials': [
            {'material': '20*1/2"', 'purchase_price': 3.50, 'selling_price': 6.80, 'stock': 600, 'note': '内螺纹连接'},
            {'material': '25*3/4"', 'purchase_price': 5.50, 'selling_price': 10.00, 'stock': 500, 'note': '内螺纹连接'},
            {'material': '32*1"', 'purchase_price': 8.50, 'selling_price': 15.00, 'stock': 400, 'note': '内螺纹连接'}
        ]
    },
    {
        'name': '外丝直接',
        'materials': [
            {'material': '20*1/2"', 'purchase_price': 3.20, 'selling_price': 6.50, 'stock': 600, 'note': '外螺纹连接'},
            {'material': '25*3/4"', 'purchase_price': 5.20, 'selling_price': 9.50, 'stock': 500, 'note': '外螺纹连接'},
            {'material': '32*1"', 'purchase_price': 8.20, 'selling_price': 14.50, 'stock': 400, 'note': '外螺纹连接'}
        ]
    },
    {
        'name': '截止阀',
        'materials': [
            {'material': '20mm铜芯', 'purchase_price': 15.80, 'selling_price': 28.00, 'stock': 200, 'note': '升降式截止阀'},
            {'material': '25mm铜芯', 'purchase_price': 22.50, 'selling_price': 38.00, 'stock': 180, 'note': '升降式截止阀'},
            {'material': '32mm铜芯', 'purchase_price': 35.00, 'selling_price': 58.00, 'stock': 150, 'note': '升降式截止阀'}
        ]
    },
    {
        'name': '球阀',
        'materials': [
            {'material': '20mm铜球', 'purchase_price': 12.50, 'selling_price': 22.00, 'stock': 300, 'note': '快开球阀'},
            {'material': '25mm铜球', 'purchase_price': 18.00, 'selling_price': 32.00, 'stock': 250, 'note': '快开球阀'},
            {'material': '32mm铜球', 'purchase_price': 28.00, 'selling_price': 48.00, 'stock': 200, 'note': '快开球阀'}
        ]
    },
    {
        'name': '冷热混水阀',
        'materials': [
            {'material': '全铜单孔', 'purchase_price': 85.00, 'selling_price': 158.00, 'stock': 80, 'note': '面盆龙头'},
            {'material': '全铜双孔', 'purchase_price': 120.00, 'selling_price': 228.00, 'stock': 60, 'note': '厨房龙头'},
            {'material': '不锈钢单孔', 'purchase_price': 65.00, 'selling_price': 118.00, 'stock': 100, 'note': '经济型面盆龙头'}
        ]
    },
    {
        'name': '花洒套装',
        'materials': [
            {'material': '三档增压', 'purchase_price': 180.00, 'selling_price': 358.00, 'stock': 50, 'note': '手持+顶喷'},
            {'material': '四档恒温', 'purchase_price': 450.00, 'selling_price': 888.00, 'stock': 30, 'note': '恒温控制'},
            {'material': '简易手持', 'purchase_price': 45.00, 'selling_price': 88.00, 'stock': 150, 'note': '单手持花洒'}
        ]
    },
    {
        'name': '地漏',
        'materials': [
            {'material': '不锈钢10*10', 'purchase_price': 12.50, 'selling_price': 25.00, 'stock': 200, 'note': '普通地漏'},
            {'material': '不锈钢15*15', 'purchase_price': 18.50, 'selling_price': 35.00, 'stock': 150, 'note': '大排量地漏'},
            {'material': '全铜防臭', 'purchase_price': 35.00, 'selling_price': 68.00, 'stock': 100, 'note': '深水封防臭'},
            {'material': '隐形地漏', 'purchase_price': 45.00, 'selling_price': 88.00, 'stock': 80, 'note': '可镶嵌瓷砖'}
        ]
    },
    {
        'name': '角阀',
        'materials': [
            {'material': '铜芯4分', 'purchase_price': 8.50, 'selling_price': 15.00, 'stock': 300, 'note': '马桶/面盆专用'},
            {'material': '铜芯6分', 'purchase_price': 12.00, 'selling_price': 22.00, 'stock': 200, 'note': '热水器专用'},
            {'material': '不锈钢4分', 'purchase_price': 5.50, 'selling_price': 10.00, 'stock': 400, 'note': '经济型'}
        ]
    },
    {
        'name': '软管',
        'materials': [
            {'material': '30cm不锈钢', 'purchase_price': 4.50, 'selling_price': 8.00, 'stock': 500, 'note': '波纹管'},
            {'material': '40cm不锈钢', 'purchase_price': 5.50, 'selling_price': 10.00, 'stock': 400, 'note': '波纹管'},
            {'material': '50cm不锈钢', 'purchase_price': 6.50, 'selling_price': 12.00, 'stock': 350, 'note': '波纹管'},
            {'material': 'PVC进水管', 'purchase_price': 3.50, 'selling_price': 6.50, 'stock': 600, 'note': '马桶进水管'}
        ]
    },
    {
        'name': '生料带',
        'materials': [
            {'material': '普通型15米', 'purchase_price': 0.80, 'selling_price': 2.00, 'stock': 1000, 'note': '聚四氟乙烯'},
            {'material': '加厚型20米', 'purchase_price': 1.20, 'selling_price': 3.00, 'stock': 800, 'note': '优质密封'},
            {'material': '液体生料带', 'purchase_price': 8.50, 'selling_price': 18.00, 'stock': 200, 'note': '厌氧胶密封'}
        ]
    },
    {
        'name': '管卡',
        'materials': [
            {'material': '20mm吊卡', 'purchase_price': 0.30, 'selling_price': 0.80, 'stock': 2000, 'note': 'PPR管固定'},
            {'material': '25mm吊卡', 'purchase_price': 0.40, 'selling_price': 1.00, 'stock': 1500, 'note': 'PPR管固定'},
            {'material': '32mm吊卡', 'purchase_price': 0.50, 'selling_price': 1.20, 'stock': 1000, 'note': 'PPR管固定'}
        ]
    }
]

# 真实的客户名称
customer_names = [
    '王建国', '李秀英', '张伟', '刘洋', '陈明',
    '杨华', '赵强', '黄丽', '周杰', '吴敏',
    '徐鹏', '孙丽', '马军', '朱婷', '胡磊',
    '郭静', '林峰', '何欣', '高飞', '梁雨',
    '宋阳', '郑浩', '谢薇', '韩冰', '唐勇',
    '冯雪', '董洋', '萧红', '程亮', '曹颖'
]

# 真实的订单备注
order_notes = [
    '新房装修，全套水管',
    '卫生间改造',
    '厨房水路改造',
    '漏水维修更换',
    '太阳能热水器安装',
    '地暖分水器更换',
    '增压泵安装配套',
    '净水器安装预留',
    '旧房翻新改造',
    '商铺装修用水',
    '出租房简装',
    '别墅全屋水路',
    '工厂车间用水',
    '办公楼改造',
    '酒店客房装修'
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
            print(f"✓ 插入项目: {project['name']}")
        
        # 插入材质
        for material in project['materials']:
            # 检查材质是否已存在
            cursor.execute("""
                SELECT id FROM materials 
                WHERE project_id = %s AND material = %s AND is_deleted = 0
            """, (project_id, material['material']))
            existing_material = cursor.fetchone()
            
            if existing_material:
                print(f"  材质 '{material['material']}' 已存在，跳过")
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
                print(f"  ✓ 插入材质: {material['material']} ¥{material['selling_price']}")
    
    conn.commit()
    print(f"\n✅ 共插入 {inserted_projects} 个项目，{inserted_materials} 个材质")

# 获取所有材质详细信息
def get_all_materials():
    cursor.execute("""
        SELECT m.id, m.material, m.purchase_price, m.selling_price, p.name as project_name
        FROM materials m
        JOIN projects p ON m.project_id = p.id
        WHERE m.is_deleted = 0 AND p.is_deleted = 0
    """)
    return cursor.fetchall()

# 生成随机日期（最近3个月内）
def get_random_date():
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)
    random_date = start_date + timedelta(
        seconds=random.randint(0, int((end_date - start_date).total_seconds()))
    )
    return random_date

# 生成测试订单
def insert_orders():
    materials = get_all_materials()
    if not materials:
        print("没有可用的材质，请先插入项目数据")
        return
    
    order_count = 50  # 生成50个测试订单
    inserted_orders = 0
    
    print(f"\n开始生成 {order_count} 个订单...")
    
    for i in range(order_count):
        # 生成订单信息
        customer_name = random.choice(customer_names)
        note = random.choice(order_notes)
        phone = f"1{random.choice(['3','4','5','6','7','8','9'])}{random.randint(100000000, 999999999)}"
        order_date = get_random_date()
        
        # 为每个订单添加3-8个项目
        item_count = random.randint(3, 8)
        selected_materials = random.sample(materials, min(item_count, len(materials)))
        
        total_amount = 0
        order_items_data = []
        
        for material in selected_materials:
            material_id = material[0]
            material_name = material[1]
            purchase_price = float(material[2])
            selling_price = float(material[3])
            project_name = material[4]
            
            # 随机数量（根据产品类型）
            if '管' in project_name:
                quantity = random.randint(10, 50)  # 管道按米或根，数量多
            elif '生料带' in project_name or '管卡' in project_name:
                quantity = random.randint(5, 20)  # 小配件
            else:
                quantity = random.randint(1, 10)  # 其他配件
            
            item_total = selling_price * quantity
            total_amount += item_total
            
            order_items_data.append({
                'name': project_name,
                'material': material_name,
                'purchase_price': purchase_price,
                'selling_price': selling_price,
                'quantity': quantity,
                'price': item_total
            })
        
        # 确定支付状态
        if random.random() < 0.7:  # 70%已支付
            paid_amount = total_amount if random.random() < 0.8 else float(total_amount) * random.choice([0.5, 0.8])
            is_paid = 1
        else:
            paid_amount = None
            is_paid = 0
        
        # 插入订单
        cursor.execute("""
            INSERT INTO orders (customer_name, phone, note, total_amount, paid_amount, is_paid, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (customer_name, phone, note, total_amount, paid_amount, is_paid, order_date))
        
        order_id = cursor.lastrowid
        
        # 插入订单项目
        for item in order_items_data:
            cursor.execute("""
                INSERT INTO order_items 
                (order_id, name, material, purchase_price, selling_price, quantity, price)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                order_id,
                item['name'],
                item['material'],
                item['purchase_price'],
                item['selling_price'],
                item['quantity'],
                item['price']
            ))
        
        inserted_orders += 1
        status = "已结账" if is_paid else "未结账"
        print(f"  ✓ 订单 {i+1}/{order_count}: {customer_name} - ¥{total_amount:.2f} ({status})")
    
    conn.commit()
    print(f"\n✅ 成功生成 {inserted_orders} 个订单")

# 销售记录类型和名称
sales_types = {
    'purchase': ['进货-华东建材', '进货-华南管材', '进货-本地批发', '补货-常规', '补货-紧急', '季度备货'],
    'sale': ['零售-散客', '零售-老客户', '批发-装修公司', '批发-工程队', '线上订单', '电话订单']
}

sales_notes = [
    '质量可靠，价格优惠',
    '客户指定品牌',
    '工程配套使用',
    '老客户回购',
    '新客户开发',
    '样品试用',
    '大批量采购',
    '急需补货',
    '季节性备货',
    '促销活动'
]

# 生成测试销售记录
def insert_sales_records():
    materials = get_all_materials()
    if not materials:
        print("没有可用的材质，请先插入项目数据")
        return
    
    sales_count = 80  # 生成80个销售记录
    inserted_sales = 0
    
    print(f"\n开始生成 {sales_count} 个销售记录...")
    
    for i in range(sales_count):
        # 随机选择类型
        sales_type = random.choice(['purchase', 'sale'])
        name = random.choice(sales_types[sales_type])
        note = random.choice(sales_notes)
        record_date = get_random_date()
        
        # 随机选择2-6个项目
        item_count = random.randint(2, 6)
        selected_materials = random.sample(materials, min(item_count, len(materials)))
        
        total_amount = 0
        sales_items_data = []
        
        for material in selected_materials:
            material_id = material[0]
            material_name = material[1]
            purchase_price = float(material[2])
            selling_price = float(material[3])
            project_name = material[4]
            
            # 随机数量
            if sales_type == 'purchase':
                quantity = random.randint(20, 100)  # 进货数量大
                item_total = quantity * purchase_price
            else:
                quantity = random.randint(1, 20)  # 销售数量小
                item_total = quantity * selling_price
            
            total_amount += item_total
            
            sales_items_data.append({
                'item_id': material_id,
                'is_system_item': 1,
                'name': project_name,
                'material': material_name,
                'purchase_price': purchase_price,
                'selling_price': selling_price,
                'quantity': quantity
            })
        
        # 插入销售记录
        cursor.execute("""
            INSERT INTO sales_records (name, type, note, total_amount, is_deleted, created_at)
            VALUES (%s, %s, %s, %s, 0, %s)
        """, (name, sales_type, note, total_amount, record_date))
        
        sales_id = cursor.lastrowid
        
        # 插入销售项目明细
        for item in sales_items_data:
            cursor.execute("""
                INSERT INTO sales_items 
                (sales_id, item_id, is_system_item, name, material, purchase_price, selling_price, quantity, note)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                sales_id,
                item['item_id'],
                item['is_system_item'],
                item['name'],
                item['material'],
                item['purchase_price'],
                item['selling_price'],
                item['quantity'],
                ''
            ))
        
        inserted_sales += 1
        type_label = "进货" if sales_type == 'purchase' else "销售"
        print(f"  ✓ 记录 {i+1}/{sales_count}: {name} - ¥{total_amount:.2f} ({type_label})")
    
    conn.commit()
    print(f"\n✅ 成功生成 {inserted_sales} 个销售记录")

# 生成价格轨迹数据
def insert_price_history():
    materials = get_all_materials()
    if not materials:
        print("没有可用的材质")
        return
    
    print("\n开始生成价格轨迹数据...")
    
    history_count = 0
    for material in materials:
        project_name = material[3]
        material_name = material[1]
        current_purchase = float(material[2])
        current_selling = float(material[3])
        
        # 为每个材质生成2-4条价格变更记录
        changes = random.randint(2, 4)
        
        for i in range(changes):
            # 生成历史价格（当前价格的80%-120%）
            factor = random.uniform(0.8, 1.2)
            historical_purchase = round(current_purchase * factor, 2)
            historical_selling = round(current_selling * factor, 2)
            
            # 随机更新时间和方式
            update_date = get_random_date()
            update_method = random.choice(['manual', 'auto'])
            
            cursor.execute("""
                INSERT INTO price_history 
                (project_name, material, purchase_price, selling_price, update_time, update_method)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (project_name, material_name, historical_purchase, historical_selling, update_date, update_method))
            
            history_count += 1
    
    conn.commit()
    print(f"✅ 成功生成 {history_count} 条价格轨迹记录")

# 主函数
def main():
    print("=" * 60)
    print("开始生成真实测试数据")
    print("=" * 60)
    
    try:
        # 1. 插入项目和材质
        insert_projects()
        
        # 2. 生成订单
        insert_orders()
        
        # 3. 生成销售记录
        insert_sales_records()
        
        # 4. 生成价格轨迹
        insert_price_history()
        
        print("\n" + "=" * 60)
        print("✅ 所有测试数据生成完成！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    main()
