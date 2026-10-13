"""
Script interactivo para generar y formatear las credenciales OAuth 2.0.
"""
import os
import sys
import json
import base64

# Configurar salida UTF-8 para consola de Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Añadir directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from core.auth_manager import get_authenticated_credentials, CLIENT_SECRET_FILE, TOKEN_FILE


def main():
    print("=" * 65)
    print("[CONFIGURADOR] CREDENCIALES OAUTH 2.0 (YOUTUBE Y GOOGLE DRIVE)")
    print("=" * 65)

    if not os.path.exists(CLIENT_SECRET_FILE):
        print(f"\n[ERROR] No se encontro el archivo '{os.path.basename(CLIENT_SECRET_FILE)}'.")
        return

    print("\n[PASO 1] Abriendo tu navegador para autorizar con tu cuenta de YouTube...")
    creds = get_authenticated_credentials()

    if not os.path.exists(TOKEN_FILE):
        print("[ERROR] No se pudo generar token.json")
        return

    print("\n[OK] Sesion autorizada correctamente!")
    print(f"Token guardado en: {TOKEN_FILE}")

    # Leer ambos archivos y codificar para GitHub Secrets
    with open(CLIENT_SECRET_FILE, "r", encoding="utf-8") as f:
        client_secret_content = f.read()

    with open(TOKEN_FILE, "r", encoding="utf-8") as f:
        token_content = f.read()

    b64_client = base64.b64encode(client_secret_content.encode("utf-8")).decode("utf-8")
    b64_token = base64.b64encode(token_content.encode("utf-8")).decode("utf-8")

    print("\n" + "=" * 65)
    print("COPIA Y PEGA ESTAS VARIABLES EN TUS GITHUB REPOSITORY SECRETS:")
    print("=" * 65)

    print("\n1) NOMBRE: GOOGLE_CLIENT_SECRET_JSON")
    print(f"   VALOR:\n{b64_client}")

    print("\n2) NOMBRE: GOOGLE_TOKEN_JSON")
    print(f"   VALOR:\n{b64_token}")

    print("\n" + "=" * 65)
    print("Listo! Tus secretos en GitHub tendran acceso permanente.")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    main()
