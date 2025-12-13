"""
VocabWeb 后端服务器 - 提供跨设备数据同步
"""
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import base64
import json
from datetime import datetime

app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 数据库文件路径
DB_FILE = 'user_vocab.db'
CONFIG_FILE = 'user_config.json'  # 存储配置信息

@app.route('/')
def index():
    """重定向到学习界面"""
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    """提供静态文件"""
    return send_from_directory('.', path)

@app.route('/api/get-db', methods=['GET'])
def get_database():
    """获取用户数据库"""
    try:
        if os.path.exists(DB_FILE):
            with open(DB_FILE, 'rb') as f:
                db_data = f.read()
            
            # 返回 Base64 编码的数据库
            db_base64 = base64.b64encode(db_data).decode('utf-8')
            
            # 获取文件修改时间
            mtime = os.path.getmtime(DB_FILE)
            last_modified = datetime.fromtimestamp(mtime).isoformat()
            
            return jsonify({
                'success': True,
                'database': db_base64,
                'lastModified': last_modified,
                'size': len(db_data)
            })
        else:
            # 数据库文件不存在
            return jsonify({
                'success': False,
                'message': '数据库文件不存在，使用预构建数据库'
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/save-db', methods=['POST'])
def save_database():
    """保存用户数据库"""
    try:
        data = request.get_json()
        
        if not data or 'database' not in data:
            return jsonify({
                'success': False,
                'error': '缺少数据库数据'
            }), 400
        
        # 解码 Base64 数据
        db_base64 = data['database']
        db_data = base64.b64decode(db_base64)
        
        # 备份旧数据库（如果存在）
        if os.path.exists(DB_FILE):
            backup_file = f'{DB_FILE}.backup'
            with open(backup_file, 'wb') as f:
                with open(DB_FILE, 'rb') as old_f:
                    f.write(old_f.read())
        
        # 保存新数据库
        with open(DB_FILE, 'wb') as f:
            f.write(db_data)
        
        # 获取保存时间
        mtime = os.path.getmtime(DB_FILE)
        last_modified = datetime.fromtimestamp(mtime).isoformat()
        
        return jsonify({
            'success': True,
            'message': '数据库保存成功',
            'lastModified': last_modified,
            'size': len(db_data)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/status', methods=['GET'])
def get_status():
    """获取服务器状态"""
    try:
        db_exists = os.path.exists(DB_FILE)
        db_size = os.path.getsize(DB_FILE) if db_exists else 0
        db_modified = None
        
        if db_exists:
            mtime = os.path.getmtime(DB_FILE)
            db_modified = datetime.fromtimestamp(mtime).isoformat()
        
        return jsonify({
            'success': True,
            'server': 'VocabWeb API',
            'version': '2.0',
            'database': {
                'exists': db_exists,
                'size': db_size,
                'lastModified': db_modified
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/save-config', methods=['POST'])
def save_config():
    """保存配置信息（如 API Key）"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': '缺少配置数据'
            }), 400
        
        # 读取现有配置
        config = {}
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
        
        # 更新配置
        if 'geminiApiKey' in data:
            config['geminiApiKey'] = data['geminiApiKey']
        
        config['lastModified'] = datetime.now().isoformat()
        
        # 保存配置
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        return jsonify({
            'success': True,
            'message': '配置保存成功'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/get-config', methods=['GET'])
def get_config():
    """获取配置信息"""
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            return jsonify({
                'success': True,
                **config
            })
        else:
            return jsonify({
                'success': True,
                'message': '配置文件不存在'
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    print('🚀 VocabWeb 服务器启动中...')
    print('📱 支持跨设备数据同步')
    print('🔑 支持配置同步（API Key 等）')
    print('🌐 访问地址: http://localhost:8080')
    print('📊 API 状态: http://localhost:8080/api/status')
    print('')
    print('💡 使用提示：')
    print('   - 电脑端：配置 API Key 后会自动保存到服务器')
    print('   - 手机端：点击"同步配置"按钮从服务器获取')
    print('')
    app.run(host='0.0.0.0', port=8080, debug=True)
