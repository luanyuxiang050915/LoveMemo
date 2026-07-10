"""
Q&L · API 服务 (MariaDB 版)
功能：倒计时 / 纪念日 / 留言板 / 恋爱相册
"""
import json
import os
import time
import uuid
from flask import Flask, request, jsonify, send_from_directory
import pymysql

app = Flask(__name__)

# === 配置 ===
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'photos')
os.makedirs(UPLOAD_DIR, exist_ok=True)

DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 3306,
    'user': 'lq',
    'password': 'Lyx20050915@',
    'database': 'lq',
    'charset': 'utf8mb4'
}

# === 初始化 ===
def init_db():
    conn = pymysql.connect(
        host=DB_CONFIG['host'], port=DB_CONFIG['port'],
        user=DB_CONFIG['user'], password=DB_CONFIG['password'],
        charset='utf8mb4'
    )
    with conn.cursor() as cur:
        cur.execute('CREATE DATABASE IF NOT EXISTS lq CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci')
    conn.close()

    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute('''
            CREATE TABLE IF NOT EXISTS countdowns (
                id VARCHAR(50) PRIMARY KEY, title VARCHAR(100) NOT NULL,
                description TEXT, target_date VARCHAR(30) NOT NULL,
                emoji VARCHAR(10) DEFAULT '⏳', color VARCHAR(20) DEFAULT '#ff6b9d',
                pinned TINYINT DEFAULT 0, created_at BIGINT DEFAULT 0
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS memorials (
                id VARCHAR(50) PRIMARY KEY, title VARCHAR(100) NOT NULL,
                description TEXT, date VARCHAR(20) NOT NULL,
                emoji VARCHAR(10) DEFAULT '💝', color VARCHAR(20) DEFAULT '#ff6b9d',
                pinned TINYINT DEFAULT 0, created_at BIGINT DEFAULT 0
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                k VARCHAR(50) PRIMARY KEY, v TEXT
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id VARCHAR(50) PRIMARY KEY, author VARCHAR(20) NOT NULL,
                content TEXT NOT NULL, created_at BIGINT DEFAULT 0
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS photos (
                id VARCHAR(50) PRIMARY KEY, category VARCHAR(50) DEFAULT '默认',
                filename VARCHAR(200) NOT NULL, caption TEXT,
                created_at BIGINT DEFAULT 0
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        ''')
    conn.commit()
    conn.close()


def get_conn():
    return pymysql.connect(**DB_CONFIG)


# === 主数据 API ===
@app.route('/api/data', methods=['GET'])
def get_data():
    conn = get_conn()
    with conn.cursor(pymysql.cursors.DictCursor) as cur:
        cur.execute('SELECT * FROM countdowns ORDER BY pinned DESC, target_date ASC')
        countdowns = []
        for r in cur.fetchall():
            countdowns.append({
                'id': r['id'], 'title': r['title'], 'description': r['description'] or '',
                'targetDate': r['target_date'], 'emoji': r['emoji'], 'color': r['color'],
                'pinned': bool(r['pinned']), 'createdAt': r['created_at']
            })

        cur.execute('SELECT * FROM memorials ORDER BY pinned DESC, date ASC')
        memorials = []
        for r in cur.fetchall():
            memorials.append({
                'id': r['id'], 'title': r['title'], 'description': r['description'] or '',
                'date': r['date'], 'emoji': r['emoji'], 'color': r['color'],
                'pinned': bool(r['pinned']), 'createdAt': r['created_at']
            })

        cur.execute('SELECT * FROM settings')
        settings = {r['k']: r['v'] for r in cur.fetchall()}

    conn.close()
    return jsonify({'countdowns': countdowns, 'memorials': memorials, 'settings': settings})


@app.route('/api/data', methods=['POST'])
def save_data():
    data = request.get_json()
    if not data:
        return jsonify({'ok': False, 'error': 'no data'}), 400

    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute('DELETE FROM countdowns')
        for c in data.get('countdowns', []):
            cur.execute(
                'INSERT INTO countdowns (id,title,description,target_date,emoji,color,pinned,created_at) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)',
                (c['id'], c['title'], c.get('description',''), c['targetDate'],
                 c.get('emoji','⏳'), c.get('color','#ff6b9d'), 1 if c.get('pinned') else 0, c.get('createdAt',0))
            )

        cur.execute('DELETE FROM memorials')
        for m in data.get('memorials', []):
            cur.execute(
                'INSERT INTO memorials (id,title,description,date,emoji,color,pinned,created_at) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)',
                (m['id'], m['title'], m.get('description',''), m['date'],
                 m.get('emoji','💝'), m.get('color','#ff6b9d'), 1 if m.get('pinned') else 0, m.get('createdAt',0))
            )

        cur.execute('DELETE FROM settings')
        for k, v in data.get('settings', {}).items():
            cur.execute('INSERT INTO settings (k, v) VALUES (%s, %s)', (k, str(v)))
        # 保留非标准 setting key（如 love_start_date）
        # 实际上上面已经全删再全写了，所以会保留

    conn.commit()
    conn.close()
    return jsonify({'ok': True})


