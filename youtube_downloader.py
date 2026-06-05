import os
import json
import subprocess
import threading
import time
import uuid
from datetime import datetime
from pathlib import Path

class YouTubeDownloader:
    def __init__(self, download_dir="~/YouTube_Downloads", library_dir="./library"):
        self.download_dir = os.path.expanduser(download_dir)
        self.library_dir = os.path.expanduser(library_dir)
        self.downloads = {}
        self.load_downloads()
        
    def start_download(self, url, format="mp3", quality="alta"):
        """Inicia una descarga de YouTube"""
        download_id = str(uuid.uuid4())
        
        # Información inicial de la descarga
        download_info = {
            'id': download_id,
            'url': url,
            'format': format,
            'quality': quality,
            'status': 'starting',
            'progress': 0,
            'message': 'Iniciando descarga...',
            'start_time': datetime.now().isoformat(),
            'end_time': None,
            'file_path': None
        }
        
        self.downloads[download_id] = download_info
        self.save_downloads()
        
        # Iniciar descarga en segundo plano
        thread = threading.Thread(
            target=self._run_download,
            args=(download_id, url, format, quality)
        )
        thread.daemon = True
        thread.start()
        
        return download_id
    
    def _run_download(self, download_id, url, format, quality):
        """Ejecuta la descarga en segundo plano"""
        download_info = self.downloads[download_id]
        
        try:
            # Actualizar estado
            download_info['status'] = 'downloading'
            download_info['message'] = 'Conectando con YouTube...'
            download_info['progress'] = 10
            self.save_downloads()
            
            # Construir comando
            script_path = os.path.join(os.path.dirname(__file__), "yt_music_downloader_arg.sh")
            
            cmd = [
                "bash", script_path,
                "-u", url,
                "-f", format,
                "-q", quality,
                "-d", self.download_dir
            ]
            
            if format == "mp3":
                cmd.append("-m")  # Incluir metadatos
            elif format == "mp4":
                cmd.append("-n")  # Sin metadatos para video
            
            print(f"Ejecutando comando: {' '.join(cmd)}")
            
            # Ejecutar descarga
            download_info['message'] = 'Descargando...'
            download_info['progress'] = 20
            self.save_downloads()
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # Monitorear progreso
            for line in process.stdout:
                line = line.strip()
                if line:
                    print(f"Salida: {line}")
                    
                    # Actualizar progreso basado en la salida
                    if "progress" in line.lower() or "%" in line:
                        # Intentar extraer porcentaje
                        try:
                            # Buscar patrones comunes de progreso
                            if "[" in line and "%" in line:
                                # Formato: [download] 50.5% of 10.5MiB at 10.5MiB/s
                                percent_str = line.split("[download]")[-1].split("%")[0].strip()
                                percent = float(percent_str)
                                download_info['progress'] = 20 + (percent * 0.7)  # 20-90%
                                download_info['message'] = f"Descargando... {percent:.1f}%"
                            elif "ETA" in line:
                                download_info['message'] = f"Descargando... {line}"
                        except:
                            pass
                    
                    self.save_downloads()
            
            # Esperar a que termine
            process.wait()
            
            if process.returncode == 0:
                # Buscar archivo descargado
                downloaded_file = self._find_downloaded_file(url)
                
                if downloaded_file:
                    # Mover a la biblioteca si es MP3
                    if format == "mp3":
                        target_dir = os.path.join(self.library_dir, "downloads")
                        os.makedirs(target_dir, exist_ok=True)
                        
                        target_path = os.path.join(target_dir, os.path.basename(downloaded_file))
                        os.rename(downloaded_file, target_path)
                        
                        download_info['file_path'] = target_path
                    else:
                        download_info['file_path'] = downloaded_file
                
                download_info['status'] = 'completed'
                download_info['progress'] = 100
                download_info['message'] = 'Descarga completada exitosamente'
                download_info['end_time'] = datetime.now().isoformat()
                
            else:
                stderr = process.stderr.read()
                error_msg = stderr if stderr else "Error en la descarga"
                raise Exception(error_msg)
                
        except Exception as e:
            download_info['status'] = 'error'
            download_info['message'] = f"Error: {str(e)}"
            download_info['end_time'] = datetime.now().isoformat()
            print(f"Error en descarga {download_id}: {e}")
        
        finally:
            self.save_downloads()
    
    def _find_downloaded_file(self, url):
        """Busca el archivo descargado en el directorio"""
        try:
            # Obtener información del video usando yt-dlp
            import yt_dlp
            
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                title = info.get('title', 'video')
                
                # Buscar archivos en el directorio de descargas
                for ext in ['mp3', 'mp4', 'm4a', 'webm']:
                    pattern = f"*{title}*.{ext}"
                    for file in Path(self.download_dir).rglob(pattern):
                        if file.is_file():
                            return str(file)
        
        except Exception as e:
            print(f"Error buscando archivo: {e}")
        
        return None
    
    def get_download_status(self, download_id):
        """Obtiene el estado de una descarga"""
        return self.downloads.get(download_id)
    
    def get_all_downloads(self):
        """Obtiene todas las descargas"""
        return self.downloads
    
    def load_downloads(self):
        """Carga las descargas desde archivo"""
        downloads_file = os.path.join(self.download_dir, "downloads.json")
        if os.path.exists(downloads_file):
            try:
                with open(downloads_file, 'r') as f:
                    self.downloads = json.load(f)
            except:
                self.downloads = {}
    
    def save_downloads(self):
        """Guarda las descargas en archivo"""
        downloads_file = os.path.join(self.download_dir, "downloads.json")
        os.makedirs(os.path.dirname(downloads_file), exist_ok=True)
        
        # Limitar el número de descargas guardadas (últimas 50)
        if len(self.downloads) > 50:
            # Ordenar por fecha y mantener solo las más recientes
            sorted_items = sorted(
                self.downloads.items(),
                key=lambda x: x[1].get('start_time', ''),
                reverse=True
            )[:50]
            self.downloads = dict(sorted_items)
        
        try:
            with open(downloads_file, 'w') as f:
                json.dump(self.downloads, f, indent=2)
        except Exception as e:
            print(f"Error guardando descargas: {e}")

# Instancia global del descargador
downloader = YouTubeDownloader()
