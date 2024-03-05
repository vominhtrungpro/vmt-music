import pymysql
from flask import Flask, request, jsonify

app = Flask(__name__)

conn = pymysql.connect(
    host='localhost',
    user='root',
    password='tin14091998',
    database='vmt_music'
)

@app.route('/api/insert_music', methods=['POST'])
def insert_music():
    data = request.json
    uuid = "uuid"
    url = data.get('url')
    status = 1
    created_by = 0
    updated_by = 0
    
    if None in (uuid, url, created_by, updated_by):
        return jsonify({'error': 'Thiếu thông tin.'}), 400
    
    try:
        with conn.cursor() as cursor:
            sql_query = """INSERT INTO music_queue (uuid, url, status, created_by, updated_by) 
                           VALUES (%s, %s, %s, %s, %s)"""
            cursor.execute(sql_query, (uuid, url, status, created_by, updated_by))
            conn.commit()
        return jsonify({'message': 'Dữ liệu đã được chèn thành công.'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)