# === 留言板 API ===
@app.route('/api/messages', methods=['GET'])
def get_messages():
    conn = get_conn()
    with conn.cursor(pymysql.cursors.DictCursor) as cur:
        cur.execute('SELECT * FROM messages ORDER BY created_at ASC')
        rows = cur.fetchall()
    conn.close()
    return jsonify([{
        'id': r['id'], 'author': r['author'], 'content': r['content'], 'createdAt': r['created_at']
    } for r in rows])


@app.route('/api/messages', methods=['POST'])
def add_message():
    data = request.get_json()
    if not data or not data.get('content'):
        return jsonify({'ok': False, 'error': 'content required'}), 400

    msg = {
        'id': 'msg_' + str(int(time.time() * 1000)),
        'author': data.get('author', '匿名'),
        'content': data['content'],
        'created_at': int(time.time() * 1000)
    }
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute('INSERT INTO messages (id, author, content, created_at) VALUES (%s,%s,%s,%s)',
                    (msg['id'], msg['author'], msg['content'], msg['created_at']))
    conn.commit()
    conn.close()
    return jsonify({'ok': True, 'message': msg})


@app.route('/api/messages/<msg_id>', methods=['DELETE'])
def delete_message(msg_id):
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute('DELETE FROM messages WHERE id = %s', (msg_id,))
    conn.commit()
    conn.close()
    return jsonify({'ok': True})


# === 相册 API ===
@app.route('/api/photos', methods=['GET'])
def get_photos():
    category = request.args.get('category', '')
    conn = get_conn()
    with conn.cursor(pymysql.cursors.DictCursor) as cur:
        if category and category != '全部':
            cur.execute('SELECT * FROM photos WHERE category = %s ORDER BY created_at DESC', (category,))
        else:
            cur.execute('SELECT * FROM photos ORDER BY created_at DESC')
        rows = cur.fetchall()
    conn.close()
    return jsonify([{
        'id': r['id'], 'category': r['category'], 'filename': r['filename'],
        'caption': r['caption'] or '', 'createdAt': r['created_at'],
        'url': f'/photos/{r["filename"]}'
    } for r in rows])


@app.route('/api/photos/categories', methods=['GET'])
def get_categories():
    conn = get_conn()
    with conn.cursor(pymysql.cursors.DictCursor) as cur:
        cur.execute('SELECT DISTINCT category FROM photos ORDER BY category')
        rows = cur.fetchall()
    conn.close()
    cats = [r['category'] for r in rows]
    if not cats:
        cats = ['默认']
    return jsonify(cats)


@app.route('/api/photos', methods=['POST'])
def upload_photo():
    if 'file' not in request.files:
        return jsonify({'ok': False, 'error': 'no file'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'ok': False, 'error': 'empty filename'}), 400

    # 生成唯一文件名
    ext = os.path.splitext(file.filename)[1] or '.jpg'
    safe_name = uuid.uuid4().hex + ext
    filepath = os.path.join(UPLOAD_DIR, safe_name)
    file.save(filepath)

    category = request.form.get('category', '默认')
    caption = request.form.get('caption', '')
    photo_id = 'photo_' + str(int(time.time() * 1000))
    now = int(time.time() * 1000)

    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute('INSERT INTO photos (id, category, filename, caption, created_at) VALUES (%s,%s,%s,%s,%s)',
                    (photo_id, category, safe_name, caption, now))
    conn.commit()
    conn.close()

    return jsonify({'ok': True, 'photo': {
        'id': photo_id, 'category': category, 'filename': safe_name,
        'caption': caption, 'createdAt': now, 'url': f'/photos/{safe_name}'
    }})


@app.route('/api/photos/<photo_id>', methods=['DELETE'])
def delete_photo(photo_id):
    conn = get_conn()
    with conn.cursor(pymysql.cursors.DictCursor) as cur:
        cur.execute('SELECT filename FROM photos WHERE id = %s', (photo_id,))
        row = cur.fetchone()
        if row:
            filepath = os.path.join(UPLOAD_DIR, row['filename'])
            if os.path.exists(filepath):
                os.remove(filepath)
        cur.execute('DELETE FROM photos WHERE id = %s', (photo_id,))
    conn.commit()
    conn.close()
    return jsonify({'ok': True})


# === 静态文件 ===
@app.route('/')
def index():
    return send_from_directory(os.path.dirname(os.path.abspath(__file__)), 'index.html')

@app.route('/<path:filename>')
def static_files(filename):
    root = os.path.dirname(os.path.abspath(__file__))
    filepath = os.path.join(root, filename)
    if os.path.exists(filepath) and os.path.isfile(filepath):
        return send_from_directory(root, filename)
    return jsonify({'error': 'not found'}), 404

# === 照片文件 ===
@app.route('/photos/<filename>')
def serve_photo(filename):
    return send_from_directory(UPLOAD_DIR, filename)


# === 健康检查 ===
@app.route('/api/ping')
def ping():
    return jsonify({'ok': True, 'time': int(time.time() * 1000)})


if __name__ == '__main__':
    print('♻️  初始化数据库...')
    init_db()
    print('✅ 数据库就绪')
    print('🚀 API 服务: http://127.0.0.1:5000')
    app.run(host='127.0.0.1', port=5000, debug=False)
