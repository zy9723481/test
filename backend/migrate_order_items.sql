-- 为order_items表添加人工费和系统项目标识字段
ALTER TABLE order_items ADD COLUMN is_labor_fee TINYINT(1) DEFAULT 0 COMMENT '是否为人工费项目';
ALTER TABLE order_items ADD COLUMN is_system_item TINYINT(1) DEFAULT 0 COMMENT '是否为系统项目';

-- 为现有记录设置默认值
UPDATE order_items SET is_labor_fee = 0 WHERE is_labor_fee IS NULL;
UPDATE order_items SET is_system_item = 0 WHERE is_system_item IS NULL;

-- 为is_labor_fee字段添加索引（可选）
CREATE INDEX idx_order_items_is_labor_fee ON order_items(is_labor_fee);

-- 为is_system_item字段添加索引（可选）
CREATE INDEX idx_order_items_is_system_item ON order_items(is_system_item);
