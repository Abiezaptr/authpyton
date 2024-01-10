import os
import urllib.parse
import uuid
from flask import Flask, redirect, request, render_template, jsonify
import adal
import requests

app = Flask(__name__, template_folder='static/templates')
app.debug = True
app.secret_key = 'development'

SESSION = requests.Session()

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

    params = urllib.parse.urlencode({
        'response_type': 'code',
        'client_id': 'a10d6918-5758-4f0f-b716-787053507b52',  # Ganti dengan client ID Anda
        'redirect_uri': 'https://192.168.0.176:5000/login/authorized',  # Ganti port sesuai kebutuhan
        'state': auth_state,
        'resource': 'https://graph.microsoft.com/',  # Ganti dengan resource yang Anda inginkan
        'prompt': prompt_behavior
    })

    return redirect('https://login.microsoftonline.com/common/oauth2/authorize?' + params)  # Ganti dengan authority URL Anda

@app.route('/login/authorized')
def authorized():
    """Penangan untuk Redirect Uri aplikasi."""
    code = request.args['code']
    auth_state = request.args['state']

    if auth_state != SESSION.auth_state:
        raise Exception('state returned to redirect URL does not match!')

    auth_context = adal.AuthenticationContext('https://login.microsoftonline.com/common', api_version=None)
    token_response = auth_context.acquire_token_with_authorization_code(
        code, 'https://192.168.0.176:5000/login/authorized', 'https://graph.microsoft.com/',
        'a10d6918-5758-4f0f-b716-787053507b52', '7uU8Q~ekwzwEgyjYlvXFMuBFxIeNNFnxMKWG7bj_'  # Ganti sesuai kebutuhan
    )

    # Dapatkan data dari Microsoft Graph
    graph_endpoint = 'https://graph.microsoft.com/v1.0/me'
    http_headers = {'Authorization': f"Bearer {token_response['accessToken']}"}
    graph_data = SESSION.get(graph_endpoint, headers=http_headers, stream=False).json()

    # Redirect ke halaman Laravel sambil membawa semua data di URL
    redirect_url = (
        f"https://192.168.0.176/microsoft/callback?"  # Ganti dengan IP atau domain yang sesuai
        f"displayName={graph_data.get('displayName')}&"
        f"givenName={graph_data.get('givenName')}&"
        f"id={graph_data.get('id')}&"
        f"jobTitle={graph_data.get('jobTitle')}&"
        f"mail={graph_data.get('mail')}&"
        f"mobilePhone={graph_data.get('mobilePhone')}&"
        f"officeLocation={graph_data.get('officeLocation')}&"
        f"preferredLanguage={graph_data.get('preferredLanguage')}&"
        f"surname={graph_data.get('surname')}&"
        f"userPrincipalName={graph_data.get('userPrincipalName')}"
    )
    return redirect(redirect_url)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000, ssl_context='adhoc')
