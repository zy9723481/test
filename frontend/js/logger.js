/**
 * 前端日志系统
 * 用于记录前端操作日志，方便调试和问题定位
 */

const Logger = (function() {
    'use strict';
    
    // 日志级别
    const LogLevel = {
        DEBUG: 0,
        INFO: 1,
        WARN: 2,
        ERROR: 3
    };
    
    // 当前日志级别
    let currentLevel = LogLevel.DEBUG;
    
    // 是否启用控制台输出
    let consoleOutput = true;
    
    // 是否启用本地存储
    let localStorageOutput = false;
    
    // 本地存储键名
    const STORAGE_KEY = 'app_logs';
    
    // 最大日志条数
    const MAX_LOGS = 1000;
    
    /**
     * 获取当前时间字符串
     */
    function getTimestamp() {
        const now = new Date();
        return now.toISOString().replace('T', ' ').substring(0, 19);
    }
    
    /**
     * 获取调用位置信息
     */
    function getCallerInfo() {
        try {
            const stack = new Error().stack;
            const lines = stack.split('\n');
            // 找到调用日志方法的行
            for (let i = 3; i < lines.length; i++) {
                const line = lines[i];
                if (line.includes('logger.js')) continue;
                const match = line.match(/at\s+(.*)\s+\((.*):(\d+):(\d+)\)/) || 
                             line.match(/at\s+(.*):(\d+):(\d+)/);
                if (match) {
                    if (match.length === 5) {
                        return `${match[2]}:${match[3]}`;
                    } else if (match.length === 4) {
                        return `${match[1]}:${match[2]}`;
                    }
                }
            }
        } catch (e) {
            return 'unknown';
        }
        return 'unknown';
    }
    
    /**
     * 格式化日志消息
     */
    function formatMessage(level, message, data) {
        const timestamp = getTimestamp();
        const caller = getCallerInfo();
        const levelName = Object.keys(LogLevel).find(k => LogLevel[k] === level) || 'UNKNOWN';
        
        let formatted = `[${timestamp}] [${levelName}] [${caller}] ${message}`;
        
        if (data !== undefined) {
            if (typeof data === 'object') {
                try {
                    formatted += ` ${JSON.stringify(data)}`;
                } catch (e) {
                    formatted += ` [Object]`;
                }
            } else {
                formatted += ` ${data}`;
            }
        }
        
        return formatted;
    }
    
    /**
     * 保存日志到本地存储
     */
    function saveToStorage(level, message, data) {
        if (!localStorageOutput) return;
        
        try {
            let logs = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]');
            
            const logEntry = {
                timestamp: getTimestamp(),
                level: Object.keys(LogLevel).find(k => LogLevel[k] === level),
                message: message,
                data: data !== undefined ? data : null
            };
            
            logs.push(logEntry);
            
            // 限制日志数量
            if (logs.length > MAX_LOGS) {
                logs = logs.slice(-MAX_LOGS);
            }
            
            localStorage.setItem(STORAGE_KEY, JSON.stringify(logs));
        } catch (e) {
            console.error('保存日志到本地存储失败:', e);
        }
    }
    
    /**
     * 输出日志
     */
    function log(level, message, data) {
        if (level < currentLevel) return;
        
        const formatted = formatMessage(level, message, data);
        
        // 控制台输出
        if (consoleOutput) {
            switch (level) {
                case LogLevel.DEBUG:
                    console.debug('%c' + formatted, 'color: #888');
                    break;
                case LogLevel.INFO:
                    console.info('%c' + formatted, 'color: #2196F3');
                    break;
                case LogLevel.WARN:
                    console.warn('%c' + formatted, 'color: #FF9800');
                    break;
                case LogLevel.ERROR:
                    console.error('%c' + formatted, 'color: #F44336');
                    break;
            }
        }
        
        // 本地存储
        saveToStorage(level, message, data);
    }
    
    // 公共API
    return {
        // 日志级别常量
        LogLevel: LogLevel,
        
        /**
         * 设置日志级别
         */
        setLevel: function(level) {
            currentLevel = level;
            this.info('日志级别设置为: ' + Object.keys(LogLevel).find(k => LogLevel[k] === level));
        },
        
        /**
         * 设置是否输出到控制台
         */
        setConsoleOutput: function(enabled) {
            consoleOutput = enabled;
        },
        
        /**
         * 设置是否保存到本地存储
         */
        setLocalStorageOutput: function(enabled) {
            localStorageOutput = enabled;
        },
        
        /**
         * 调试日志
         */
        debug: function(message, data) {
            log(LogLevel.DEBUG, message, data);
        },
        
        /**
         * 信息日志
         */
        info: function(message, data) {
            log(LogLevel.INFO, message, data);
        },
        
        /**
         * 警告日志
         */
        warn: function(message, data) {
            log(LogLevel.WARN, message, data);
        },
        
        /**
         * 错误日志
         */
        error: function(message, data) {
            log(LogLevel.ERROR, message, data);
        },
        
        /**
         * 记录API请求
         */
        logRequest: function(endpoint, method, data) {
            this.info(`【请求】${method} ${endpoint}`, data);
        },
        
        /**
         * 记录API响应
         */
        logResponse: function(endpoint, success, message, data) {
            const status = success ? '成功' : '失败';
            const level = success ? LogLevel.INFO : LogLevel.WARN;
            log(level, `【响应】${endpoint} - ${status}: ${message}`, data);
        },
        
        /**
         * 记录错误
         */
        logError: function(endpoint, error, data) {
            this.error(`【错误】${endpoint}: ${error}`, data);
        },
        
        /**
         * 记录用户操作
         */
        logUserAction: function(action, details) {
            this.info(`【用户操作】${action}`, details);
        },
        
        /**
         * 记录页面跳转
         */
        logPageView: function(pageName, params) {
            this.info(`【页面访问】${pageName}`, params);
        },
        
        /**
         * 获取所有日志
         */
        getLogs: function() {
            try {
                return JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]');
            } catch (e) {
                return [];
            }
        },
        
        /**
         * 清空日志
         */
        clearLogs: function() {
            localStorage.removeItem(STORAGE_KEY);
            this.info('日志已清空');
        },
        
        /**
         * 导出日志
         */
        exportLogs: function() {
            const logs = this.getLogs();
            const blob = new Blob([JSON.stringify(logs, null, 2)], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `logs_${getTimestamp().replace(/[: ]/g, '_')}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            this.info('日志已导出');
        }
    };
})();

// 自动记录页面加载
window.addEventListener('load', function() {
    const pageName = window.location.pathname.split('/').pop() || 'index.html';
    Logger.logPageView(pageName, {
        url: window.location.href,
        referrer: document.referrer,
        userAgent: navigator.userAgent.substring(0, 50) + '...'
    });
});

// 自动记录错误
window.addEventListener('error', function(event) {
    Logger.error('【全局错误】', {
        message: event.message,
        filename: event.filename,
        lineno: event.lineno,
        colno: event.colno,
        error: event.error ? event.error.stack : null
    });
});

// 自动记录未处理的Promise错误
window.addEventListener('unhandledrejection', function(event) {
    Logger.error('【未处理的Promise错误】', {
        reason: event.reason ? event.reason.toString() : 'Unknown'
    });
});

// 使Logger全局可用
window.Logger = Logger;
