import os
import urllib.parse
import uuid
from flask import Flask, redirect, request, render_template, jsonify
import adal
import flask
import requests
from OpenSSL import crypto
import config

app = Flask(__name__, template_folder='static/templates')
app.debug = True
app.secret_key = 'development'

SESSION = requests.Session()

# Gunakan sertifikat dan kunci yang sudah dibuat di root proyek
CERT_FILE = 'cert.pem'
KEY_FILE = 'key.pem'

# Periksa apakah file sertifikat dan kunci ada
if not os.path.isfile(CERT_FILE) or not os.path.isfile(KEY_FILE):
    raise FileNotFoundError("The certificate or key file was not found.")

# Gunakan sertifikat dan kunci yang sudah dibuat
ssl_context = (CERT_FILE, KEY_FILE)

@app.route('/')
def homepage():
    """Render halaman utama."""
    return render_template('homepage.html', sample='ADAL')

@app.route('/login')
def login():
    """Minta pengguna untuk mengotentikasi."""
    auth_state = str(uuid.uuid4())
    SESSION.auth_state = auth_state

    # Untuk contoh ini, pengguna memilih akun untuk mengotentikasi.
    prompt_behavior = 'select_account'

    params = urllib.parse.urlencode({'response_type': 'code',
                                     'client_id': config.CLIENT_ID,
                                     'redirect_uri': config.REDIRECT_URI,
                                     'state': auth_state,
                                     'resource': config.RESOURCE,
                                     'prompt': prompt_behavior})

    return flask.redirect(config.AUTHORITY_URL + '/oauth2/authorize?' + params)

@app.route('/login/authorized')
def authorized():
    """Penangan untuk Redirect Uri aplikasi."""
    code = request.args['code']
    auth_state = request.args['state']

    if auth_state != SESSION.auth_state:
        raise Exception('state returned to redirect URL does not match!')

    auth_context = adal.AuthenticationContext(config.AUTHORITY_URL, api_version=None)
    token_response = auth_context.acquire_token_with_authorization_code(
        code, config.REDIRECT_URI, config.RESOURCE,
        config.CLIENT_ID, config.CLIENT_SECRET  # Ganti sesuai kebutuhan
    )

    # Dapatkan data dari Microsoft Graph
    graph_endpoint = 'https://graph.microsoft.com/v1.0/me'
    http_headers = {'Authorization': f"Bearer {token_response['accessToken']}"}
    graph_data = SESSION.get(graph_endpoint, headers=http_headers, stream=False).json()

    # Redirect ke halaman Laravel sambil membawa semua data di URL
    redirect_url = (
        f"https://192.168.0.176/portaldashboard/callback?"  # Ganti dengan IP atau domain yang sesuai
        f"displayName={graph_data.get('displayName')}&"
        f"id={graph_data.get('id')}&"
        f"jobTitle={graph_data.get('jobTitle')}&"
        f"mail={graph_data.get('mail')}&"
        f"mobilePhone={graph_data.get('mobilePhone')}&"
        f"officeLocation={graph_data.get('officeLocation')}"
    )
    return redirect(redirect_url)

if __name__ == '__main__':
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    app.run(debug=True, host='0.0.0.0', port=5000, ssl_context=ssl_context, use_debugger=True, use_reloader=True)