-- 创建价格轨迹表
CREATE TABLE IF NOT EXISTS price_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    project_name VARCHAR(255) NOT NULL,
    material VARCHAR(255) NOT NULL,
    purchase_price DECIMAL(10,2) NOT NULL,
    selling_price DECIMAL(10,2) NOT NULL,
    update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_method ENUM('manual', 'auto') NOT NULL,
    INDEX idx_project_material (project_name, material)
);