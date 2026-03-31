from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from db import get_db_connection
from logger_config import logger, log_request, log_response, log_error, log_db_operation, log_price_update
import os
import traceback

app = Flask(__name__)
CORS(app)

# 初始化数据库表结构
def init_database():
    logger.info("【系统】开始初始化数据库表结构")
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
            logger.info("【系统】价格轨迹表初始化成功")
    except Exception as e:
        logger.error(f"【系统】初始化数据库表失败: {e}", exc_info=True)
    finally:
        connection.close()

# 初始化数据库
init_database()

# ======================
# 前端访问（相对路径，任何环境都能运行）
# ======================
@app.route('/')
def serve_frontend():
    logger.info("【访问】根路径，返回 index.html")
    return send_from_directory('../frontend', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    logger.debug(f"【访问】静态文件: {path}")
    return send_from_directory('../frontend', path)

# 登录接口
@app.route('/api/login', methods=['POST'])
def login():
    endpoint = '/api/login'
    method = 'POST'
    
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')
        
        log_request(logger, endpoint, method, data={'username': username})
        
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                log_db_operation(logger, 'SELECT', 'users', condition=f'username={username}')
                cursor.execute('SELECT * FROM users WHERE username = %s AND password = %s', (username, password))
                user = cursor.fetchone()
                if user:
                    log_response(logger, endpoint, True, '登录成功')
                    return jsonify({'success': True, 'message': '登录成功'})
                else:
                    log_response(logger, endpoint, False, '用户名或密码错误')
                    return jsonify({'success': False, 'message': '用户名或密码错误'})
        finally:
            connection.close()
    except Exception as e:
        log_error(logger, endpoint, str(e), exc_info=True)
        return jsonify({'success': False, 'message': f'登录失败: {str(e)}'})

# 项目管理接口 - 一对多模式

# 获取项目列表
@app.route('/api/projects', methods=['GET'])
def get_projects():
    endpoint = '/api/projects'
    method = 'GET'
    
    try:
        name = request.args.get('name')
        log_request(logger, endpoint, method, params={'name': name})
        
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                if name:
                    log_db_operation(logger, 'SELECT', 'projects', condition=f'name LIKE %{name}%')
                    cursor.execute('SELECT * FROM projects WHERE name LIKE %s AND is_deleted = 0', ('%' + name + '%',))
                else:
                    log_db_operation(logger, 'SELECT', 'projects')
                    cursor.execute('SELECT * FROM projects WHERE is_deleted = 0')
                projects = cursor.fetchall()
                
                logger.info(f"【查询】找到 {len(projects)} 个项目")
                
                # 为每个项目获取关联的材质
                for project in projects:
                    log_db_operation(logger, 'SELECT', 'materials', condition=f'project_id={project["id"]}')
                    cursor.execute('SELECT * FROM materials WHERE project_id = %s AND is_deleted = 0', (project['id'],))
                    project['materials'] = cursor.fetchall()
                
                log_response(logger, endpoint, True, f'获取到 {len(projects)} 个项目')
                return jsonify({'success': True, 'data': projects})
        finally:
            connection.close()
    except Exception as e:
        log_error(logger, endpoint, str(e), exc_info=True)
        return jsonify({'success': False, 'message': f'获取项目列表失败: {str(e)}'})

# 添加项目
@app.route('/api/projects', methods=['POST'])
def add_project():
    endpoint = '/api/projects'
    method = 'POST'
    
    try:
        data = request.json
        name = data.get('name')
        
        log_request(logger, endpoint, method, data={'name': name})
        
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                # 检查项目名称是否已存在
                log_db_operation(logger, 'SELECT', 'projects', condition=f'name={name}')
                cursor.execute('SELECT * FROM projects WHERE name = %s AND is_deleted = 0', (name,))
                if cursor.fetchone():
                    logger.warning(f"【警告】项目名称 '{name}' 已存在")
                    return jsonify({'success': False, 'message': '项目名称已存在'})
                
                # 插入新项目
                log_db_operation(logger, 'INSERT', 'projects', data={'name': name})
                cursor.execute('INSERT INTO projects (name) VALUES (%s)', (name,))
                project_id = cursor.lastrowid
                connection.commit()
                
                logger.info(f"【成功】项目 '{name}' 创建成功，ID: {project_id}")
                log_response(logger, endpoint, True, '项目添加成功', {'project_id': project_id})
                return jsonify({'success': True, 'message': '项目添加成功', 'project_id': project_id})
        finally:
            connection.close()
    except Exception as e:
        log_error(logger, endpoint, str(e), exc_info=True)
        return jsonify({'success': False, 'message': f'添加项目失败: {str(e)}'})

# 获取项目详情
@app.route('/api/projects/<int:project_id>', methods=['GET'])
def get_project(project_id):
    endpoint = f'/api/projects/{project_id}'
    method = 'GET'
    
    try:
        log_request(logger, endpoint, method)
        
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                # 获取项目信息
                log_db_operation(logger, 'SELECT', 'projects', condition=f'id={project_id}')
                cursor.execute('SELECT * FROM projects WHERE id = %s AND is_deleted = 0', (project_id,))
                project = cursor.fetchone()
                if not project:
                    logger.warning(f"【警告】项目 ID {project_id} 不存在")
                    return jsonify({'success': False, 'message': '项目不存在'})
                
                # 获取关联的材质
                log_db_operation(logger, 'SELECT', 'materials', condition=f'project_id={project_id}')
                cursor.execute('SELECT * FROM materials WHERE project_id = %s AND is_deleted = 0', (project_id,))
                project['materials'] = cursor.fetchall()
                
                logger.info(f"【查询】项目 '{project['name']}' 详情获取成功")
                log_response(logger, endpoint, True, '获取项目详情成功')
                return jsonify({'success': True, 'data': project})
        finally:
            connection.close()
    except Exception as e:
        log_error(logger, endpoint, str(e), exc_info=True)
        return jsonify({'success': False, 'message': f'获取项目详情失败: {str(e)}'})

# 更新项目
@app.route('/api/projects/<int:project_id>', methods=['PUT'])
def update_project(project_id):
    endpoint = f'/api/projects/{project_id}'
    method = 'PUT'
    
    try:
        data = request.json
        name = data.get('name')
        
        log_request(logger, endpoint, method, data={'name': name})
        
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                # 检查项目是否存在
                log_db_operation(logger, 'SELECT', 'projects', condition=f'id={project_id}')
                cursor.execute('SELECT * FROM projects WHERE id = %s AND is_deleted = 0', (project_id,))
                if not cursor.fetchone():
                    logger.warning(f"【警告】项目 ID {project_id} 不存在")
                    return jsonify({'success': False, 'message': '项目不存在'})
                
                # 检查新名称是否已被其他项目使用
                log_db_operation(logger, 'SELECT', 'projects', condition=f'name={name}, id!={project_id}')
                cursor.execute('SELECT * FROM projects WHERE name = %s AND id != %s AND is_deleted = 0', (name, project_id))
                if cursor.fetchone():
                    logger.warning(f"【警告】项目名称 '{name}' 已被其他项目使用")
                    return jsonify({'success': False, 'message': '项目名称已存在'})
                
                # 更新项目名称
                log_db_operation(logger, 'UPDATE', 'projects', data={'name': name}, condition=f'id={project_id}')
                cursor.execute('UPDATE projects SET name = %s WHERE id = %s', (name, project_id))
                connection.commit()
                
                logger.info(f"【成功】项目 ID {project_id} 更新为 '{name}'")
                log_response(logger, endpoint, True, '项目更新成功')
                return jsonify({'success': True, 'message': '项目更新成功'})
        finally:
            connection.close()
    except Exception as e:
        log_error(logger, endpoint, str(e), exc_info=True)
        return jsonify({'success': False, 'message': f'更新项目失败: {str(e)}'})

# 删除项目
@app.route('/api/projects/<int:project_id>', methods=['DELETE'])
def delete_project(project_id):
    endpoint = f'/api/projects/{project_id}'
    method = 'DELETE'
    
    try:
        log_request(logger, endpoint, method)
        
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                # 软删除项目（级联删除材质）
                log_db_operation(logger, 'UPDATE', 'projects', data={'is_deleted': 1}, condition=f'id={project_id}')
                cursor.execute('UPDATE projects SET is_deleted = 1 WHERE id = %s', (project_id,))
                connection.commit()
                
                logger.info(f"【成功】项目 ID {project_id} 已软删除")
                log_response(logger, endpoint, True, '项目删除成功')
                return jsonify({'success': True, 'message': '项目删除成功'})
        finally:
            connection.close()
    except Exception as e:
        log_error(logger, endpoint, str(e), exc_info=True)
        return jsonify({'success': False, 'message': f'删除项目失败: {str(e)}'})

# 材质管理接口

# 添加材质
@app.route('/api/materials', methods=['POST'])
def add_material():
    endpoint = '/api/materials'
    method = 'POST'
    
    try:
        data = request.json
        project_id = data.get('project_id')
        material = data.get('material')
        purchase_price = data.get('purchase_price')
        selling_price = data.get('selling_price')
        stock = data.get('stock', 0)
        note = data.get('note')
        
        log_request(logger, endpoint, method, data={
            'project_id': project_id,
            'material': material,
            'purchase_price': purchase_price,
            'selling_price': selling_price
        })
        
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                # 检查项目是否存在
                log_db_operation(logger, 'SELECT', 'projects', condition=f'id={project_id}')
                cursor.execute('SELECT * FROM projects WHERE id = %s AND is_deleted = 0', (project_id,))
                project = cursor.fetchone()
                if not project:
                    logger.warning(f"【警告】项目 ID {project_id} 不存在")
                    return jsonify({'success': False, 'message': '项目不存在'})
                
                # 检查材质是否已存在
                log_db_operation(logger, 'SELECT', 'materials', condition=f'project_id={project_id}, material={material}')
                cursor.execute('SELECT * FROM materials WHERE project_id = %s AND material = %s AND is_deleted = 0', (project_id, material))
                if cursor.fetchone():
                    logger.warning(f"【警告】材质 '{material}' 已存在于项目 ID {project_id}")
                    return jsonify({'success': False, 'message': '材质已存在'})
                
                # 插入新材质
                log_db_operation(logger, 'INSERT', 'materials', data={
                    'project_id': project_id,
                    'material': material,
                    'purchase_price': purchase_price,
                    'selling_price': selling_price
                })
                cursor.execute('''
                INSERT INTO materials (project_id, material, purchase_price, selling_price, stock, note)
                VALUES (%s, %s, %s, %s, %s, %s)
                ''', (project_id, material, purchase_price, selling_price, stock, note))
                
                # 记录初始价格轨迹
                cursor.execute('''
                INSERT INTO price_history (project_name, material, purchase_price, selling_price, update_method)
                VALUES (%s, %s, %s, %s, 'manual')
                ''', (project['name'], material, purchase_price, selling_price))
                
                connection.commit()
                
                logger.info(f"【成功】材质 '{material}' 添加到项目 '{project['name']}'，并记录初始价格轨迹")
                log_response(logger, endpoint, True, '材质添加成功')
                return jsonify({'success': True, 'message': '材质添加成功'})
        finally:
            connection.close()
    except Exception as e:
        log_error(logger, endpoint, str(e), exc_info=True)
        return jsonify({'success': False, 'message': f'添加材质失败: {str(e)}'})

# 更新材质
@app.route('/api/materials/<int:material_id>', methods=['PUT'])
def update_material(material_id):
    endpoint = f'/api/materials/{material_id}'
    method = 'PUT'
    
    try:
        data = request.json
        material = data.get('material')
        purchase_price = data.get('purchase_price')
        selling_price = data.get('selling_price')
        stock = data.get('stock', 0)
        note = data.get('note')
        
        log_request(logger, endpoint, method, data={
            'material': material,
            'purchase_price': purchase_price,
            'selling_price': selling_price
        })
        
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                # 检查材质是否存在
                log_db_operation(logger, 'SELECT', 'materials', condition=f'id={material_id}')
                cursor.execute('SELECT * FROM materials WHERE id = %s AND is_deleted = 0', (material_id,))
                existing_material = cursor.fetchone()
                if not existing_material:
                    logger.warning(f"【警告】材质 ID {material_id} 不存在")
                    return jsonify({'success': False, 'message': '材质不存在'})
                
                # 检查新材质名称是否已被同一项目使用
                if material and material != existing_material['material']:
                    log_db_operation(logger, 'SELECT', 'materials', condition=f'project_id={existing_material["project_id"]}, material={material}')
                    cursor.execute('''
                    SELECT * FROM materials WHERE project_id = %s AND material = %s AND id != %s AND is_deleted = 0
                    ''', (existing_material['project_id'], material, material_id))
                    if cursor.fetchone():
                        logger.warning(f"【警告】材质 '{material}' 已存在于该项目")
                        return jsonify({'success': False, 'message': '材质已存在'})
                
                # 记录价格变化
                old_purchase_price = existing_material['purchase_price']
                old_selling_price = existing_material['selling_price']
                
                # 更新材质信息
                log_db_operation(logger, 'UPDATE', 'materials', data={
                    'material': material,
                    'purchase_price': purchase_price,
                    'selling_price': selling_price
                }, condition=f'id={material_id}')
                cursor.execute('''
                UPDATE materials SET material = %s, purchase_price = %s, selling_price = %s, stock = %s, note = %s
                WHERE id = %s
                ''', (material, purchase_price, selling_price, stock, note, material_id))
                
                # 如果价格发生变化，记录价格轨迹
                if old_purchase_price != purchase_price or old_selling_price != selling_price:
                    # 获取项目名称
                    cursor.execute('SELECT name FROM projects WHERE id = %s', (existing_material['project_id'],))
                    project = cursor.fetchone()
                    if project:
                        log_price_update(logger, project['name'], material, 
                                       f'{old_purchase_price}/{old_selling_price}', 
                                       f'{purchase_price}/{selling_price}', 'manual')
                        
                        cursor.execute('''
                        INSERT INTO price_history (project_name, material, purchase_price, selling_price, update_method)
                        VALUES (%s, %s, %s, %s, 'manual')
                        ''', (project['name'], material, purchase_price, selling_price))
                
                connection.commit()
                
                logger.info(f"【成功】材质 ID {material_id} 更新成功")
                log_response(logger, endpoint, True, '材质更新成功')
                return jsonify({'success': True, 'message': '材质更新成功'})
        finally:
            connection.close()
    except Exception as e:
        log_error(logger, endpoint, str(e), exc_info=True)
        return jsonify({'success': False, 'message': f'更新材质失败: {str(e)}'})

# 删除材质
@app.route('/api/materials/<int:material_id>', methods=['DELETE'])
def delete_material(material_id):
    endpoint = f'/api/materials/{material_id}'
    method = 'DELETE'
    
    try:
        log_request(logger, endpoint, method)
        
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                # 软删除材质
                log_db_operation(logger, 'UPDATE', 'materials', data={'is_deleted': 1}, condition=f'id={material_id}')
                cursor.execute('UPDATE materials SET is_deleted = 1 WHERE id = %s', (material_id,))
                connection.commit()
                
                logger.info(f"【成功】材质 ID {material_id} 已软删除")
                log_response(logger, endpoint, True, '材质删除成功')
                return jsonify({'success': True, 'message': '材质删除成功'})
        finally:
            connection.close()
    except Exception as e:
        log_error(logger, endpoint, str(e), exc_info=True)
        return jsonify({'success': False, 'message': f'删除材质失败: {str(e)}'})

# 兼容旧接口（用于前端过渡）
@app.route('/api/items', methods=['GET'])
def get_items():
    endpoint = '/api/items'
    method = 'GET'
    
    try:
        name = request.args.get('name')
        log_request(logger, endpoint, method, params={'name': name})
        
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                if name:
                    log_db_operation(logger, 'SELECT', 'items', condition=f'name LIKE %{name}%')
                    cursor.execute('SELECT * FROM items WHERE name LIKE %s AND is_deleted = 0', ('%' + name + '%',))
                else:
                    log_db_operation(logger, 'SELECT', 'items')
                    cursor.execute('SELECT * FROM items WHERE is_deleted = 0')
                items = cursor.fetchall()
                
                logger.info(f"【查询】找到 {len(items)} 个旧表项目")
                log_response(logger, endpoint, True, f'获取到 {len(items)} 个项目')
                return jsonify({'success': True, 'data': items})
        finally:
            connection.close()
    except Exception as e:
        log_error(logger, endpoint, str(e), exc_info=True)
        return jsonify({'success': False, 'message': f'获取项目列表失败: {str(e)}'})

@app.route('/api/items', methods=['POST'])
def add_item():
    endpoint = '/api/items'
    method = 'POST'
    
    try:
        data = request.json
        name = data.get('name')
        purchase_price = data.get('purchase_price')
        selling_price = data.get('selling_price')
        stock = data.get('stock')
        note = data.get('note')
        material = data.get('material')
        
        log_request(logger, endpoint, method, data={'name': name, 'material': material})
        
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                if material:
                    log_db_operation(logger, 'SELECT', 'items', condition=f'name={name}, material={material}')
                    cursor.execute('''
                    SELECT * FROM items WHERE name = %s AND material = %s AND is_deleted = 0
                    ''', (name, material))
                else:
                    log_db_operation(logger, 'SELECT', 'items', condition=f'name={name}')
                    cursor.execute('''
                    SELECT * FROM items WHERE name = %s AND (material IS NULL OR material = '') AND is_deleted = 0
                    ''', (name,))
                
                if cursor.fetchone():
                    logger.warning(f"【警告】项目 '{name}' 已存在")
                    return jsonify({'success': False, 'message': '项目名称已存在'})
                
                log_db_operation(logger, 'INSERT', 'items', data={'name': name, 'material': material})
                cursor.execute('''
                INSERT INTO items (name, purchase_price, selling_price, stock, note, material)
                VALUES (%s, %s, %s, %s, %s, %s)
                ''', (name, purchase_price, selling_price, stock or 0, note, material))
                connection.commit()
                
                logger.info(f"【成功】项目 '{name}' 添加到旧表")
                log_response(logger, endpoint, True, '项目添加成功')
                return jsonify({'success': True, 'message': '项目添加成功'})
        finally:
            connection.close()
    except Exception as e:
        log_error(logger, endpoint, str(e), exc_info=True)
        return jsonify({'success': False, 'message': f'添加项目失败: {str(e)}'})

@app.route('/api/items/<int:item_id>', methods=['GET'])
def get_item(item_id):
    endpoint = f'/api/items/{item_id}'
    method = 'GET'
    
    try:
        log_request(logger, endpoint, method)
        
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                log_db_operation(logger, 'SELECT', 'items', condition=f'id={item_id}')
                cursor.execute('''
                SELECT * FROM items WHERE id = %s AND is_deleted = 0
                ''', (item_id,))
                item = cursor.fetchone()
                if item:
                    log_response(logger, endpoint, True, '获取项目成功')
                    return jsonify({'success': True, 'data': item})
                else:
                    logger.warning(f"【警告】项目 ID {item_id} 不存在")
                    return jsonify({'success': False, 'message': '项目不存在'})
        finally:
            connection.close()
    except Exception as e:
        log_error(logger, endpoint, str(e), exc_info=True)
        return jsonify({'success': False, 'message': f'获取项目失败: {str(e)}'})

@app.route('/api/items/<int:item_id>', methods=['PUT'])
def update_item(item_id):
    endpoint = f'/api/items/{item_id}'
    method = 'PUT'
    
    try:
        data = request.json
        name = data.get('name')
        purchase_price = data.get('purchase_price')
        selling_price = data.get('selling_price')
        stock = data.get('stock')
        note = data.get('note')
        material = data.get('material')
        
        log_request(logger, endpoint, method, data={'name': name, 'material': material})
        
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                if material:
                    log_db_operation(logger, 'SELECT', 'items', condition=f'name={name}, material={material}, id!={item_id}')
                    cursor.execute('''
                    SELECT * FROM items WHERE name = %s AND material = %s AND id != %s AND is_deleted = 0
                    ''', (name, material, item_id))
                else:
                    log_db_operation(logger, 'SELECT', 'items', condition=f'name={name}, id!={item_id}')
                    cursor.execute('''
                    SELECT * FROM items WHERE name = %s AND (material IS NULL OR material = '') AND id != %s AND is_deleted = 0
                    ''', (name, item_id))
                
                if cursor.fetchone():
                    logger.warning(f"【警告】项目名称 '{name}' 已存在")
                    return jsonify({'success': False, 'message': '项目名称已存在'})
                
                log_db_operation(logger, 'UPDATE', 'items', data={'name': name}, condition=f'id={item_id}')
                cursor.execute('''
                UPDATE items SET name = %s, purchase_price = %s, selling_price = %s, stock = %s, note = %s, material = %s
                WHERE id = %s
                ''', (name, purchase_price, selling_price, stock or 0, note, material, item_id))
                connection.commit()
                
                logger.info(f"【成功】项目 ID {item_id} 更新成功")
                log_response(logger, endpoint, True, '项目更新成功')
                return jsonify({'success': True, 'message': '项目更新成功'})
        finally:
            connection.close()
    except Exception as e:
        log_error(logger, endpoint, str(e), exc_info=True)
        return jsonify({'success': False, 'message': f'更新项目失败: {str(e)}'})

@app.route('/api/items/<int:item_id>', methods=['DELETE'])
def delete_item(item_id):
    endpoint = f'/api/items/{item_id}'
    method = 'DELETE'
    
    try:
        log_request(logger, endpoint, method)
        
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                log_db_operation(logger, 'UPDATE', 'items', data={'is_deleted': 1}, condition=f'id={item_id}')
                cursor.execute('''
                UPDATE items SET is_deleted = 1
                WHERE id = %s
                ''', (item_id,))
                connection.commit()
                
                logger.info(f"【成功】项目 ID {item_id} 已软删除")
                log_response(logger, endpoint, True, '项目删除成功')
                return jsonify({'success': True, 'message': '项目删除成功'})
        finally:
            connection.close()
    except Exception as e:
        log_error(logger, endpoint, str(e), exc_info=True)
        return jsonify({'success': False, 'message': f'删除项目失败: {str(e)}'})

# 订单管理接口
@app.route('/api/orders', methods=['GET'])
def get_orders():
    endpoint = '/api/orders'
    method = 'GET'
    
    try:
        log_request(logger, endpoint, method)
        
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                log_db_operation(logger, 'SELECT', 'orders')
                cursor.execute('''
                SELECT o.*, COUNT(oi.id) as item_count 
                FROM orders o
                LEFT JOIN order_items oi ON o.id = oi.order_id
                GROUP BY o.id
                ORDER BY o.created_at DESC
                ''')
                orders = cursor.fetchall()
                
                logger.info(f"【查询】找到 {len(orders)} 个订单")
                log_response(logger, endpoint, True, f'获取到 {len(orders)} 个订单')
                return jsonify({'success': True, 'data': orders})
        finally:
            connection.close()
    except Exception as e:
        log_error(logger, endpoint, str(e), exc_info=True)
        return jsonify({'success': False, 'message': f'获取订单列表失败: {str(e)}'})

# 创建项目的辅助函数
def create_project(cursor, project_name):
    try:
        logger.info(f"【辅助函数】create_project 被调用: {project_name}")
        # 检查项目是否存在
        cursor.execute('''
        SELECT id FROM projects WHERE name = %s AND is_deleted = 0
        ''', (project_name,))
        project = cursor.fetchone()
        
        if not project:
            # 创建新项目
            logger.info(f"【辅助函数】创建项目: {project_name}")
            cursor.execute("INSERT INTO projects (name) VALUES (%s)", (project_name,))
            project_id = cursor.lastrowid
            logger.info(f"【辅助函数】项目创建成功，ID: {project_id}")
            return project_id
        else:
            logger.info(f"【辅助函数】项目已存在，ID: {project['id']}")
            return project['id']
    except Exception as e:
        logger.error(f"【辅助函数】create_project 错误: {e}", exc_info=True)
        return 1

# 创建材质的辅助函数
def create_material(cursor, project_id, material_name, purchase_price, selling_price, stock, note, source):
    try:
        logger.info(f"【辅助函数】create_material 被调用: project_id={project_id}, material={material_name}")
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
            logger.info(f"【辅助函数】材质创建成功: {material_name}")
        else:
            logger.info(f"【辅助函数】材质已存在: {material_name}")
    except Exception as e:
        logger.error(f"【辅助函数】create_material 错误: {e}", exc_info=True)

@app.route('/api/orders', methods=['POST'])
def add_order():
    endpoint = '/api/orders'
    method = 'POST'
    
    try:
        data = request.json
        customer_name = data.get('customer_name')
        phone = data.get('phone')
        paid_amount = data.get('paid_amount')
        order_items = data.get('items')
        
        log_request(logger, endpoint, method, data={
            'customer_name': customer_name,
            'phone': phone,
            'item_count': len(order_items) if order_items else 0
        })
        
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                processed_items = []
                duplicate_items = []
                
                logger.info(f"【订单】开始处理 {len(order_items)} 个订单项目")
                
                for item in order_items:
                    if not item.get('item_id') and item.get('name'):
                        logger.info(f"【订单】处理非系统项目: {item['name']}")
                        # 检查项目是否存在
                        cursor.execute('''
                        SELECT id FROM projects WHERE name = %s AND is_deleted = 0
                        ''', (item['name'],))
                        project = cursor.fetchone()
                        
                        if not project:
                            # 创建项目
                            logger.info(f"【订单】创建项目: {item['name']}")
                            cursor.execute("INSERT INTO projects (name) VALUES (%s)", (item['name'],))
                            project_id = cursor.lastrowid
                            logger.info(f"【订单】项目创建成功，ID: {project_id}")
                        else:
                            project_id = project['id']
                            logger.info(f"【订单】使用已有项目，ID: {project_id}")
                        
                        # 检查材质是否存在
                        cursor.execute('''
                        SELECT id FROM materials WHERE project_id = %s AND material = %s AND is_deleted = 0
                        ''', (project_id, item.get('material', '')))
                        material = cursor.fetchone()
                        
                        if not material:
                            # 创建材质
                            logger.info(f"【订单】创建材质: {item.get('material', '')}")
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
                                logger.info(f"【订单】价格发生变化，更新项目 ID {item_id}")
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
                                logger.info(f"【订单】价格轨迹已记录: {item['name']} - {item.get('material', '')}")
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
                            logger.info(f"【订单】新项目初始价格轨迹已记录: {item['name']} - {item.get('material', '')}")
                        
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
                log_db_operation(logger, 'INSERT', 'orders', data={
                    'customer_name': customer_name,
                    'total_amount': total_amount
                })
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
                logger.info(f"【订单】订单创建成功，ID: {order_id}，总金额: {total_amount}")
                
                response = {
                    'success': True,
                    'message': '订单添加成功',
                    'order_id': order_id
                }
                if duplicate_items:
                    response['duplicate_items'] = duplicate_items
                
                log_response(logger, endpoint, True, f'订单创建成功，ID: {order_id}')
                return jsonify(response)
        finally:
            connection.close()
    except Exception as e:
        log_error(logger, endpoint, str(e), exc_info=True)
        return jsonify({'success': False, 'message': f'添加订单失败: {str(e)}'})

@app.route('/api/orders/<int:order_id>', methods=['GET'])
def get_order_detail(order_id):
    endpoint = f'/api/orders/{order_id}'
    method = 'GET'
    
    try:
        log_request(logger, endpoint, method)
        
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                log_db_operation(logger, 'SELECT', 'orders', condition=f'id={order_id}')
                cursor.execute('SELECT * FROM orders WHERE id = %s', (order_id,))
                order = cursor.fetchone()
                
                log_db_operation(logger, 'SELECT', 'order_items', condition=f'order_id={order_id}')
                cursor.execute('''
                SELECT * FROM order_items 
                WHERE order_id = %s
                ''', (order_id,))
                items = cursor.fetchall()
                
                order['items'] = items
                
                logger.info(f"【查询】订单 ID {order_id} 详情获取成功，包含 {len(items)} 个项目")
                log_response(logger, endpoint, True, '获取订单详情成功')
                return jsonify({'success': True, 'data': order})
        finally:
            connection.close()
    except Exception as e:
        log_error(logger, endpoint, str(e), exc_info=True)
        return jsonify({'success': False, 'message': f'获取订单详情失败: {str(e)}'})

# 获取价格轨迹
@app.route('/api/price-history', methods=['GET'])
def get_price_history():
    endpoint = '/api/price-history'
    method = 'GET'
    
    try:
        project_name = request.args.get('project_name')
        material = request.args.get('material')
        
        log_request(logger, endpoint, method, params={
            'project_name': project_name,
            'material': material
        })
        
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                if project_name and material:
                    log_db_operation(logger, 'SELECT', 'price_history', condition=f'project_name={project_name}, material={material}')
                    cursor.execute('''
                    SELECT * FROM price_history 
                    WHERE project_name = %s AND material = %s 
                    ORDER BY update_time DESC
                    ''', (project_name, material))
                else:
                    logger.warning("【警告】缺少项目名称或材质参数")
                    return jsonify({'success': False, 'message': '缺少项目名称或材质参数'})
                
                history = cursor.fetchall()
                
                logger.info(f"【查询】找到 {len(history)} 条价格轨迹记录: {project_name} - {material}")
                log_response(logger, endpoint, True, f'获取到 {len(history)} 条价格轨迹')
                return jsonify({'success': True, 'data': history})
        finally:
            connection.close()
    except Exception as e:
        log_error(logger, endpoint, str(e), exc_info=True)
        return jsonify({'success': False, 'message': f'获取价格轨迹失败: {str(e)}'})

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
            logger.info("【系统】销售记录表初始化成功")
    except Exception as e:
        logger.error(f"【系统】初始化销售记录表失败: {e}", exc_info=True)
    finally:
        connection.close()

# 初始化销售记录表
init_sales_tables()

# 获取销售记录列表
@app.route('/api/sales', methods=['GET'])
def get_sales_records():
    endpoint = '/api/sales'
    method = 'GET'
    
    try:
        search = request.args.get('search', '')
        start_date = request.args.get('start_date', '')
        end_date = request.args.get('end_date', '')
        
        log_request(logger, endpoint, method, params={
            'search': search,
            'start_date': start_date,
            'end_date': end_date
        })
        
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
                
                log_db_operation(logger, 'SELECT', 'sales_records')
                cursor.execute(query, params)
                records = cursor.fetchall()
                
                logger.info(f"【查询】找到 {len(records)} 条销售记录")
                log_response(logger, endpoint, True, f'获取到 {len(records)} 条销售记录')
                return jsonify({'success': True, 'data': records})
        finally:
            connection.close()
    except Exception as e:
        log_error(logger, endpoint, str(e), exc_info=True)
        return jsonify({'success': False, 'message': f'获取销售记录失败: {str(e)}'})

# 获取单个销售记录详情
@app.route('/api/sales/<int:sales_id>', methods=['GET'])
def get_sales_record(sales_id):
    endpoint = f'/api/sales/{sales_id}'
    method = 'GET'
    
    try:
        log_request(logger, endpoint, method)
        
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                # 获取主记录
                log_db_operation(logger, 'SELECT', 'sales_records', condition=f'id={sales_id}')
                cursor.execute('''
                SELECT * FROM sales_records 
                WHERE id = %s AND is_deleted = 0
                ''', (sales_id,))
                record = cursor.fetchone()
                
                if not record:
                    logger.warning(f"【警告】销售记录 ID {sales_id} 不存在")
                    return jsonify({'success': False, 'message': '销售记录不存在'})
                
                # 获取项目明细
                log_db_operation(logger, 'SELECT', 'sales_items', condition=f'sales_id={sales_id}')
                cursor.execute('''
                SELECT * FROM sales_items 
                WHERE sales_id = %s
                ''', (sales_id,))
                items = cursor.fetchall()
                
                record['items'] = items
                
                logger.info(f"【查询】销售记录 ID {sales_id} 详情获取成功，包含 {len(items)} 个项目")
                log_response(logger, endpoint, True, '获取销售记录详情成功')
                return jsonify({'success': True, 'data': record})
        finally:
            connection.close()
    except Exception as e:
        log_error(logger, endpoint, str(e), exc_info=True)
        return jsonify({'success': False, 'message': f'获取销售记录详情失败: {str(e)}'})

# 创建销售记录
@app.route('/api/sales', methods=['POST'])
def create_sales_record():
    endpoint = '/api/sales'
    method = 'POST'
    
    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        record_type = data.get('type', 'sale')
        note = data.get('note', '').strip()
        items = data.get('items', [])
        
        log_request(logger, endpoint, method, data={
            'name': name,
            'type': record_type,
            'item_count': len(items)
        })
        
        if not name:
            logger.warning("【警告】销售记录名称为空")
            return jsonify({'success': False, 'message': '名称不能为空'})
        
        if not items:
            logger.warning("【警告】销售记录没有项目")
            return jsonify({'success': False, 'message': '请至少添加一个项目'})
        
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                # 计算总金额
                total_amount = sum(item.get('selling_price', 0) * item.get('quantity', 1) for item in items)
                
                # 插入主记录
                log_db_operation(logger, 'INSERT', 'sales_records', data={
                    'name': name,
                    'type': record_type,
                    'total_amount': total_amount
                })
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
                    
                    if is_system_item and item_id:
                        # 系统项目：更新价格和轨迹
                        cursor.execute('''
                        SELECT m.id, m.purchase_price, m.selling_price, p.name as project_name
                        FROM materials m
                        JOIN projects p ON m.project_id = p.id
                        WHERE m.id = %s AND m.is_deleted = 0 AND p.is_deleted = 0
                        ''', (item_id,))
                        material_info = cursor.fetchone()
                        
                        if material_info:
                            material_id = material_info['id']
                            current_purchase_price = material_info['purchase_price']
                            current_selling_price = material_info['selling_price']
                            project_name = material_info['project_name']
                            
                            # 检查价格是否发生变化
                            if current_purchase_price != purchase_price or current_selling_price != selling_price:
                                logger.info(f"【销售】系统项目价格变化: {project_name} - {material}")
                                # 更新材质价格
                                cursor.execute('''
                                UPDATE materials SET purchase_price = %s, selling_price = %s
                                WHERE id = %s
                                ''', (purchase_price, selling_price, material_id))
                                
                                # 记录价格轨迹
                                cursor.execute('''
                                INSERT INTO price_history (project_name, material, purchase_price, selling_price, update_method)
                                VALUES (%s, %s, %s, %s, 'auto')
                                ''', (project_name, material, purchase_price, selling_price))
                                logger.info(f"【销售】价格轨迹已记录: {project_name} - {material}")
                    elif not is_system_item and item_name:
                        # 非系统项目：检查是否需要添加到项目管理
                        logger.info(f"【销售】处理非系统项目: {item_name}")
                        # 检查项目是否已存在
                        cursor.execute('''
                        SELECT id FROM projects WHERE name = %s AND is_deleted = 0
                        ''', (item_name,))
                        project = cursor.fetchone()
                        
                        if not project:
                            # 创建新项目
                            logger.info(f"【销售】创建项目: {item_name}")
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
                            logger.info(f"【销售】新项目初始价格轨迹已记录: {item_name} - {material or '默认'}")
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
                                    logger.info(f"【销售】材质价格变化: {item_name} - {material or '默认'}")
                                    cursor.execute('''
                                    UPDATE materials SET purchase_price = %s, selling_price = %s
                                    WHERE id = %s
                                    ''', (purchase_price, selling_price, existing_material['id']))
                                    
                                    # 记录价格轨迹
                                    cursor.execute('''
                                    INSERT INTO price_history (project_name, material, purchase_price, selling_price, update_method)
                                    VALUES (%s, %s, %s, %s, 'auto')
                                    ''', (item_name, material or '默认', purchase_price, selling_price))
                                    logger.info(f"【销售】价格轨迹已记录: {item_name} - {material or '默认'}")
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
                logger.info(f"【销售】销售记录创建成功，ID: {sales_id}，总金额: {total_amount}")
                log_response(logger, endpoint, True, f'销售记录创建成功，ID: {sales_id}')
                return jsonify({'success': True, 'message': '销售记录创建成功', 'id': sales_id})
        except Exception as e:
            connection.rollback()
            raise e
        finally:
            connection.close()
    except Exception as e:
        log_error(logger, endpoint, str(e), exc_info=True)
        return jsonify({'success': False, 'message': f'创建失败: {str(e)}'})

# 更新销售记录
@app.route('/api/sales/<int:sales_id>', methods=['PUT'])
def update_sales_record(sales_id):
    endpoint = f'/api/sales/{sales_id}'
    method = 'PUT'
    
    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        record_type = data.get('type', 'sale')
        note = data.get('note', '').strip()
        items = data.get('items', [])
        
        log_request(logger, endpoint, method, data={
            'name': name,
            'type': record_type,
            'item_count': len(items)
        })
        
        if not name:
            logger.warning("【警告】销售记录名称为空")
            return jsonify({'success': False, 'message': '名称不能为空'})
        
        if not items:
            logger.warning("【警告】销售记录没有项目")
            return jsonify({'success': False, 'message': '请至少添加一个项目'})
        
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                # 检查记录是否存在
                log_db_operation(logger, 'SELECT', 'sales_records', condition=f'id={sales_id}')
                cursor.execute('''
                SELECT id FROM sales_records WHERE id = %s AND is_deleted = 0
                ''', (sales_id,))
                if not cursor.fetchone():
                    logger.warning(f"【警告】销售记录 ID {sales_id} 不存在")
                    return jsonify({'success': False, 'message': '销售记录不存在'})
                
                # 计算总金额
                total_amount = sum(item.get('selling_price', 0) * item.get('quantity', 1) for item in items)
                
                # 更新主记录
                log_db_operation(logger, 'UPDATE', 'sales_records', data={
                    'name': name,
                    'type': record_type,
                    'total_amount': total_amount
                }, condition=f'id={sales_id}')
                cursor.execute('''
                UPDATE sales_records SET name = %s, type = %s, note = %s, total_amount = %s
                WHERE id = %s
                ''', (name, record_type, note, total_amount, sales_id))
                
                # 删除旧的项目明细
                log_db_operation(logger, 'DELETE', 'sales_items', condition=f'sales_id={sales_id}')
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
                    
                    if is_system_item and item_id:
                        # 系统项目：更新价格和轨迹
                        cursor.execute('''
                        SELECT m.id, m.purchase_price, m.selling_price, p.name as project_name
                        FROM materials m
                        JOIN projects p ON m.project_id = p.id
                        WHERE m.id = %s AND m.is_deleted = 0 AND p.is_deleted = 0
                        ''', (item_id,))
                        material_info = cursor.fetchone()
                        
                        if material_info:
                            material_id = material_info['id']
                            current_purchase_price = material_info['purchase_price']
                            current_selling_price = material_info['selling_price']
                            project_name = material_info['project_name']
                            
                            # 检查价格是否发生变化
                            if current_purchase_price != purchase_price or current_selling_price != selling_price:
                                logger.info(f"【销售】系统项目价格变化: {project_name} - {material}")
                                # 更新材质价格
                                cursor.execute('''
                                UPDATE materials SET purchase_price = %s, selling_price = %s
                                WHERE id = %s
                                ''', (purchase_price, selling_price, material_id))
                                
                                # 记录价格轨迹
                                cursor.execute('''
                                INSERT INTO price_history (project_name, material, purchase_price, selling_price, update_method)
                                VALUES (%s, %s, %s, %s, 'auto')
                                ''', (project_name, material, purchase_price, selling_price))
                                logger.info(f"【销售】价格轨迹已记录: {project_name} - {material}")
                    elif not is_system_item and item_name:
                        # 非系统项目：检查是否需要添加到项目管理
                        logger.info(f"【销售】处理非系统项目: {item_name}")
                        # 检查项目是否已存在
                        cursor.execute('''
                        SELECT id FROM projects WHERE name = %s AND is_deleted = 0
                        ''', (item_name,))
                        project = cursor.fetchone()
                        
                        if not project:
                            # 创建新项目
                            logger.info(f"【销售】创建项目: {item_name}")
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
                            logger.info(f"【销售】新项目初始价格轨迹已记录: {item_name} - {material or '默认'}")
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
                                    logger.info(f"【销售】材质价格变化: {item_name} - {material or '默认'}")
                                    cursor.execute('''
                                    UPDATE materials SET purchase_price = %s, selling_price = %s
                                    WHERE id = %s
                                    ''', (purchase_price, selling_price, existing_material['id']))
                                    
                                    # 记录价格轨迹
                                    cursor.execute('''
                                    INSERT INTO price_history (project_name, material, purchase_price, selling_price, update_method)
                                    VALUES (%s, %s, %s, %s, 'auto')
                                    ''', (item_name, material or '默认', purchase_price, selling_price))
                                    logger.info(f"【销售】价格轨迹已记录: {item_name} - {material or '默认'}")
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
                logger.info(f"【销售】销售记录更新成功，ID: {sales_id}")
                log_response(logger, endpoint, True, '销售记录更新成功')
                return jsonify({'success': True, 'message': '销售记录更新成功'})
        except Exception as e:
            connection.rollback()
            raise e
        finally:
            connection.close()
    except Exception as e:
        log_error(logger, endpoint, str(e), exc_info=True)
        return jsonify({'success': False, 'message': f'更新失败: {str(e)}'})

# 删除销售记录（软删除）
@app.route('/api/sales/<int:sales_id>', methods=['DELETE'])
def delete_sales_record(sales_id):
    endpoint = f'/api/sales/{sales_id}'
    method = 'DELETE'
    
    try:
        log_request(logger, endpoint, method)
        
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                # 检查记录是否存在
                log_db_operation(logger, 'SELECT', 'sales_records', condition=f'id={sales_id}')
                cursor.execute('''
                SELECT id FROM sales_records WHERE id = %s AND is_deleted = 0
                ''', (sales_id,))
                if not cursor.fetchone():
                    logger.warning(f"【警告】销售记录 ID {sales_id} 不存在")
                    return jsonify({'success': False, 'message': '销售记录不存在'})
                
                # 软删除
                log_db_operation(logger, 'UPDATE', 'sales_records', data={'is_deleted': 1}, condition=f'id={sales_id}')
                cursor.execute('''
                UPDATE sales_records SET is_deleted = 1 WHERE id = %s
                ''', (sales_id,))
                
                connection.commit()
                logger.info(f"【销售】销售记录 ID {sales_id} 已软删除")
                log_response(logger, endpoint, True, '销售记录删除成功')
                return jsonify({'success': True, 'message': '销售记录删除成功'})
        except Exception as e:
            connection.rollback()
            raise e
        finally:
            connection.close()
    except Exception as e:
        log_error(logger, endpoint, str(e), exc_info=True)
        return jsonify({'success': False, 'message': f'删除失败: {str(e)}'})

if __name__ == '__main__':
    logger.info("【系统】Flask 应用启动")
    app.run(debug=True, host='0.0.0.0', port=5000)
