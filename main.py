import pymysql
from flask import Flask, request, jsonify
import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
import requests
import datetime
from flask_cors import CORS  # Import CORS module


secret_key = "your_secret_key_here"


app = Flask(__name__)
CORS(app) 

conn = pymysql.connect(
    host='localhost',
    user='root',
    password='tin14091998',
    database='vmt_music'
)

def get_google_public_keys():
    response = requests.get("https://www.googleapis.com/oauth2/v3/certs")
    return response.json()


def validate_google_jwt(token):
    public_keys = get_google_public_keys()
    for key in public_keys.values():
        try:
            payload = jwt.decode(token, key, algorithms=['RS256'])
            return True
        except ExpiredSignatureError:
            return False
        except InvalidTokenError:
            pass  
    return True


# @app.before_request
# def authenticate():
#     token = request.headers.get('Authorization')

#     if not token or not validate_google_jwt(token):
#         return jsonify({'error': 'Unauthorized access.'}), 401

def get_email():
    token = request.headers.get('Authorization')
    if token != None and token != '':
        payload = jwt.decode(token, options={"verify_signature": False})
        email = payload.get("email")
        return email
    else:
        return ''
    
def create_user_google(email):
    uuid = "uuid"
    email = email
    status = 1
    login_type = "google"

    try:
        with conn.cursor() as cursor:
            sql_query = """INSERT INTO users (uuid, email, status, login_type) 
                           VALUES (%s, %s, %s, %s)"""
            cursor.execute(sql_query, (uuid, email, status, login_type))
            conn.commit()

            user_id = cursor.lastrowid
            
            return user_id,None,0
            
    except Exception as e:
        return None,jsonify({'Message': str(e)}), 500
        
def check_email_exist(email):
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE email = %s LIMIT 1", (email,))
            user = cursor.fetchone()
            if user:
                current_time = datetime.datetime.now()
                lr = user[6]  
                time_difference = current_time - lr
                if time_difference.total_seconds() <= 5 * 60: 
                    return None,jsonify({'Message': 'Request limit'}), 200
                else:
                    return user[0],None,0
            else:
                return None,None,0

    except Exception as e:
        return None,jsonify({'Message': str(e)}), 500
    
def create_music_queue(user_id,url):
    user_id = user_id
    url = url
    if None in (user_id, url):
        return jsonify({'Message': 'Missing data'}), 200
    
    try:
        with conn.cursor() as cursor:
            sql_query1 = """INSERT INTO music_queue (uuid, url, status, requested_by, created_by, updated_by) 
                           VALUES (%s, %s, %s, %s, %s, %s)"""
            cursor.execute(sql_query1, ("uuid", url, 1, user_id, 0, 0))

            sql_query2 = """UPDATE users SET last_request = CURRENT_TIMESTAMP 
                           WHERE id = %s"""
            cursor.execute(sql_query2, (user_id,))

            conn.commit()

            return None,0
    except Exception as e:
        return jsonify({'Message': str(e)}), 500
    
def get_public_ip():
    try:
        response = requests.get('https://httpbin.org/ip')
        if response.status_code == 200:
            data = response.json()
            return data.get('origin')
        else:
            print(f"Error: Unable to retrieve public IP (Status code: {response.status_code})")
            return None
    except Exception as e:
        print(f"Error: {e}")
        return None

    
@app.route('/api/insert_music', methods=['POST'])
def insert_music():
    email = get_email()
    if email == '':
        ip_address = get_public_ip()
        email = ip_address
        user_id,err,code = check_email_exist(email)
        if err != None:
            return err,code
        else:
            if user_id == None:
                user_id,err,code = create_user_google(email)
                if err != None:
                    return err,code
    else:
        user_id,err,code = check_email_exist(email)
        if err != None:
            return err,code
        else:
            if user_id == None:
                user_id,err,code = create_user_google(email)
                if err != None:
                    return err,code

    data = request.json
    url = data.get('url')
    result,code = create_music_queue(user_id,url)
    if result != None:
        return result,code
    else:
        return jsonify({'Message': 'Success'}), 200
    
if __name__ == '__main__':
    app.run(host='192.168.1.12', port=5000, debug=True)
