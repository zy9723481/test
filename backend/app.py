from flask import Flask, request, jsonify
from flask_cors import CORS
from db import get_db_connection

app = Flask(__name__)
CORS(app)

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

# 项目管理接口

# 获取项目列表
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

# 新增项目
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
            # 检查项目名称是否重复
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
            
            # 插入新项目
            cursor.execute('''
            INSERT INTO items (name, purchase_price, selling_price, stock, note, material)
            VALUES (%s, %s, %s, %s, %s, %s)
            ''', (name, purchase_price, selling_price, stock or 0, note, material))
            connection.commit()
            return jsonify({'success': True, 'message': '项目添加成功'})
    finally:
        connection.close()

# 获取单个项目详情
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

# 更新项目
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
            # 检查项目名称是否重复（排除当前项目）
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
            
            # 更新项目
            cursor.execute('''
            UPDATE items SET name = %s, purchase_price = %s, selling_price = %s, stock = %s, note = %s, material = %s
            WHERE id = %s
            ''', (name, purchase_price, selling_price, stock or 0, note, material, item_id))
            connection.commit()
            return jsonify({'success': True, 'message': '项目更新成功'})
    finally:
        connection.close()

# 删除项目（逻辑删除）
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

# 获取订单列表
@app.route('/api/orders', methods=['GET'])
def get_orders():
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            # 使用LEFT JOIN和COUNT获取每个订单的项目数量
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

# 新增订单
@app.route('/api/orders', methods=['POST'])
def add_order():
    data = request.json
    customer_name = data.get('customer_name')
    phone = data.get('phone')
    paid_amount = data.get('paid_amount')
    order_items = data.get('items')
    
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            # 处理自定义项目并入库
            processed_items = []
            for item in order_items:
                # 如果是自定义项目（没有item_id，但有完整的项目信息）
                if not item.get('item_id') and item.get('name'):
                    # 检查项目是否已存在
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
                        # 项目已存在，使用现有的item_id
                        item_id = existing_item['id']
                    else:
                        # 项目不存在，创建新项目
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
                    # 选择现有项目，获取完整信息
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
            
            # 计算是否已结账
            is_paid = 1 if paid_amount else 0
            
            # 插入订单
            cursor.execute('''
            INSERT INTO orders (customer_name, phone, total_amount, paid_amount, is_paid)
            VALUES (%s, %s, %s, %s, %s)
            ''', (customer_name, phone, total_amount, paid_amount, is_paid))
            order_id = cursor.lastrowid
            
            # 插入订单项目
            for item in processed_items:
                cursor.execute('''
                INSERT INTO order_items (order_id, item_id, name, material, purchase_price, selling_price, note, quantity, price)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ''', (
                    order_id, item['item_id'], item['name'], item['material'],
                    item['purchase_price'], item['selling_price'], item['note'],
                    item['quantity'], item['price']
                ))
            
            connection.commit()
            return jsonify({'success': True, 'message': '订单添加成功', 'order_id': order_id})
    finally:
        connection.close()

# 获取订单详情
@app.route('/api/orders/<int:order_id>', methods=['GET'])
def get_order_detail(order_id):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            # 获取订单信息
            cursor.execute('SELECT * FROM orders WHERE id = %s', (order_id,))
            order = cursor.fetchone()
            
            # 获取订单项目
            cursor.execute('''
            SELECT * FROM order_items 
            WHERE order_id = %s
            ''', (order_id,))
            items = cursor.fetchall()
            
            order['items'] = items
            return jsonify({'success': True, 'data': order})
    finally:
        connection.close()

# 编辑订单（完整编辑功能）
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
            # 处理自定义项目并入库
            processed_update_items = []
            for item in items_to_update:
                # 如果是自定义项目（没有item_id，但有完整的项目信息）
                if not item.get('item_id') and item.get('name'):
                    # 检查项目是否已存在
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
                        # 项目已存在，使用现有的item_id
                        item_id = existing_item['id']
                    else:
                        # 项目不存在，创建新项目
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
                    # 选择现有项目，获取完整信息
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
            
            # 处理要添加的自定义项目
            processed_add_items = []
            for item in items_to_add:
                # 如果是自定义项目（没有item_id，但有完整的项目信息）
                if not item.get('item_id') and item.get('name'):
                    # 检查项目是否已存在
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
                        # 项目已存在，使用现有的item_id
                        item_id = existing_item['id']
                    else:
                        # 项目不存在，创建新项目
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
                    # 选择现有项目，获取完整信息
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
            
            # 更新现有项目
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
            
            # 删除项目
            for item in items_to_delete:
                cursor.execute('DELETE FROM order_items WHERE id = %s', (item['id'],))
            
            # 添加新项目
            for item in processed_add_items:
                cursor.execute('''
                INSERT INTO order_items (order_id, item_id, name, material, purchase_price, selling_price, note, quantity, price)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ''', (
                    order_id, item['item_id'], item['name'], item['material'],
                    item['purchase_price'], item['selling_price'], item['note'],
                    item['quantity'], item['price']
                ))
            
            # 重新计算总金额
            cursor.execute('''
            SELECT COALESCE(SUM(quantity * price), 0) as total 
            FROM order_items 
            WHERE order_id = %s
            ''', (order_id,))
            result = cursor.fetchone()
            total_amount = result['total']
            
            # 计算是否已结账
            is_paid = 1 if paid_amount else 0
            
            # 更新订单信息
            has_changes = len(processed_update_items) > 0 or len(items_to_delete) > 0 or len(processed_add_items) > 0
            if has_changes or customer_name or phone is not None or paid_amount is not None:
                # 构建更新语句
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
            return jsonify({'success': True, 'message': '订单更新成功'})
    finally:
        connection.close()

# 删除订单
@app.route('/api/orders/<int:order_id>', methods=['DELETE'])
def delete_order(order_id):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            # 先删除订单项目
            cursor.execute('DELETE FROM order_items WHERE order_id = %s', (order_id,))
            
            # 再删除订单
            cursor.execute('DELETE FROM orders WHERE id = %s', (order_id,))
            
            connection.commit()
            return jsonify({'success': True, 'message': '订单删除成功'})
    finally:
        connection.close()

from config import HOST, PORT

if __name__ == '__main__':
    app.run(debug=True, host=HOST, port=PORT)
