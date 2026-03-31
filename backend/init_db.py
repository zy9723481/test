from db import get_db_connection

def init_database():
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            # 创建用户表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY COMMENT '用户ID，主键自增',
                username VARCHAR(50) NOT NULL UNIQUE COMMENT '用户名，唯一',
                password VARCHAR(50) NOT NULL COMMENT '密码'
            ) COMMENT='用户表，存储系统登录用户信息'
            ''')
            
            # 创建项目表（只存储项目名称）
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS projects (
                id INT AUTO_INCREMENT PRIMARY KEY COMMENT '项目ID，主键自增',
                name VARCHAR(100) NOT NULL UNIQUE COMMENT '项目名称，唯一',
                is_deleted TINYINT(1) DEFAULT 0 COMMENT '软删除标记，0-未删除，1-已删除'
            ) COMMENT='项目表，存储水暖管件项目名称'
            ''')
            
            # 创建材质表（存储材质信息和与项目的关联）
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS materials (
                id INT AUTO_INCREMENT PRIMARY KEY COMMENT '材质ID，主键自增',
                project_id INT NOT NULL COMMENT '关联的项目ID',
                material VARCHAR(50) NOT NULL COMMENT '材质名称',
                purchase_price DECIMAL(10,2) NOT NULL COMMENT '进价',
                selling_price DECIMAL(10,2) NOT NULL COMMENT '销售价',
                stock INT NOT NULL DEFAULT 0 COMMENT '库存数量',
                note TEXT COMMENT '备注',
                is_deleted TINYINT(1) DEFAULT 0 COMMENT '软删除标记，0-未删除，1-已删除',
                source VARCHAR(50) DEFAULT 'normal' COMMENT '来源，normal-正常添加，order_add-订单添加，sales-销售记录添加',
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
                UNIQUE KEY unique_project_material (project_id, material)
            ) COMMENT='材质表，存储项目的材质信息及价格'
            ''')
            
            # 兼容旧表（用于数据迁移）
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS items (
                id INT AUTO_INCREMENT PRIMARY KEY COMMENT '项目ID，主键自增',
                name VARCHAR(100) NOT NULL COMMENT '项目名称',
                purchase_price DECIMAL(10,2) NOT NULL COMMENT '进价',
                selling_price DECIMAL(10,2) NOT NULL COMMENT '销售价',
                stock INT NOT NULL COMMENT '库存数量',
                note TEXT COMMENT '备注',
                material VARCHAR(50) COMMENT '材质',
                is_deleted TINYINT(1) DEFAULT 0 COMMENT '软删除标记，0-未删除，1-已删除',
                source VARCHAR(50) DEFAULT 'normal' COMMENT '来源，normal-正常添加，order_add-订单添加'
            ) COMMENT='项目表（旧表），用于兼容旧数据'
            ''')
            
            # 创建订单表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INT AUTO_INCREMENT PRIMARY KEY COMMENT '订单ID，主键自增',
                customer_name VARCHAR(100) NOT NULL COMMENT '客户名称',
                phone VARCHAR(20) COMMENT '客户手机号',
                total_amount DECIMAL(10,2) NOT NULL COMMENT '订单总金额',
                paid_amount DECIMAL(10,2) COMMENT '已支付金额',
                is_paid TINYINT(1) DEFAULT 0 COMMENT '结账状态，0-未结账，1-已结账',
                add_count INT DEFAULT 0 COMMENT '添加次数',
                note TEXT COMMENT '订单备注',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间'
            ) COMMENT='订单表，存储客户订单信息'
            ''')
            
            # 尝试添加note字段（如果不存在）
            try:
                cursor.execute('''
                ALTER TABLE orders ADD COLUMN note TEXT
                ''')
            except:
                # 字段已存在，忽略错误
                pass
            
            # 尝试添加phone字段（如果不存在）
            try:
                cursor.execute('''
                ALTER TABLE orders ADD COLUMN phone VARCHAR(20)
                ''')
            except:
                # 字段已存在，忽略错误
                pass
            
            # 尝试添加paid_amount字段（如果不存在）
            try:
                cursor.execute('''
                ALTER TABLE orders ADD COLUMN paid_amount DECIMAL(10,2)
                ''')
            except:
                # 字段已存在，忽略错误
                pass
            
            # 尝试添加is_paid字段（如果不存在）
            try:
                cursor.execute('''
                ALTER TABLE orders ADD COLUMN is_paid TINYINT(1) DEFAULT 0
                ''')
            except:
                # 字段已存在，忽略错误
                pass
            
            # 尝试添加paid_at字段（结账时间）
            try:
                cursor.execute('''
                ALTER TABLE orders ADD COLUMN paid_at TIMESTAMP NULL COMMENT '结账时间'
                ''')
            except:
                pass
            
            # 创建订单项目关联表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS order_items (
                id INT AUTO_INCREMENT PRIMARY KEY COMMENT '订单项目ID，主键自增',
                order_id INT NOT NULL COMMENT '关联的订单ID',
                item_id INT COMMENT '关联的项目ID（可为空）',
                name VARCHAR(100) NOT NULL COMMENT '项目名称',
                material VARCHAR(50) COMMENT '材质',
                purchase_price DECIMAL(10,2) NOT NULL COMMENT '进价',
                selling_price DECIMAL(10,2) NOT NULL COMMENT '销售价',
                note TEXT COMMENT '备注',
                quantity INT NOT NULL COMMENT '数量',
                price DECIMAL(10,2) NOT NULL COMMENT '单价',
                FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
                FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE SET NULL
            ) COMMENT='订单项目表，存储订单中的项目明细'
            ''')
            
            # 尝试添加缺失的字段（如果不存在）
            try:
                cursor.execute('''
                ALTER TABLE order_items ADD COLUMN name VARCHAR(100) NOT NULL
                ''')
            except:
                pass
            
            try:
                cursor.execute('''
                ALTER TABLE order_items ADD COLUMN material VARCHAR(50)
                ''')
            except:
                pass
            
            try:
                cursor.execute('''
                ALTER TABLE order_items ADD COLUMN purchase_price DECIMAL(10,2) NOT NULL
                ''')
            except:
                pass
            
            try:
                cursor.execute('''
                ALTER TABLE order_items ADD COLUMN selling_price DECIMAL(10,2) NOT NULL
                ''')
            except:
                pass
            
            try:
                cursor.execute('''
                ALTER TABLE order_items ADD COLUMN note TEXT
                ''')
            except:
                pass
            
            try:
                cursor.execute('''
                ALTER TABLE order_items MODIFY COLUMN item_id INT
                ''')
            except:
                pass
            
            # 创建价格轨迹表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS price_history (
                id INT AUTO_INCREMENT PRIMARY KEY COMMENT '轨迹ID，主键自增',
                project_name VARCHAR(255) NOT NULL COMMENT '项目名称',
                material VARCHAR(255) NOT NULL COMMENT '材质',
                purchase_price DECIMAL(10,2) NOT NULL COMMENT '进价',
                selling_price DECIMAL(10,2) NOT NULL COMMENT '销售价',
                update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '更新时间',
                update_method ENUM('manual', 'auto') NOT NULL COMMENT '更新方式，manual-手动，auto-自动',
                INDEX idx_project_material (project_name, material)
            ) COMMENT='价格轨迹表，记录价格变更历史'
            ''')
            
            # 创建销售记录主表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS sales_records (
                id INT AUTO_INCREMENT PRIMARY KEY COMMENT '销售记录ID，主键自增',
                name VARCHAR(255) NOT NULL COMMENT '销售记录名称',
                type ENUM('purchase', 'sale') NOT NULL COMMENT '类型，purchase-进货，sale-日常销售',
                note TEXT COMMENT '备注',
                total_amount DECIMAL(10,2) NOT NULL DEFAULT 0 COMMENT '总金额',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                is_deleted TINYINT(1) DEFAULT 0 COMMENT '软删除标记，0-未删除，1-已删除'
            ) COMMENT='销售记录表，存储进货和销售记录'
            ''')
            
            # 创建销售记录项目明细表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS sales_items (
                id INT AUTO_INCREMENT PRIMARY KEY COMMENT '销售项目ID，主键自增',
                sales_id INT NOT NULL COMMENT '关联的销售记录ID',
                item_id INT COMMENT '关联的系统项目ID（可为空）',
                is_system_item TINYINT(1) DEFAULT 0 COMMENT '是否系统项目，0-非系统项目，1-系统项目',
                name VARCHAR(255) NOT NULL COMMENT '项目名称',
                material VARCHAR(255) COMMENT '材质',
                purchase_price DECIMAL(10,2) NOT NULL DEFAULT 0 COMMENT '进价',
                selling_price DECIMAL(10,2) NOT NULL DEFAULT 0 COMMENT '销售价',
                quantity INT NOT NULL DEFAULT 1 COMMENT '数量',
                note TEXT COMMENT '备注',
                FOREIGN KEY (sales_id) REFERENCES sales_records(id) ON DELETE CASCADE
            ) COMMENT='销售项目表，存储销售记录中的项目明细'
            ''')
            
            # 插入默认管理员用户
            cursor.execute('''
            INSERT IGNORE INTO users (username, password) VALUES ('admin', 'admin')
            ''')
            
        connection.commit()
        print("数据库初始化成功")
    finally:
        connection.close()

if __name__ == "__main__":
    init_database()
