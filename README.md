# 🚀 YouTube Shorts Auto-Publisher (Zero-Cost & Cloud Autonomous)

Sistema 100% autónomo para publicar videos en YouTube Shorts en 4 horarios diarios (8:00 AM, 12:00 PM, 5:00 PM y 9:00 PM Hora Colombia UTC-5) **completamente gratis y con tu computadora apagada**.

---

## 🏗️ Arquitectura de Ejecución

1. **Almacén:** Tus videos se guardan en Google Drive (en la carpeta `Shorts_Pendientes`).
2. **Disparador:** GitHub Actions se despierta gratis 4 veces al día con tareas programadas (`cron`).
3. **Candado Anti-Spam:** Verifica que no se haya publicado ningún video en los últimos 45 minutos para proteger la cuota de la API de YouTube y evitar duplicados.
4. **Subida:** Descarga el siguiente video en la cola, limpia su título, agrega la etiqueta `#Shorts` y tu llamada a la acción (CTA), y lo publica directamente en tu canal.
5. **Historial:** Mueve el archivo a la carpeta `Shorts_Publicados` en Google Drive para que nunca se repita.

---

## 📋 Guía de Configuración Paso a Paso

### Paso 1: Obtener `client_secret.json` en Google Cloud Console
1. Entra a [Google Cloud Console](https://console.cloud.google.com/).
2. Crea un proyecto nuevo (por ejemplo: `Youtube-Shorts-Bot`).
3. En el menú lateral ve a **APIs y servicios > Biblioteca** y habilita estas 2 APIs:
   - **YouTube Data API v3**
   - **Google Drive API**
4. Ve a **Pantalla de consentimiento de OAuth**:
   - Selecciona **Externo** y dale a "Crear".
   - Pon un nombre a la app (ej. `Shorts AutoPublisher`) y tu correo electrónico.
   - En **Usuarios de prueba (Test users)**, agrega el correo de tu canal de YouTube y dale a "Guardar".
5. Ve a **Credenciales > Crear credenciales > ID de cliente de OAuth**:
   - Tipo de aplicación: **App de escritorio** (Desktop app).
   - Nombre: `Bot Escritorio`.
   - Haz clic en **Crear** y luego en **Descargar JSON**.
6. Renombra ese archivo descargado como `client_secret.json` y colócalo en la carpeta raíz de este proyecto.

---

### Paso 2: Crear las 2 Carpetas en Google Drive
1. Abre [Google Drive](https://drive.google.com/) con la misma cuenta o crea dos carpetas:
   - `Shorts_Pendientes` (donde subirás tus 482 videos).
   - `Shorts_Publicados` (donde el bot los moverá automáticamente tras subirlos).
2. Entra a cada carpeta y copia su **ID** desde la barra de direcciones del navegador:
   - Ejemplo de URL: `https://drive.google.com/drive/folders/1aBcDeFgHiJkLmNoPqRsTuVwXyZ`
   - El ID es la última parte: `1aBcDeFgHiJkLmNoPqRsTuVwXyZ`.

---

### Paso 3: Generar tus Credenciales (Una sola vez en tu PC)
1. Abre una terminal en esta carpeta e instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```
2. Ejecuta el asistente interactivo:
   ```bash
   python scripts/setup_credentials.py
   ```
3. Se abrirá tu navegador web solicitando permiso para acceder a YouTube y Google Drive. Concede los permisos con la cuenta de tu canal.
4. La consola imprimirá los valores listos para copiar y pegar en GitHub Secrets:
   - `GOOGLE_CLIENT_SECRET_JSON`
   - `GOOGLE_TOKEN_JSON`

---

### Paso 4: Subir a GitHub y Configurar los Secretos
1. Sube este proyecto a un repositorio **Privado** en tu cuenta de GitHub:
   ```bash
   git init
   git add .
   git commit -m "feat: bot autonomo de shorts"
   git branch -M main
   git remote add origin https://github.com/TU_USUARIO/TU_REPOSITORIO.git
   git push -u origin main
   ```
2. En tu repositorio de GitHub, ve a **Settings > Secrets and variables > Actions > New repository secret**.
3. Agrega estos 4 secretos obligatorios:

| Nombre del Secreto | Valor |
|---|---|
| `GOOGLE_CLIENT_SECRET_JSON` | El valor copiado del Paso 3 |
| `GOOGLE_TOKEN_JSON` | El valor copiado del Paso 3 |
| `GDRIVE_PENDING_FOLDER_ID` | El ID de la carpeta `Shorts_Pendientes` |
| `GDRIVE_PUBLISHED_FOLDER_ID` | El ID de la carpeta `Shorts_Publicados` |

*(Opcional: puedes agregar `DEFAULT_CTA` para personalizar tu llamada a la acción en la descripción).*

---

### Paso 5: Probar el Sistema (¡Con 1 Clic!)
1. Ve a la pestaña **Actions** en tu repositorio de GitHub.
2. Selecciona el workflow **Publicar Shorts en YouTube**.
3. Haz clic en **Run workflow** > botón verde **Run workflow**.
4. ¡El bot se ejecutará, tomará el primer video de tu Google Drive, lo publicará en YouTube y lo moverá a publicados en menos de 45 segundos!

A partir de ahí, **puedes apagar tu computadora**. GitHub Actions se activará automáticamente todos los días a las:
- 🕒 8:00 AM (Colombia UTC-5)
- 🕒 12:00 PM (Colombia UTC-5)
- 🕒 5:00 PM (Colombia UTC-5)
- 🕒 9:00 PM (Colombia UTC-5)
