from db import get_db_connection

def init_database():
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            # 创建用户表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) NOT NULL UNIQUE,
                password VARCHAR(50) NOT NULL
            )
            ''')
            
            # 创建项目表（只存储项目名称）
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS projects (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL UNIQUE,
                is_deleted TINYINT(1) DEFAULT 0
            )
            ''')
            
            # 创建材质表（存储材质信息和与项目的关联）
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS materials (
                id INT AUTO_INCREMENT PRIMARY KEY,
                project_id INT NOT NULL,
                material VARCHAR(50) NOT NULL,
                purchase_price DECIMAL(10,2) NOT NULL,
                selling_price DECIMAL(10,2) NOT NULL,
                stock INT NOT NULL DEFAULT 0,
                note TEXT,
                is_deleted TINYINT(1) DEFAULT 0,
                source VARCHAR(50) DEFAULT 'normal',
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
                UNIQUE KEY unique_project_material (project_id, material)
            )
            ''')
            
            # 兼容旧表（用于数据迁移）
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS items (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                purchase_price DECIMAL(10,2) NOT NULL,
                selling_price DECIMAL(10,2) NOT NULL,
                stock INT NOT NULL,
                note TEXT,
                material VARCHAR(50),
                is_deleted TINYINT(1) DEFAULT 0,
                source VARCHAR(50) DEFAULT 'normal'
            )
            ''')
            
            # 创建订单表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INT AUTO_INCREMENT PRIMARY KEY,
                customer_name VARCHAR(100) NOT NULL,
                phone VARCHAR(20),
                total_amount DECIMAL(10,2) NOT NULL,
                paid_amount DECIMAL(10,2),
                is_paid TINYINT(1) DEFAULT 0,
                add_count INT DEFAULT 0,
                note TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
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
            
            # 创建订单项目关联表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS order_items (
                id INT AUTO_INCREMENT PRIMARY KEY,
                order_id INT NOT NULL,
                item_id INT,
                name VARCHAR(100) NOT NULL,
                material VARCHAR(50),
                purchase_price DECIMAL(10,2) NOT NULL,
                selling_price DECIMAL(10,2) NOT NULL,
                note TEXT,
                quantity INT NOT NULL,
                price DECIMAL(10,2) NOT NULL,
                FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
                FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE SET NULL
            )
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
