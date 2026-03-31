from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from db import get_db_connection
import os

app = Flask(__name__)
CORS(app)

# 初始化数据库表结构
def init_database():
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            # 创建价格轨迹表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS price_history (
                id INT AUTO_INCREMENT PRIMARY KEY,
                project_name VARCHAR(255) NOT NULL,
                material VARCHAR(255) NOT NULL,
                purchase_price DECIMAL(10,2) NOT NULL,
                selling_price DECIMAL(10,2) NOT NULL,
                update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                update_method ENUM('manual', 'auto') NOT NULL,
                INDEX idx_project_material (project_name, material)
            )
            ''')
            connection.commit()
            print('价格轨迹表初始化成功')
    except Exception as e:
        print(f'初始化数据库表失败: {e}')
    finally:
        connection.close()

# 初始化数据库
init_database()

# ======================
# 🔥 修复前端访问（相对路径，任何环境都能运行）
# ======================
@app.route('/')
def serve_frontend():
    return send_from_directory('../frontend', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('../frontend', path)

# 登录接口
@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT * FROM users WHERE username = %s AND password = %s', (username, password))
            user = cursor.fetchone()
            if user:
                return jsonify({'success': True, 'message': '登录成功'})
            else:
                return jsonify({'success': False, 'message': '用户名或密码错误'})
    finally:
        connection.close()

# 项目管理接口 - 一对多模式

# 获取项目列表
@app.route('/api/projects', methods=['GET'])
def get_projects():
    name = request.args.get('name')
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            if name:
                cursor.execute('SELECT * FROM projects WHERE name LIKE %s AND is_deleted = 0', ('%' + name + '%',))
            else:
                cursor.execute('SELECT * FROM projects WHERE is_deleted = 0')
            projects = cursor.fetchall()
            
            # 为每个项目获取关联的材质
            for project in projects:
                cursor.execute('SELECT * FROM materials WHERE project_id = %s AND is_deleted = 0', (project['id'],))
                project['materials'] = cursor.fetchall()
            
            return jsonify({'success': True, 'data': projects})
    finally:
        connection.close()

# 添加项目
@app.route('/api/projects', methods=['POST'])
def add_project():
    data = request.json
    name = data.get('name')
    
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            # 检查项目名称是否已存在
            cursor.execute('SELECT * FROM projects WHERE name = %s AND is_deleted = 0', (name,))
            if cursor.fetchone():
                return jsonify({'success': False, 'message': '项目名称已存在'})
            
            # 插入新项目
            cursor.execute('INSERT INTO projects (name) VALUES (%s)', (name,))
            project_id = cursor.lastrowid
            connection.commit()
            return jsonify({'success': True, 'message': '项目添加成功', 'project_id': project_id})
    finally:
        connection.close()

# 获取项目详情
@app.route('/api/projects/<int:project_id>', methods=['GET'])
def get_project(project_id):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            # 获取项目信息
            cursor.execute('SELECT * FROM projects WHERE id = %s AND is_deleted = 0', (project_id,))
            project = cursor.fetchone()
            if not project:
                return jsonify({'success': False, 'message': '项目不存在'})
            
            # 获取关联的材质
            cursor.execute('SELECT * FROM materials WHERE project_id = %s AND is_deleted = 0', (project_id,))
            project['materials'] = cursor.fetchall()
            
            return jsonify({'success': True, 'data': project})
    finally:
        connection.close()

# 更新项目
@app.route('/api/projects/<int:project_id>', methods=['PUT'])
def update_project(project_id):
    data = request.json
    name = data.get('name')
    
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            # 检查项目是否存在
            cursor.execute('SELECT * FROM projects WHERE id = %s AND is_deleted = 0', (project_id,))
            if not cursor.fetchone():
                return jsonify({'success': False, 'message': '项目不存在'})
            
            # 检查新名称是否已被其他项目使用
            cursor.execute('SELECT * FROM projects WHERE name = %s AND id != %s AND is_deleted = 0', (name, project_id))
            if cursor.fetchone():
                return jsonify({'success': False, 'message': '项目名称已存在'})
            
            # 更新项目名称
            cursor.execute('UPDATE projects SET name = %s WHERE id = %s', (name, project_id))
            connection.commit()
            return jsonify({'success': True, 'message': '项目更新成功'})
    finally:
        connection.close()

# 删除项目
@app.route('/api/projects/<int:project_id>', methods=['DELETE'])
def delete_project(project_id):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            # 软删除项目（级联删除材质）
            cursor.execute('UPDATE projects SET is_deleted = 1 WHERE id = %s', (project_id,))
            connection.commit()
            return jsonify({'success': True, 'message': '项目删除成功'})
    finally:
        connection.close()

# 材质管理接口

# 添加材质
@app.route('/api/materials', methods=['POST'])
def add_material():
    data = request.json
    project_id = data.get('project_id')
    material = data.get('material')
    purchase_price = data.get('purchase_price')
    selling_price = data.get('selling_price')
    stock = data.get('stock', 0)
    note = data.get('note')
    
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            # 检查项目是否存在
            cursor.execute('SELECT * FROM projects WHERE id = %s AND is_deleted = 0', (project_id,))
            if not cursor.fetchone():
                return jsonify({'success': False, 'message': '项目不存在'})
            
            # 检查材质是否已存在
            cursor.execute('SELECT * FROM materials WHERE project_id = %s AND material = %s AND is_deleted = 0', (project_id, material))
            if cursor.fetchone():
                return jsonify({'success': False, 'message': '材质已存在'})
            
            # 插入新材质
            cursor.execute('''
            INSERT INTO materials (project_id, material, purchase_price, selling_price, stock, note)
            VALUES (%s, %s, %s, %s, %s, %s)
            ''', (project_id, material, purchase_price, selling_price, stock, note))
            connection.commit()
            return jsonify({'success': True, 'message': '材质添加成功'})
    finally:
        connection.close()

# 更新材质
@app.route('/api/materials/<int:material_id>', methods=['PUT'])
def update_material(material_id):
    data = request.json
    material = data.get('material')
    purchase_price = data.get('purchase_price')
    selling_price = data.get('selling_price')
    stock = data.get('stock', 0)
    note = data.get('note')
    
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            # 检查材质是否存在
            cursor.execute('SELECT * FROM materials WHERE id = %s AND is_deleted = 0', (material_id,))
            existing_material = cursor.fetchone()
            if not existing_material:
                return jsonify({'success': False, 'message': '材质不存在'})
            
            # 检查新材质名称是否已被同一项目使用
            if material and material != existing_material['material']:
                cursor.execute('''
                SELECT * FROM materials WHERE project_id = %s AND material = %s AND id != %s AND is_deleted = 0
                ''', (existing_material['project_id'], material, material_id))
                if cursor.fetchone():
                    return jsonify({'success': False, 'message': '材质已存在'})
            
            # 更新材质信息
            cursor.execute('''
            UPDATE materials SET material = %s, purchase_price = %s, selling_price = %s, stock = %s, note = %s
            WHERE id = %s
            ''', (material, purchase_price, selling_price, stock, note, material_id))
            connection.commit()
            return jsonify({'success': True, 'message': '材质更新成功'})
    finally:
        connection.close()

# 删除材质
@app.route('/api/materials/<int:material_id>', methods=['DELETE'])
def delete_material(material_id):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            # 软删除材质
            cursor.execute('UPDATE materials SET is_deleted = 1 WHERE id = %s', (material_id,))
            connection.commit()
            return jsonify({'success': True, 'message': '材质删除成功'})
    finally:
        connection.close()

# 兼容旧接口（用于前端过渡）
@app.route('/api/items', methods=['GET'])
def get_items():
    name = request.args.get('name')
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            if name:
                cursor.execute('SELECT * FROM items WHERE name LIKE %s AND is_deleted = 0', ('%' + name + '%',))
            else:
                cursor.execute('SELECT * FROM items WHERE is_deleted = 0')
            items = cursor.fetchall()
            return jsonify({'success': True, 'data': items})
    finally:
        connection.close()

@app.route('/api/items', methods=['POST'])
def add_item():
    data = request.json
    name = data.get('name')
    purchase_price = data.get('purchase_price')
    selling_price = data.get('selling_price')
    stock = data.get('stock')
    note = data.get('note')
    material = data.get('material')
    
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            if material:
                cursor.execute('''
                SELECT * FROM items WHERE name = %s AND material = %s AND is_deleted = 0
                ''', (name, material))
            else:
                cursor.execute('''
                SELECT * FROM items WHERE name = %s AND (material IS NULL OR material = '') AND is_deleted = 0
                ''', (name,))
            
            if cursor.fetchone():
                return jsonify({'success': False, 'message': '项目名称已存在'})
            
            cursor.execute('''
            INSERT INTO items (name, purchase_price, selling_price, stock, note, material)
            VALUES (%s, %s, %s, %s, %s, %s)
            ''', (name, purchase_price, selling_price, stock or 0, note, material))
            connection.commit()
            return jsonify({'success': True, 'message': '项目添加成功'})
    finally:
        connection.close()

@app.route('/api/items/<int:item_id>', methods=['GET'])
def get_item(item_id):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute('''
            SELECT * FROM items WHERE id = %s AND is_deleted = 0
            ''', (item_id,))
            item = cursor.fetchone()
            if item:
                return jsonify({'success': True, 'data': item})
            else:
                return jsonify({'success': False, 'message': '项目不存在'})
    finally:
        connection.close()

@app.route('/api/items/<int:item_id>', methods=['PUT'])
def update_item(item_id):
    data = request.json
    name = data.get('name')
    purchase_price = data.get('purchase_price')
    selling_price = data.get('selling_price')
    stock = data.get('stock')
    note = data.get('note')
    material = data.get('material')
    
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            if material:
                cursor.execute('''
                SELECT * FROM items WHERE name = %s AND material = %s AND id != %s AND is_deleted = 0
                ''', (name, material, item_id))
            else:
                cursor.execute('''
                SELECT * FROM items WHERE name = %s AND (material IS NULL OR material = '') AND id != %s AND is_deleted = 0
                ''', (name, item_id))
            
            if cursor.fetchone():
                return jsonify({'success': False, 'message': '项目名称已存在'})
            
            cursor.execute('''
            UPDATE items SET name = %s, purchase_price = %s, selling_price = %s, stock = %s, note = %s, material = %s
            WHERE id = %s
            ''', (name, purchase_price, selling_price, stock or 0, note, material, item_id))
            connection.commit()
            return jsonify({'success': True, 'message': '项目更新成功'})
    finally:
        connection.close()

@app.route('/api/items/<int:item_id>', methods=['DELETE'])
def delete_item(item_id):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute('''
            UPDATE items SET is_deleted = 1
            WHERE id = %s
            ''', (item_id,))
            connection.commit()
            return jsonify({'success': True, 'message': '项目删除成功'})
    finally:
        connection.close()

# 订单管理接口
@app.route('/api/orders', methods=['GET'])
def get_orders():
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute('''
            SELECT o.*, COUNT(oi.id) as item_count 
            FROM orders o
            LEFT JOIN order_items oi ON o.id = oi.order_id
            GROUP BY o.id
            ORDER BY o.created_at DESC
            ''')
            orders = cursor.fetchall()
            return jsonify({'success': True, 'data': orders})
    finally:
        connection.close()

# 创建项目的辅助函数
def create_project(cursor, project_name):
    try:
        print(f"=== create_project called with: {project_name} ===")
        # 检查项目是否存在
        cursor.execute('''
        SELECT id FROM projects WHERE name = %s AND is_deleted = 0
        ''', (project_name,))
        project = cursor.fetchone()
        print(f"Project check result: {project}")
        
        if not project:
            # 创建新项目
            print(f"Creating project: {project_name}")
            # 先检查SQL语法
            insert_sql = "INSERT INTO projects (name) VALUES (%s)"
            print(f"Executing SQL: {insert_sql} with params: {project_name}")
            
            # 执行插入
            cursor.execute(insert_sql, (project_name,))
            
            # 获取插入后的ID
            project_id = cursor.lastrowid
            print(f"Created project with id: {project_id}")
            
            # 验证插入是否成功
            cursor.execute('''
            SELECT id FROM projects WHERE id = %s AND is_deleted = 0
            ''', (project_id,))
            verify = cursor.fetchone()
            print(f"Verification result: {verify}")
            
            if verify:
                return project_id
            else:
                print(f"Project creation failed, verification returned None")
                return 1
        else:
            print(f"Project already exists: {project}")
            return project['id']
    except Exception as e:
        print(f"Error in create_project: {type(e).__name__}: {e}")
        # 重新查询项目，确保返回有效ID
        try:
            cursor.execute('''
            SELECT id FROM projects WHERE name = %s AND is_deleted = 0
            ''', (project_name,))
            project = cursor.fetchone()
            print(f"Retry project check result: {project}")
            if project:
                return project['id']
        except Exception as e2:
            print(f"Error in retry: {e2}")
        return 1

# 创建材质的辅助函数
def create_material(cursor, project_id, material_name, purchase_price, selling_price, stock, note, source):
    try:
        # 检查材质是否存在
        cursor.execute('''
        SELECT id FROM materials WHERE project_id = %s AND material = %s AND is_deleted = 0
        ''', (project_id, material_name))
        material = cursor.fetchone()
        
        if not material:
            # 创建新材质
            cursor.execute('''
            INSERT INTO materials (project_id, material, purchase_price, selling_price, stock, note, source)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ''', (
                project_id,
                material_name,
                purchase_price,
                selling_price,
                stock,
                note,
                source
            ))
            print(f"Created material: {material_name}")
    except Exception as e:
        print(f"Error in create_material: {e}")

@app.route('/api/orders', methods=['POST'])
def add_order():
    data = request.json
    customer_name = data.get('customer_name')
    phone = data.get('phone')
    paid_amount = data.get('paid_amount')
    order_items = data.get('items')
    
    connection = get_db_connection()
    try:
        # 处理所有项目，包括系统项目和非系统项目
        with connection.cursor() as cursor:
            processed_items = []
            duplicate_items = []
            
            print("=== add_order function called ===")
            print(f"Order items: {order_items}")
            
            for item in order_items:
                print(f"Processing item: {item}")
                if not item.get('item_id') and item.get('name'):
                    print(f"Processing non-system item: {item['name']}")
                    # 检查项目是否存在于projects表中（无论是否存在于items表中）
                    cursor.execute('''
                    SELECT id FROM projects WHERE name = %s AND is_deleted = 0
                    ''', (item['name'],))
                    project = cursor.fetchone()
                    print(f"Project check result: {project}")
                    
                    if not project:
                        # 创建项目
                        print(f"=== Creating project: {item['name']} ===")
                        try:
                            # 先检查SQL语法
                            insert_sql = "INSERT INTO projects (name) VALUES (%s)"
                            print(f"Executing SQL: {insert_sql} with params: {item['name']}")
                            
                            cursor.execute(insert_sql, (item['name'],))
                            project_id = cursor.lastrowid
                            print(f"Created project: {item['name']} with ID: {project_id}")
                            
                            # 验证插入是否成功
                            cursor.execute('''
                            SELECT id FROM projects WHERE id = %s AND is_deleted = 0
                            ''', (project_id,))
                            verify = cursor.fetchone()
                            print(f"Verification result: {verify}")
                            
                            if verify:
                                print(f"Project creation verification successful")
                                # 更新project变量，确保后续逻辑使用正确的项目信息
                                project = verify
                                project_id = project['id']
                            else:
                                print(f"Project creation verification failed")
                                # 尝试重新查询
                                cursor.execute('''
                                SELECT id FROM projects WHERE name = %s AND is_deleted = 0
                                ''', (item['name'],))
                                project = cursor.fetchone()
                                if project:
                                    project_id = project['id']
                                    print(f"Found project after verification: {project_id}")
                                else:
                                    project_id = 1
                                    print(f"Using default project ID: {project_id}")
                        except Exception as e:
                            print(f"Error creating project: {type(e).__name__}: {e}")
                            # 重新查询项目，确保返回有效ID
                            cursor.execute('''
                            SELECT id FROM projects WHERE name = %s AND is_deleted = 0
                            ''', (item['name'],))
                            project = cursor.fetchone()
                            print(f"Retry project check result: {project}")
                            if project:
                                project_id = project['id']
                                print(f"Found existing project: {item['name']} with ID: {project_id}")
                            else:
                                project_id = 1
                                print(f"Using default project ID: {project_id}")
                    else:
                        project_id = project['id']
                        print(f"Project already exists: {item['name']} with ID: {project_id}")
                    
                    # 检查材质是否存在
                    cursor.execute('''
                    SELECT id FROM materials WHERE project_id = %s AND material = %s AND is_deleted = 0
                    ''', (project_id, item.get('material', '')))
                    material = cursor.fetchone()
                    
                    if not material:
                        # 创建材质
                        try:
                            cursor.execute('''
                            INSERT INTO materials (project_id, material, purchase_price, selling_price, stock, note, source)
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                            ''', (
                                project_id,
                                item.get('material', ''),
                                item['purchase_price'],
                                item['selling_price'],
                                item.get('stock', 0),
                                item.get('note'),
                                'order_add'
                            ))
                            print(f"Created material: {item.get('material', '')}")
                        except Exception as e:
                            print(f"Error creating material: {e}")
                    
                    # 检查项目是否存在于items表中
                    if item.get('material'):
                        cursor.execute('''
                        SELECT * FROM items WHERE name = %s AND material = %s AND is_deleted = 0
                        ''', (item['name'], item['material']))
                    else:
                        cursor.execute('''
                        SELECT * FROM items WHERE name = %s AND (material IS NULL OR material = '') AND is_deleted = 0
                        ''', (item['name'],))
                    
                    existing_item = cursor.fetchone()
                    
                    if existing_item:
                        item_id = existing_item['id']
                        duplicate_items.append({
                            'id': item_id,
                            'name': existing_item['name'],
                            'material': existing_item['material']
                        })
                        
                        # 检查价格是否发生变化
                        if (existing_item['purchase_price'] != item['purchase_price'] or 
                            existing_item['selling_price'] != item['selling_price']):
                            # 更新 items 表中的价格
                            cursor.execute('''
                            UPDATE items SET purchase_price = %s, selling_price = %s
                            WHERE id = %s
                            ''', (
                                item['purchase_price'],
                                item['selling_price'],
                                item_id
                            ))
                            
                            # 同时更新 materials 表中的价格
                            cursor.execute('''
                            UPDATE materials SET purchase_price = %s, selling_price = %s
                            WHERE project_id = (SELECT id FROM projects WHERE name = %s AND is_deleted = 0 LIMIT 1) AND material = %s AND is_deleted = 0
                            ''', (
                                item['purchase_price'],
                                item['selling_price'],
                                item['name'],
                                item.get('material', '')
                            ))
                            
                            # 记录价格轨迹
                            cursor.execute('''
                            INSERT INTO price_history (project_name, material, purchase_price, selling_price, update_method)
                            VALUES (%s, %s, %s, %s, 'auto')
                            ''', (
                                item['name'],
                                item.get('material', ''),
                                item['purchase_price'],
                                item['selling_price']
                            ))
                    else:
                        # 添加到 items 表
                        cursor.execute('''
                        INSERT INTO items (name, purchase_price, selling_price, stock, note, material, source)
                        VALUES (%s, %s, %s, %s, %s, %s, 'order_add')
                        ''', (
                            item['name'],
                            item['purchase_price'],
                            item['selling_price'],
                            item.get('stock', 0),
                            item.get('note'),
                            item.get('material')
                        ))
                        item_id = cursor.lastrowid
                        
                        # 记录初始价格轨迹
                        cursor.execute('''
                        INSERT INTO price_history (project_name, material, purchase_price, selling_price, update_method)
                        VALUES (%s, %s, %s, %s, 'auto')
                        ''', (
                            item['name'],
                            item.get('material', ''),
                            item['purchase_price'],
                            item['selling_price']
                        ))
                    
                    processed_item = {
                        'item_id': item_id,
                        'name': item['name'],
                        'material': item.get('material'),
                        'purchase_price': item['purchase_price'],
                        'selling_price': item['selling_price'],
                        'note': item.get('note'),
                        'quantity': item['quantity'],
                        'price': item['price']
                    }
                    processed_items.append(processed_item)
                else:
                    cursor.execute('''
                    SELECT name, material, purchase_price, selling_price, note 
                    FROM items WHERE id = %s AND is_deleted = 0
                    ''', (item['item_id'],))
                    item_info = cursor.fetchone()
                    if item_info:
                        processed_item = {
                            'item_id': item['item_id'],
                            'name': item_info['name'],
                            'material': item_info['material'],
                            'purchase_price': item_info['purchase_price'],
                            'selling_price': item_info['selling_price'],
                            'note': item_info['note'],
                            'quantity': item['quantity'],
                            'price': item['price']
                        }
                        processed_items.append(processed_item)
            
            # 计算总金额
            total_amount = 0
            for item in processed_items:
                total_amount += item['quantity'] * item['price']
            
            is_paid = 1 if paid_amount else 0
            
            # 创建订单
            cursor.execute('''
            INSERT INTO orders (customer_name, phone, total_amount, paid_amount, is_paid)
            VALUES (%s, %s, %s, %s, %s)
            ''', (customer_name, phone, total_amount, paid_amount, is_paid))
            order_id = cursor.lastrowid
            
            # 添加订单项目
            for item in processed_items:
                cursor.execute('''
                INSERT INTO order_items (order_id, item_id, name, material, purchase_price, selling_price, note, quantity, price)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ''', (
                    order_id, item['item_id'], item['name'], item['material'],
                    item['purchase_price'], item['selling_price'], item['note'],
                    item['quantity'], item['price']
                ))
            
            # 提交所有事务
            connection.commit()
            print("Committed all transactions")
            
            response = {
                'success': True,
                'message': '订单添加成功',
                'order_id': order_id
            }
            if duplicate_items:
                response['duplicate_items'] = duplicate_items
            return jsonify(response)
    finally:
        connection.close()

@app.route('/api/orders/<int:order_id>', methods=['GET'])
def get_order_detail(order_id):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT * FROM orders WHERE id = %s', (order_id,))
            order = cursor.fetchone()
            
            cursor.execute('''
            SELECT * FROM order_items 
            WHERE order_id = %s
            ''', (order_id,))
            items = cursor.fetchall()
            
            order['items'] = items
            return jsonify({'success': True, 'data': order})
    finally:
        connection.close()

@app.route('/api/orders/<int:order_id>', methods=['PUT'])
def update_order(order_id):
    data = request.json
    customer_name = data.get('customer_name')
    phone = data.get('phone')
    paid_amount = data.get('paid_amount')
    items_to_update = data.get('items_to_update', [])
    items_to_delete = data.get('items_to_delete', [])
    items_to_add = data.get('items_to_add', [])
    
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            processed_update_items = []
            duplicate_items = []
            for item in items_to_update:
                if not item.get('item_id') and item.get('name'):
                    if item.get('material'):
                        cursor.execute('''
                        SELECT * FROM items WHERE name = %s AND material = %s AND is_deleted = 0
                        ''', (item['name'], item['material']))
                    else:
                        cursor.execute('''
                        SELECT * FROM items WHERE name = %s AND (material IS NULL OR material = '') AND is_deleted = 0
                        ''', (item['name'],))
                    
                    existing_item = cursor.fetchone()
                    
                    # 检查项目是否存在于项目管理系统中
                    cursor.execute('''
                    SELECT id FROM projects WHERE name = %s AND is_deleted = 0
                    ''', (item['name'],))
                    project = cursor.fetchone()
                    
                    if not project:
                        try:
                            # 创建新项目
                            print(f"Creating project: {item['name']}")
                            cursor.execute('''
                            INSERT INTO projects (name)
                            VALUES (%s)
                            ''', (item['name'],))
                            project_id = cursor.lastrowid
                            print(f"Created project with id: {project_id}")
                        except Exception as e:
                            # 处理项目名称重复的情况
                            print(f"Error creating project: {e}")
                            # 重新查询项目
                            cursor.execute('''
                            SELECT id FROM projects WHERE name = %s AND is_deleted = 0
                            ''', (item['name'],))
                            project = cursor.fetchone()
                            if project:
                                project_id = project['id']
                                print(f"Found existing project with id: {project_id}")
                            else:
                                # 如果仍然不存在，使用默认值
                                project_id = 1
                                print(f"Using default project id: {project_id}")
                    else:
                        project_id = project['id']
                        print(f"Using existing project with id: {project_id}")
                    
                    # 检查材质是否存在
                    cursor.execute('''
                    SELECT id FROM materials WHERE project_id = %s AND material = %s AND is_deleted = 0
                    ''', (project_id, item.get('material', '')))
                    material = cursor.fetchone()
                    
                    if not material:
                        # 创建新材质
                        cursor.execute('''
                        INSERT INTO materials (project_id, material, purchase_price, selling_price, stock, note, source)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ''', (
                            project_id,
                            item.get('material', ''),
                            item['purchase_price'],
                            item['selling_price'],
                            item.get('stock', 0),
                            item.get('note'),
                            'order_edit'
                        ))
                    
                    if existing_item:
                        item_id = existing_item['id']
                        duplicate_items.append({
                            'id': item_id,
                            'name': existing_item['name'],
                            'material': existing_item['material']
                        })
                        
                        # 检查价格是否发生变化
                        if (existing_item['purchase_price'] != item['purchase_price'] or 
                            existing_item['selling_price'] != item['selling_price']):
                            # 更新 items 表中的价格
                            cursor.execute('''
                            UPDATE items SET purchase_price = %s, selling_price = %s
                            WHERE id = %s
                            ''', (
                                item['purchase_price'],
                                item['selling_price'],
                                item_id
                            ))
                            
                            # 同时更新 materials 表中的价格
                            cursor.execute('''
                            UPDATE materials SET purchase_price = %s, selling_price = %s
                            WHERE project_id = (SELECT id FROM projects WHERE name = %s AND is_deleted = 0 LIMIT 1) AND material = %s AND is_deleted = 0
                            ''', (
                                item['purchase_price'],
                                item['selling_price'],
                                item['name'],
                                item.get('material', '')
                            ))
                            
                            # 记录价格轨迹
                            cursor.execute('''
                            INSERT INTO price_history (project_name, material, purchase_price, selling_price, update_method)
                            VALUES (%s, %s, %s, %s, 'auto')
                            ''', (
                                item['name'],
                                item.get('material', ''),
                                item['purchase_price'],
                                item['selling_price']
                            ))
                    else:
                        # 添加到 items 表
                        cursor.execute('''
                        INSERT INTO items (name, purchase_price, selling_price, stock, note, material, source)
                        VALUES (%s, %s, %s, %s, %s, %s, 'order_edit')
                        ''', (
                            item['name'],
                            item['purchase_price'],
                            item['selling_price'],
                            item.get('stock', 0),
                            item.get('note'),
                            item.get('material')
                        ))
                        item_id = cursor.lastrowid
                        
                        # 记录初始价格轨迹
                        cursor.execute('''
                        INSERT INTO price_history (project_name, material, purchase_price, selling_price, update_method)
                        VALUES (%s, %s, %s, %s, 'auto')
                        ''', (
                            item['name'],
                            item.get('material', ''),
                            item['purchase_price'],
                            item['selling_price']
                        ))
                    
                    processed_item = {
                        'id': item['id'],
                        'item_id': item_id,
                        'name': item['name'],
                        'material': item.get('material'),
                        'purchase_price': item['purchase_price'],
                        'selling_price': item['selling_price'],
                        'note': item.get('note'),
                        'quantity': item['quantity'],
                        'price': item['price']
                    }
                    processed_update_items.append(processed_item)
                else:
                    cursor.execute('''
                    SELECT name, material, purchase_price, selling_price, note 
                    FROM items WHERE id = %s AND is_deleted = 0
                    ''', (item['item_id'],))
                    item_info = cursor.fetchone()
                    if item_info:
                        processed_item = {
                            'id': item['id'],
                            'item_id': item['item_id'],
                            'name': item_info['name'],
                            'material': item_info['material'],
                            'purchase_price': item_info['purchase_price'],
                            'selling_price': item_info['selling_price'],
                            'note': item_info['note'],
                            'quantity': item['quantity'],
                            'price': item['price']
                        }
                        processed_update_items.append(processed_item)
            
            processed_add_items = []
            for item in items_to_add:
                if not item.get('item_id') and item.get('name'):
                    if item.get('material'):
                        cursor.execute('''
                        SELECT * FROM items WHERE name = %s AND material = %s AND is_deleted = 0
                        ''', (item['name'], item['material']))
                    else:
                        cursor.execute('''
                        SELECT * FROM items WHERE name = %s AND (material IS NULL OR material = '') AND is_deleted = 0
                        ''', (item['name'],))
                    
                    existing_item = cursor.fetchone()
                    
                    # 检查项目是否存在于项目管理系统中
                    cursor.execute('''
                    SELECT id FROM projects WHERE name = %s AND is_deleted = 0
                    ''', (item['name'],))
                    project = cursor.fetchone()
                    
                    if not project:
                        try:
                            # 创建新项目
                            print(f"Creating project: {item['name']}")
                            cursor.execute('''
                            INSERT INTO projects (name)
                            VALUES (%s)
                            ''', (item['name'],))
                            project_id = cursor.lastrowid
                            print(f"Created project with id: {project_id}")
                        except Exception as e:
                            # 处理项目名称重复的情况
                            print(f"Error creating project: {e}")
                            # 重新查询项目
                            cursor.execute('''
                            SELECT id FROM projects WHERE name = %s AND is_deleted = 0
                            ''', (item['name'],))
                            project = cursor.fetchone()
                            if project:
                                project_id = project['id']
                                print(f"Found existing project with id: {project_id}")
                            else:
                                # 如果仍然不存在，使用默认值
                                project_id = 1
                                print(f"Using default project id: {project_id}")
                    else:
                        project_id = project['id']
                        print(f"Using existing project with id: {project_id}")
                    
                    # 检查材质是否存在
                    cursor.execute('''
                    SELECT id FROM materials WHERE project_id = %s AND material = %s AND is_deleted = 0
                    ''', (project_id, item.get('material', '')))
                    material = cursor.fetchone()
                    
                    if not material:
                        # 创建新材质
                        cursor.execute('''
                        INSERT INTO materials (project_id, material, purchase_price, selling_price, stock, note, source)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ''', (
                            project_id,
                            item.get('material', ''),
                            item['purchase_price'],
                            item['selling_price'],
                            item.get('stock', 0),
                            item.get('note'),
                            'order_edit'
                        ))
                    
                    if existing_item:
                        item_id = existing_item['id']
                        duplicate_items.append({
                            'id': item_id,
                            'name': existing_item['name'],
                            'material': existing_item['material']
                        })
                        
                        # 检查价格是否发生变化
                        if (existing_item['purchase_price'] != item['purchase_price'] or 
                            existing_item['selling_price'] != item['selling_price']):
                            # 更新 items 表中的价格
                            cursor.execute('''
                            UPDATE items SET purchase_price = %s, selling_price = %s
                            WHERE id = %s
                            ''', (
                                item['purchase_price'],
                                item['selling_price'],
                                item_id
                            ))
                            
                            # 同时更新 materials 表中的价格
                            cursor.execute('''
                            UPDATE materials SET purchase_price = %s, selling_price = %s
                            WHERE project_id = (SELECT id FROM projects WHERE name = %s AND is_deleted = 0 LIMIT 1) AND material = %s AND is_deleted = 0
                            ''', (
                                item['purchase_price'],
                                item['selling_price'],
                                item['name'],
                                item.get('material', '')
                            ))
                            
                            # 记录价格轨迹
                            cursor.execute('''
                            INSERT INTO price_history (project_name, material, purchase_price, selling_price, update_method)
                            VALUES (%s, %s, %s, %s, 'auto')
                            ''', (
                                item['name'],
                                item.get('material', ''),
                                item['purchase_price'],
                                item['selling_price']
                            ))
                    else:
                        # 添加到 items 表
                        cursor.execute('''
                        INSERT INTO items (name, purchase_price, selling_price, stock, note, material, source)
                        VALUES (%s, %s, %s, %s, %s, %s, 'order_edit')
                        ''', (
                            item['name'],
                            item['purchase_price'],
                            item['selling_price'],
                            item.get('stock', 0),
                            item.get('note'),
                            item.get('material')
                        ))
                        item_id = cursor.lastrowid
                        
                        # 记录初始价格轨迹
                        cursor.execute('''
                        INSERT INTO price_history (project_name, material, purchase_price, selling_price, update_method)
                        VALUES (%s, %s, %s, %s, 'auto')
                        ''', (
                            item['name'],
                            item.get('material', ''),
                            item['purchase_price'],
                            item['selling_price']
                        ))
                    
                    processed_item = {
                        'item_id': item_id,
                        'name': item['name'],
                        'material': item.get('material'),
                        'purchase_price': item['purchase_price'],
                        'selling_price': item['selling_price'],
                        'note': item.get('note'),
                        'quantity': item['quantity'],
                        'price': item['price']
                    }
                    processed_add_items.append(processed_item)
                else:
                    cursor.execute('''
                    SELECT name, material, purchase_price, selling_price, note 
                    FROM items WHERE id = %s AND is_deleted = 0
                    ''', (item['item_id'],))
                    item_info = cursor.fetchone()
                    if item_info:
                        processed_item = {
                            'item_id': item['item_id'],
                            'name': item_info['name'],
                            'material': item_info['material'],
                            'purchase_price': item_info['purchase_price'],
                            'selling_price': item_info['selling_price'],
                            'note': item_info['note'],
                            'quantity': item['quantity'],
                            'price': item['price']
                        }
                        processed_add_items.append(processed_item)
            
            for item in processed_update_items:
                cursor.execute('''
                UPDATE order_items 
                SET item_id = %s, name = %s, material = %s, purchase_price = %s, selling_price = %s, note = %s, quantity = %s, price = %s
                WHERE id = %s
                ''', (
                    item['item_id'], item['name'], item['material'],
                    item['purchase_price'], item['selling_price'], item['note'],
                    item['quantity'], item['price'], item['id']
                ))
            
            for item in items_to_delete:
                cursor.execute('DELETE FROM order_items WHERE id = %s', (item['id'],))
            
            for item in processed_add_items:
                cursor.execute('''
                INSERT INTO order_items (order_id, item_id, name, material, purchase_price, selling_price, note, quantity, price)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ''', (
                    order_id, item['item_id'], item['name'], item['material'],
                    item['purchase_price'], item['selling_price'], item['note'],
                    item['quantity'], item['price']
                ))
            
            cursor.execute('''
            SELECT COALESCE(SUM(quantity * price), 0) as total 
            FROM order_items 
            WHERE order_id = %s
            ''', (order_id,))
            result = cursor.fetchone()
            total_amount = result['total']
            
            is_paid = 1 if paid_amount else 0
            
            has_changes = len(processed_update_items) > 0 or len(items_to_delete) > 0 or len(processed_add_items) > 0
            if has_changes or customer_name or phone is not None or paid_amount is not None:
                update_fields = []
                update_values = []
                
                if customer_name:
                    update_fields.append('customer_name = %s')
                    update_values.append(customer_name)
                
                if phone is not None:
                    update_fields.append('phone = %s')
                    update_values.append(phone)
                
                update_fields.append('total_amount = %s')
                update_values.append(total_amount)
                
                if paid_amount is not None:
                    update_fields.append('paid_amount = %s')
                    update_values.append(paid_amount)
                    update_fields.append('is_paid = %s')
                    update_values.append(is_paid)
                
                if has_changes:
                    update_fields.append('add_count = add_count + 1')
                
                update_values.append(order_id)
                
                update_sql = f'''UPDATE orders SET {', '.join(update_fields)} WHERE id = %s'''
                cursor.execute(update_sql, update_values)
            
            connection.commit()
            response = {
                'success': True,
                'message': '订单更新成功'
            }
            if duplicate_items:
                response['duplicate_items'] = duplicate_items
            return jsonify(response)
    finally:
        connection.close()

@app.route('/api/orders/<int:order_id>', methods=['DELETE'])
def delete_order(order_id):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute('DELETE FROM order_items WHERE order_id = %s', (order_id,))
            cursor.execute('DELETE FROM orders WHERE id = %s', (order_id,))
            connection.commit()
            return jsonify({'success': True, 'message': '订单删除成功'})
    finally:
        connection.close()

# 获取价格轨迹
@app.route('/api/price-history', methods=['GET'])
def get_price_history():
    project_name = request.args.get('project_name')
    material = request.args.get('material')
    
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            if project_name and material:
                cursor.execute('''
                SELECT * FROM price_history 
                WHERE project_name = %s AND material = %s 
                ORDER BY update_time DESC
                ''', (project_name, material))
            else:
                return jsonify({'success': False, 'message': '缺少项目名称或材质参数'})
            
            history = cursor.fetchall()
            return jsonify({'success': True, 'data': history})
    finally:
        connection.close()

# ==================== 销售记录API ====================

# 初始化销售记录表
def init_sales_tables():
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            # 创建销售记录主表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS sales_records (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                type ENUM('purchase', 'sale') NOT NULL,
                note TEXT,
                total_amount DECIMAL(10,2) NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                is_deleted TINYINT(1) DEFAULT 0
            )
            ''')
            
            # 创建销售记录项目明细表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS sales_items (
                id INT AUTO_INCREMENT PRIMARY KEY,
                sales_id INT NOT NULL,
                item_id INT,
                is_system_item TINYINT(1) DEFAULT 0,
                name VARCHAR(255) NOT NULL,
                material VARCHAR(255),
                purchase_price DECIMAL(10,2) NOT NULL DEFAULT 0,
                selling_price DECIMAL(10,2) NOT NULL DEFAULT 0,
                quantity INT NOT NULL DEFAULT 1,
                note TEXT,
                FOREIGN KEY (sales_id) REFERENCES sales_records(id) ON DELETE CASCADE
            )
            ''')
            
            connection.commit()
            print('销售记录表初始化成功')
    except Exception as e:
        print(f'初始化销售记录表失败: {e}')
    finally:
        connection.close()

# 初始化销售记录表
init_sales_tables()

# 获取销售记录列表
@app.route('/api/sales', methods=['GET'])
def get_sales_records():
    search = request.args.get('search', '')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            query = '''
            SELECT s.*, COUNT(si.id) as item_count 
            FROM sales_records s 
            LEFT JOIN sales_items si ON s.id = si.sales_id 
            WHERE s.is_deleted = 0
            '''
            params = []
            
            if search:
                query += ' AND s.name LIKE %s'
                params.append(f'%{search}%')
            
            if start_date:
                query += ' AND DATE(s.created_at) >= %s'
                params.append(start_date)
            
            if end_date:
                query += ' AND DATE(s.created_at) <= %s'
                params.append(end_date)
            
            query += ' GROUP BY s.id ORDER BY s.created_at DESC'
            
            cursor.execute(query, params)
            records = cursor.fetchall()
            
            return jsonify({'success': True, 'data': records})
    finally:
        connection.close()

# 获取单个销售记录详情
@app.route('/api/sales/<int:sales_id>', methods=['GET'])
def get_sales_record(sales_id):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            # 获取主记录
            cursor.execute('''
            SELECT * FROM sales_records 
            WHERE id = %s AND is_deleted = 0
            ''', (sales_id,))
            record = cursor.fetchone()
            
            if not record:
                return jsonify({'success': False, 'message': '销售记录不存在'})
            
            # 获取项目明细
            cursor.execute('''
            SELECT * FROM sales_items 
            WHERE sales_id = %s
            ''', (sales_id,))
            items = cursor.fetchall()
            
            record['items'] = items
            
            return jsonify({'success': True, 'data': record})
    finally:
        connection.close()

# 创建销售记录
@app.route('/api/sales', methods=['POST'])
def create_sales_record():
    data = request.get_json()
    name = data.get('name', '').strip()
    record_type = data.get('type', 'sale')
    note = data.get('note', '').strip()
    items = data.get('items', [])
    
    if not name:
        return jsonify({'success': False, 'message': '名称不能为空'})
    
    if not items:
        return jsonify({'success': False, 'message': '请至少添加一个项目'})
    
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            # 计算总金额
            total_amount = sum(item.get('selling_price', 0) * item.get('quantity', 1) for item in items)
            
            # 插入主记录
            cursor.execute('''
            INSERT INTO sales_records (name, type, note, total_amount)
            VALUES (%s, %s, %s, %s)
            ''', (name, record_type, note, total_amount))
            
            sales_id = cursor.lastrowid
            
            # 处理每个项目
            for item in items:
                item_name = item.get('name', '').strip()
                is_system_item = item.get('is_system_item', False)
                item_id = item.get('item_id')
                material = item.get('material', '')
                purchase_price = item.get('purchase_price', 0)
                selling_price = item.get('selling_price', 0)
                quantity = item.get('quantity', 1)
                item_note = item.get('note', '')
                
                # 如果不是系统项目，检查是否需要添加到项目管理
                if not is_system_item and item_name:
                    # 检查项目是否已存在
                    cursor.execute('''
                    SELECT id FROM projects WHERE name = %s AND is_deleted = 0
                    ''', (item_name,))
                    project = cursor.fetchone()
                    
                    if not project:
                        # 创建新项目
                        cursor.execute('''
                        INSERT INTO projects (name) VALUES (%s)
                        ''', (item_name,))
                        project_id = cursor.lastrowid
                        
                        # 创建材质
                        cursor.execute('''
                        INSERT INTO materials (project_id, material, purchase_price, selling_price, stock, note, source)
                        VALUES (%s, %s, %s, %s, %s, %s, 'sales')
                        ''', (project_id, material or '默认', purchase_price, selling_price, quantity, item_note))
                        
                        # 记录价格轨迹
                        cursor.execute('''
                        INSERT INTO price_history (project_name, material, purchase_price, selling_price, update_method)
                        VALUES (%s, %s, %s, %s, 'auto')
                        ''', (item_name, material or '默认', purchase_price, selling_price))
                    else:
                        project_id = project['id']
                        
                        # 检查材质是否已存在
                        cursor.execute('''
                        SELECT id, purchase_price, selling_price FROM materials 
                        WHERE project_id = %s AND material = %s AND is_deleted = 0
                        ''', (project_id, material or '默认'))
                        existing_material = cursor.fetchone()
                        
                        if existing_material:
                            # 更新价格
                            if existing_material['purchase_price'] != purchase_price or existing_material['selling_price'] != selling_price:
                                cursor.execute('''
                                UPDATE materials SET purchase_price = %s, selling_price = %s
                                WHERE id = %s
                                ''', (purchase_price, selling_price, existing_material['id']))
                                
                                # 记录价格轨迹
                                cursor.execute('''
                                INSERT INTO price_history (project_name, material, purchase_price, selling_price, update_method)
                                VALUES (%s, %s, %s, %s, 'auto')
                                ''', (item_name, material or '默认', purchase_price, selling_price))
                        else:
                            # 创建新材质
                            cursor.execute('''
                            INSERT INTO materials (project_id, material, purchase_price, selling_price, stock, note, source)
                            VALUES (%s, %s, %s, %s, %s, %s, 'sales')
                            ''', (project_id, material or '默认', purchase_price, selling_price, quantity, item_note))
                
                # 插入销售项目明细
                cursor.execute('''
                INSERT INTO sales_items (sales_id, item_id, is_system_item, name, material, purchase_price, selling_price, quantity, note)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ''', (sales_id, item_id, 1 if is_system_item else 0, item_name, material, purchase_price, selling_price, quantity, item_note))
            
            connection.commit()
            return jsonify({'success': True, 'message': '销售记录创建成功', 'id': sales_id})
    except Exception as e:
        connection.rollback()
        return jsonify({'success': False, 'message': f'创建失败: {str(e)}'})
    finally:
        connection.close()

# 更新销售记录
@app.route('/api/sales/<int:sales_id>', methods=['PUT'])
def update_sales_record(sales_id):
    data = request.get_json()
    name = data.get('name', '').strip()
    record_type = data.get('type', 'sale')
    note = data.get('note', '').strip()
    items = data.get('items', [])
    
    if not name:
        return jsonify({'success': False, 'message': '名称不能为空'})
    
    if not items:
        return jsonify({'success': False, 'message': '请至少添加一个项目'})
    
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            # 检查记录是否存在
            cursor.execute('''
            SELECT id FROM sales_records WHERE id = %s AND is_deleted = 0
            ''', (sales_id,))
            if not cursor.fetchone():
                return jsonify({'success': False, 'message': '销售记录不存在'})
            
            # 计算总金额
            total_amount = sum(item.get('selling_price', 0) * item.get('quantity', 1) for item in items)
            
            # 更新主记录
            cursor.execute('''
            UPDATE sales_records SET name = %s, type = %s, note = %s, total_amount = %s
            WHERE id = %s
            ''', (name, record_type, note, total_amount, sales_id))
            
            # 删除旧的项目明细
            cursor.execute('DELETE FROM sales_items WHERE sales_id = %s', (sales_id,))
            
            # 处理每个项目
            for item in items:
                item_name = item.get('name', '').strip()
                is_system_item = item.get('is_system_item', False)
                item_id = item.get('item_id')
                material = item.get('material', '')
                purchase_price = item.get('purchase_price', 0)
                selling_price = item.get('selling_price', 0)
                quantity = item.get('quantity', 1)
                item_note = item.get('note', '')
                
                # 如果不是系统项目，检查是否需要添加到项目管理
                if not is_system_item and item_name:
                    # 检查项目是否已存在
                    cursor.execute('''
                    SELECT id FROM projects WHERE name = %s AND is_deleted = 0
                    ''', (item_name,))
                    project = cursor.fetchone()
                    
                    if not project:
                        # 创建新项目
                        cursor.execute('''
                        INSERT INTO projects (name) VALUES (%s)
                        ''', (item_name,))
                        project_id = cursor.lastrowid
                        
                        # 创建材质
                        cursor.execute('''
                        INSERT INTO materials (project_id, material, purchase_price, selling_price, stock, note, source)
                        VALUES (%s, %s, %s, %s, %s, %s, 'sales')
                        ''', (project_id, material or '默认', purchase_price, selling_price, quantity, item_note))
                        
                        # 记录价格轨迹
                        cursor.execute('''
                        INSERT INTO price_history (project_name, material, purchase_price, selling_price, update_method)
                        VALUES (%s, %s, %s, %s, 'auto')
                        ''', (item_name, material or '默认', purchase_price, selling_price))
                    else:
                        project_id = project['id']
                        
                        # 检查材质是否已存在
                        cursor.execute('''
                        SELECT id, purchase_price, selling_price FROM materials 
                        WHERE project_id = %s AND material = %s AND is_deleted = 0
                        ''', (project_id, material or '默认'))
                        existing_material = cursor.fetchone()
                        
                        if existing_material:
                            # 更新价格
                            if existing_material['purchase_price'] != purchase_price or existing_material['selling_price'] != selling_price:
                                cursor.execute('''
                                UPDATE materials SET purchase_price = %s, selling_price = %s
                                WHERE id = %s
                                ''', (purchase_price, selling_price, existing_material['id']))
                                
                                # 记录价格轨迹
                                cursor.execute('''
                                INSERT INTO price_history (project_name, material, purchase_price, selling_price, update_method)
                                VALUES (%s, %s, %s, %s, 'auto')
                                ''', (item_name, material or '默认', purchase_price, selling_price))
                        else:
                            # 创建新材质
                            cursor.execute('''
                            INSERT INTO materials (project_id, material, purchase_price, selling_price, stock, note, source)
                            VALUES (%s, %s, %s, %s, %s, %s, 'sales')
                            ''', (project_id, material or '默认', purchase_price, selling_price, quantity, item_note))
                
                # 插入销售项目明细
                cursor.execute('''
                INSERT INTO sales_items (sales_id, item_id, is_system_item, name, material, purchase_price, selling_price, quantity, note)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ''', (sales_id, item_id, 1 if is_system_item else 0, item_name, material, purchase_price, selling_price, quantity, item_note))
            
            connection.commit()
            return jsonify({'success': True, 'message': '销售记录更新成功'})
    except Exception as e:
        connection.rollback()
        return jsonify({'success': False, 'message': f'更新失败: {str(e)}'})
    finally:
        connection.close()

# 删除销售记录（软删除）
@app.route('/api/sales/<int:sales_id>', methods=['DELETE'])
def delete_sales_record(sales_id):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            # 检查记录是否存在
            cursor.execute('''
            SELECT id FROM sales_records WHERE id = %s AND is_deleted = 0
            ''', (sales_id,))
            if not cursor.fetchone():
                return jsonify({'success': False, 'message': '销售记录不存在'})
            
            # 软删除
            cursor.execute('''
            UPDATE sales_records SET is_deleted = 1 WHERE id = %s
            ''', (sales_id,))
            
            connection.commit()
            return jsonify({'success': True, 'message': '销售记录删除成功'})
    except Exception as e:
        connection.rollback()
        return jsonify({'success': False, 'message': f'删除失败: {str(e)}'})
    finally:
        connection.close()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)