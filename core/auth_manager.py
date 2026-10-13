"""
Gestor de autenticación OAuth 2.0 para Google APIs (YouTube Data API v3 y Google Drive API v3).
Diseñado para funcionar transparentemente en Local y en Entornos CI/CD (GitHub Actions).
"""
import os
import json
import base64
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from config.settings import YOUTUBE_SCOPES

TOKEN_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "token.json")
CLIENT_SECRET_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "client_secret.json")


def _decode_or_read_json(env_var_name: str, fallback_file_path: str) -> dict:
    """
    Intenta obtener un JSON desde una variable de entorno (en texto plano o base64).
    Si no existe, intenta leer desde un archivo físico local.
    """
    val = os.getenv(env_var_name)
    if val:
        val = val.strip()
        # Intentar parsear directo como JSON
        try:
            return json.loads(val)
        except json.JSONDecodeError:
            pass
        # Intentar decodificar como base64
        try:
            decoded = base64.b64decode(val).decode("utf-8")
            return json.loads(decoded)
        except Exception as e:
            raise ValueError(f"La variable {env_var_name} no contiene un JSON ni Base64 válido: {e}")

    if os.path.exists(fallback_file_path):
        with open(fallback_file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    return None


def get_authenticated_credentials() -> Credentials:
    """
    Obtiene y renueva las credenciales OAuth 2.0.
    1. Si está en GitHub Actions, recupera el token desde GOOGLE_TOKEN_JSON.
    2. Si el token expiró, lo renueva con el refresh_token.
    3. Si corre en local por primera vez, lanza el flujo de navegador y guarda token.json.
    """
    creds = None
    token_data = _decode_or_read_json("GOOGLE_TOKEN_JSON", TOKEN_FILE)

    if token_data:
        creds = Credentials.from_authorized_user_info(token_data, YOUTUBE_SCOPES)

    # Si no hay credenciales o no son válidas
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("[AUTH] El token de acceso expiró. Renovando automáticamente con el refresh_token...")
            creds.refresh(Request())
            # Actualizar el archivo local si estamos en local
            if os.path.exists(os.path.dirname(TOKEN_FILE)):
                with open(TOKEN_FILE, "w", encoding="utf-8") as f:
                    f.write(creds.to_json())
            print("[AUTH] Token renovado con éxito.")
        else:
            # Flujo interactivo inicial (sólo para ejecución local inicial)
            client_data = _decode_or_read_json("GOOGLE_CLIENT_SECRET_JSON", CLIENT_SECRET_FILE)
            if not client_data:
                raise FileNotFoundError(
                    "No se encontró 'client_secret.json' ni la variable 'GOOGLE_CLIENT_SECRET_JSON'.\n"
                    "Por favor descarga tu archivo client_secret.json desde Google Cloud Console."
                )

            flow = InstalledAppFlow.from_client_config(client_data, YOUTUBE_SCOPES)
            print("[AUTH] Servidor local escuchando en el puerto 8080...")
            print("[AUTH] Abriendo tu navegador para iniciar sesión con Google...")
            try:
                creds = flow.run_local_server(port=8080, prompt="consent", access_type="offline", open_browser=True)
            except Exception as e:
                auth_url, _ = flow.authorization_url(prompt="consent", access_type="offline")
                print(f"[AUTH] Si tu navegador no se abrio automaticamente, abre este enlace:\n{auth_url}")
                raise e

            with open(TOKEN_FILE, "w", encoding="utf-8") as f:
                f.write(creds.to_json())
            print(f"[AUTH] ¡Autorización exitosa! Credenciales guardadas en: {TOKEN_FILE}")

    return creds


def get_youtube_service():
    """Retorna el cliente de YouTube Data API v3 autenticado."""
    creds = get_authenticated_credentials()
    return build("youtube", "v3", credentials=creds)


def get_drive_service():
    """Retorna el cliente de Google Drive API v3 autenticado."""
    creds = get_authenticated_credentials()
    return build("drive", "v3", credentials=creds)
