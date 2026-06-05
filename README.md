# 🎬 VideoCitrix - Streaming de vídeo gratuito

![Estado del Proyecto](https://img.shields.io/badge/Estado-En%20desarrollo-brightgreen) ![Licencia](https://img.shields.io/badge/Licencia-MIT-blue) ![Plataforma](https://img.shields.io/badge/Plataforma-Web%20%7C%20Móvil-lightgrey)

**Videoteca personal en la nube, sin coste y sin publicidad.**

VideoCitrix te permite almacenar, organizar y reproducir tus vídeos favoritos desde cualquier navegador. Olvídate de suscripciones mensuales o de ceder tu privacidad a grandes plataformas. Aquí **tú controlas tu contenido**.

<img width="1817" height="880" alt="image" src="https://github.com/user-attachments/assets/8ca6187a-9199-4b25-80a9-f5129195eeb3" />


## 📖 Descripción

VideoCitrix es un servicio de streaming **totalmente gratuito** diseñado para amantes del vídeo que valoran su libertad. Permite a los usuarios:

- **Almacenar** su colección personal de vídeos (MP4, MKV, AVI, etc.) en la nube.
- **Acceder** desde cualquier dispositivo con conexión a internet mediante una interfaz web limpia y rápida.
- **Reproducir** en streaming sin interrupciones publicitarias ni seguimiento de datos.
- **Organizar** por carpetas, listas de reproducción o etiquetas personalizadas.

A diferencia de plataformas como YouTube o Vimeo, **no hay algoritmos que te empujen contenido** ni recopilación masiva de datos. Solo tú y tu videoteca.

## ✨ Características principales

- 🆓 **Completamente gratuito** – Sin tarifas, sin planes premium ocultos.
- 🔐 **Acceso seguro** – Inicio de sesión con usuario/contraseña (próximamente 2FA opcional).
- 🎥 **Reproductor integrado** – Soporta múltiples formatos y guarda el progreso de reproducción.
- ☁️ **Almacenamiento en la nube** – Tus vídeos disponibles siempre que tengas internet.
- 📱 **Diseño responsive** – Funciona en móvil, tablet y ordenador.
- 🚀 **Streaming optimizado** – Carga inteligente y baja latencia.
- 📜 **Registro gratuito** – Crea tu cuenta en segundos, sin compromiso.

## 🛠️ Stack tecnológico (actual)

| Capa | Tecnologías |
|------|--------------|
| Frontend | HTML5, CSS3, JavaScript (Vanilla + HLS.js) |
| Backend | Python + Flask |
| Base de datos | SQLite (local) / PostgreSQL (producción) |
| Almacenamiento | Sistema de archivos local / S3 compatible |
| Streaming | HTTP Live Streaming (HLS) para vídeo |

> **Nota de seguridad:** El archivo `setup.db` que contenía credenciales ha sido **eliminado** del repositorio. Ahora toda la configuración sensible se maneja mediante variables de entorno (archivo `.env`). No vuelvas a subir credenciales a Git.

## 🚀 Comenzar a usar (para usuarios finales)

1. Visita [https://videocitrix.com](https://videocitrix.com)
2. Si ya tienes cuenta, introduce tu **Usuario o email** y **Contraseña**.
3. Si eres nuevo, haz clic en **"Regístrate gratis"** y completa el formulario.
4. Una vez dentro, usa el botón **"Subir vídeo"** o arrastra archivos a la ventana.
5. Organiza tus vídeos, crea listas de reproducción y dale al **play**.

💡 **Consejo:** Activa la verificación en dos pasos desde tu perfil para máxima seguridad (próximamente).

## 🔧 Instalación local (solo para desarrolladores)

Sigue estos pasos si quieres ejecutar tu propia instancia de VideoCitrix.


### 1. Clona el repositorio
```bash
git clone https://github.com/allepuzandresgithub/videocitrix.git
cd videocitrix
```
2. Crea y activa un entorno virtual
```bash
# Linux/macOS
python3 -m venv .venv
source .venv/bin/activate

# Windows
python -m venv .venv
.venv\Scripts\activate
```
3. Instala dependencias
```bash
pip install -r requirements.txt
```

### 4. Configura las variables de entorno (importante)

Crea un archivo **`.env`** en la raíz del proyecto con el siguiente contenido (ajusta los valores si es necesario):

```env
DB_HOST=localhost
DB_ROOT_USER=root
DB_ROOT_PASSWORD=
DB_NAME=videocloud
DB_APP_USER=videocloud
DB_APP_PASSWORD=mivideopass
```
5. Inicializa la base de datos
```bash
python setup_db.py --init
```
6. Ejecuta el servidor
```bash
python app.py
# o si tienes el script de inicio:
bash start_server.sh
```

