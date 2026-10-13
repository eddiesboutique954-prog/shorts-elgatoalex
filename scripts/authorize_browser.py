import os
import sys
import json
import base64
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
import subprocess
from google_auth_oauthlib.flow import InstalledAppFlow

sys.stdout.reconfigure(encoding="utf-8")

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/drive"
]

root_dir = os.path.dirname(os.path.dirname(__file__))
client_secret_path = os.path.join(root_dir, "client_secret.json")
token_path = os.path.join(root_dir, "token.json")

with open(client_secret_path, "r", encoding="utf-8") as f:
    client_data = json.load(f)

flow = InstalledAppFlow.from_client_config(
    client_data,
    SCOPES,
    redirect_uri="http://localhost:8080/"
)

auth_code = None

class OAuthCallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global auth_code
        query = urllib.parse.urlparse(self.path).query
        params = urllib.parse.parse_qs(query)
        
        if "code" in params:
            auth_code = params["code"][0]
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            html_success = """
            <html>
            <body style="font-family:sans-serif; text-align:center; padding:50px; background:#f4f6f8;">
                <h1 style="color:#2e7d32;">¡Autorización Exitosa! 🎉</h1>
                <p style="font-size:18px; color:#333;">Tu canal de YouTube y Google Drive han sido vinculados correctamente.</p>
                <p style="color:#666;">Ya puedes cerrar esta pestaña y volver al chat.</p>
            </body>
            </html>
            """
            self.wfile.write(html_success.encode("utf-8"))
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Error: No se recibio codigo de autorizacion.")

    def log_message(self, format, *args):
        # Silenciar logs ruidosos en stdout
        return

auth_url, _ = flow.authorization_url(prompt="consent", access_type="offline")

print("=" * 60)
print("SERVIDOR LOCAL INICIADO EN http://localhost:8080/")
print("=" * 60)
print(f"URL: {auth_url}\n")
sys.stdout.flush()

# Intentar abrir el navegador en Windows
try:
    subprocess.Popen(["powershell.exe", "-Command", f'Start-Process "{auth_url}"'])
except Exception:
    pass

# Iniciar servidor HTTP para capturar la respuesta de Google
server = HTTPServer(("localhost", 8080), OAuthCallbackHandler)

while auth_code is None:
    server.handle_request()

server.server_close()

print(f"[AUTH] Codigo recibido de Google con exito.")
flow.fetch_token(code=auth_code)
creds = flow.credentials

with open(token_path, "w", encoding="utf-8") as f:
    f.write(creds.to_json())

print("\n" + "=" * 60)
print("¡AUTORIZACION COMPLETADA! TOKEN GUARDADO EN token.json")
print("=" * 60)

# Generar variables para GitHub Secrets
with open(client_secret_path, "r", encoding="utf-8") as f:
    c_raw = f.read()
with open(token_path, "r", encoding="utf-8") as f:
    t_raw = f.read()

b64_client = base64.b64encode(c_raw.encode("utf-8")).decode("utf-8")
b64_token = base64.b64encode(t_raw.encode("utf-8")).decode("utf-8")

secrets_file = os.path.join(root_dir, "GITHUB_SECRETS_LISTOS.txt")
with open(secrets_file, "w", encoding="utf-8") as f:
    f.write(f"GOOGLE_CLIENT_SECRET_JSON={b64_client}\n\n")
    f.write(f"GOOGLE_TOKEN_JSON={b64_token}\n")

print(f"Secretos exportados en: {secrets_file}")
sys.stdout.flush()
