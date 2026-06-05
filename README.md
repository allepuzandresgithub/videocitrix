# videocitrix

# 🎥 VideoCitrix

**Streaming gratuito – Tu videoteca personal en la nube**

VideoCitrix es un servicio de streaming **totalmente gratuito** que te permite acceder a tu propia videoteca personal desde cualquier dispositivo. Regístrate sin coste y disfruta de tus vídeos favoritos donde quieras, cuando quieras.

<img width="1817" height="880" alt="image" src="https://github.com/user-attachments/assets/3a4cb0a6-020b-42b8-aaf8-dc45d10923d9" />

## ✨ Características principales

- 🆓 **100% gratuito** – Sin suscripciones, sin pagos ocultos.
- 📚 **Videoteca personal** – Organiza y guarda tu contenido favorito.
- 🌐 **Acceso multiplataforma** – Solo necesitas un navegador web.
- 🔐 **Cuenta segura** – Registro rápido con usuario y contraseña.
- 🚀 **Sin publicidad** – Experiencia limpia y sin interrupciones.

## 🛠️ Configuración del proyecto (importante)

> **⚠️ Seguridad:** El archivo `setup.db` que contenía credenciales ha sido **eliminado** del repositorio por razones de seguridad. Ahora la configuración se maneja mediante variables de entorno.

### Pasos para configurar tu entorno local

1. **Crea un archivo `.env`** en la raíz del proyecto (no lo subas a Git).
2. **Define las siguientes variables** con tus propios datos (ejemplo):
   ```env
   DB_HOST=localhost
   DB_USER=tu_usuario
   DB_PASSWORD=tu_contraseña_segura
   DB_NAME=videocitrix
   PORT=3000
   SECRET_KEY=una_clave_muy_larga_y_aleatoria
