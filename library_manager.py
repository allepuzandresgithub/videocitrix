#!/usr/bin/env python3
# library_manager.py - Gestión de biblioteca con soporte por usuario

import os
import time
import threading
import subprocess
import hashlib
import concurrent.futures
from datetime import datetime
import urllib.parse

try:
    from mutagen import File
    from mutagen.id3 import ID3, APIC
    from mutagen.mp4 import MP4, MP4Cover
    from mutagen.flac import FLAC, Picture
    MUTAGEN_AVAILABLE = True
except ImportError:
    MUTAGEN_AVAILABLE = False
    print("⚠️ [library_manager] mutagen no instalado. Las portadas se extraerán solo con ffmpeg.")

# Directorios base (globales, se configuran desde app.py)
MUSIC_DIR = None
THUMBNAILS_DIR = None
CACHE_DIR = None

DURATION_CACHE = {}

# Progreso de thumbnails por usuario
_thumbnail_progress = {}
_thumbnail_locks = {}
_global_lock = threading.Lock()


def init_directories(music_dir, thumbnails_dir, cache_dir):
    global MUSIC_DIR, THUMBNAILS_DIR, CACHE_DIR
    MUSIC_DIR = music_dir
    THUMBNAILS_DIR = thumbnails_dir
    CACHE_DIR = cache_dir
    os.makedirs(THUMBNAILS_DIR, exist_ok=True)
    os.makedirs(CACHE_DIR, exist_ok=True)


# -------------------------------------------------------------------
# Thumbnails
# -------------------------------------------------------------------

def get_thumbnail_path(audio_filename, thumbnails_dir=None):
    tdir = thumbnails_dir or THUMBNAILS_DIR
    file_hash = hashlib.md5(audio_filename.encode('utf-8')).hexdigest()
    return os.path.join(tdir, f"{file_hash}.jpg")


def has_video_stream(filepath):
    try:
        cmd = ['ffprobe', '-v', 'error', '-select_streams', 'v:0',
               '-show_entries', 'stream=codec_type',
               '-of', 'default=noprint_wrappers=1:nokey=1', filepath]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        return result.returncode == 0 and result.stdout.strip() == 'video'
    except:
        return False


def extract_thumbnail_with_mutagen(audio_path, thumbnail_path):
    try:
        audio = File(audio_path)
        if audio is None:
            return False
        if hasattr(audio, 'tags') and audio.tags:
            for tag in audio.tags.values():
                if isinstance(tag, APIC):
                    with open(thumbnail_path, 'wb') as f:
                        f.write(tag.data)
                    return True
        if isinstance(audio, MP4) and 'covr' in audio:
            cover_data = audio['covr'][0]
            if isinstance(cover_data, MP4Cover):
                with open(thumbnail_path, 'wb') as f:
                    f.write(cover_data)
                return True
        if isinstance(audio, FLAC) and audio.pictures:
            with open(thumbnail_path, 'wb') as f:
                f.write(audio.pictures[0].data)
            return True
        return False
    except Exception:
        return False


def extract_thumbnail_with_ffmpeg(audio_path, thumbnail_path):
    if not has_video_stream(audio_path):
        return False
    try:
        cmd = ['ffmpeg', '-i', audio_path, '-an', '-c:v', 'copy',
               '-map', '0:v:0', '-frames:v', '1', '-f', 'image2',
               '-y', '-loglevel', 'error', thumbnail_path]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        return result.returncode == 0 and os.path.exists(thumbnail_path) and os.path.getsize(thumbnail_path) > 0
    except:
        return False


def ensure_thumbnail(audio_filename, music_dir=None, thumbnails_dir=None):
    try:
        mdir = music_dir or MUSIC_DIR
        audio_path = os.path.join(mdir, audio_filename)
        thumb_path = get_thumbnail_path(audio_filename, thumbnails_dir)
        if os.path.exists(thumb_path) and os.path.getsize(thumb_path) > 0:
            return thumb_path
        if MUTAGEN_AVAILABLE:
            if extract_thumbnail_with_mutagen(audio_path, thumb_path):
                return thumb_path
        if extract_thumbnail_with_ffmpeg(audio_path, thumb_path):
            return thumb_path
        return None
    except Exception:
        return None


# -------------------------------------------------------------------
# Duración y metadatos
# -------------------------------------------------------------------

def get_duration_for_file(filename, music_dir=None):
    cache_key = f"{music_dir or MUSIC_DIR}:{filename}"
    if cache_key in DURATION_CACHE:
        return DURATION_CACHE[cache_key]
    mdir = music_dir or MUSIC_DIR
    filepath = os.path.join(mdir, filename)
    if not os.path.exists(filepath):
        return '0:00'
    try:
        cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
               '-of', 'default=noprint_wrappers=1:nokey=1', filepath]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=2)
        if result.returncode == 0 and result.stdout.strip():
            seconds = float(result.stdout.strip())
            duration = f"{int(seconds//60)}:{int(seconds%60):02d}"
            DURATION_CACHE[cache_key] = duration
            return duration
    except:
        pass
    return '0:00'


def get_audio_info_fast(filename, music_dir=None, thumbnails_dir=None):
    try:
        mdir = music_dir or MUSIC_DIR
        filepath = os.path.join(mdir, filename)
        if not os.path.exists(filepath):
            return None
        stat = os.stat(filepath)
        ext = filename.lower()
        if ext.endswith('.mp3'):
            file_type, color = 'audio', '#8b5cf6'
        elif ext.endswith('.mp4'):
            file_type, color = 'video', '#ef4444'
        else:
            file_type, color = 'audio', '#6d28d9'
        thumb_path = get_thumbnail_path(filename, thumbnails_dir)
        has_cover = os.path.exists(thumb_path) and os.path.getsize(thumb_path) > 0
        return {
            'name': filename,
            'size': _format_size(stat.st_size),
            'duration': get_duration_for_file(filename, mdir),
            'date': datetime.fromtimestamp(stat.st_mtime).strftime('%d/%m/%Y %H:%M'),
            'timestamp': stat.st_mtime,
            'filesize': stat.st_size,
            'type': file_type,
            'color': color,
            'has_cover': has_cover,
            'cover_url': f'/api/cover/{urllib.parse.quote(filename)}' if has_cover else '/static/default-cover.png',
            'path': f'/api/stream/{urllib.parse.quote(filename)}'
        }
    except Exception:
        return None


def _format_size(bytes_size):
    if bytes_size < 1024:
        return f"{bytes_size} B"
    elif bytes_size < 1024 * 1024:
        return f"{bytes_size/1024:.1f} KB"
    elif bytes_size < 1024 * 1024 * 1024:
        return f"{bytes_size/(1024*1024):.1f} MB"
    else:
        return f"{bytes_size/(1024*1024*1024):.2f} GB"


# -------------------------------------------------------------------
# Listado con paginación
# -------------------------------------------------------------------

def get_sorted_audio_files(music_dir=None):
    mdir = music_dir or MUSIC_DIR
    if not mdir or not os.path.exists(mdir):
        return []
    try:
        supported = ('.mp3', '.mp4', '.m4a', '.webm', '.ogg', '.flac', '.wav', '.wma', '.aac')
        audio_files = [f for f in os.listdir(mdir) if f.lower().endswith(supported)]
        files_with_time = []
        for f in audio_files:
            try:
                mtime = os.path.getmtime(os.path.join(mdir, f))
                files_with_time.append((f, mtime))
            except:
                files_with_time.append((f, 0))
        files_with_time.sort(key=lambda x: x[1], reverse=True)
        return [f for f, _ in files_with_time]
    except:
        return []


def get_page(page, per_page=50, music_dir=None, thumbnails_dir=None):
    all_files = get_sorted_audio_files(music_dir)
    total = len(all_files)
    start = (page - 1) * per_page
    end = start + per_page
    result = []
    for filename in all_files[start:end]:
        info = get_audio_info_fast(filename, music_dir, thumbnails_dir)
        if info:
            result.append(info)
    return result, total, end < total


def get_user_storage(music_dir):
    """Devuelve el total de bytes usados por un usuario."""
    if not music_dir or not os.path.exists(music_dir):
        return 0
    total = 0
    for f in os.listdir(music_dir):
        fp = os.path.join(music_dir, f)
        if os.path.isfile(fp):
            try:
                total += os.path.getsize(fp)
            except:
                pass
    return total


# -------------------------------------------------------------------
# Procesamiento de thumbnails en segundo plano (por usuario)
# -------------------------------------------------------------------

def _get_user_lock(user_id):
    with _global_lock:
        if user_id not in _thumbnail_locks:
            _thumbnail_locks[user_id] = threading.Lock()
        return _thumbnail_locks[user_id]


def _process_thumbnails_for_user(user_id, music_dir, thumbnails_dir):
    lock = _get_user_lock(user_id)
    progress = {'status': 'processing', 'total': 0, 'processed': 0,
                'percentage': 0, 'current_file': '', 'error': None}
    with _global_lock:
        _thumbnail_progress[user_id] = progress
    try:
        all_files = get_sorted_audio_files(music_dir)
        to_process = [f for f in all_files
                      if not os.path.exists(get_thumbnail_path(f, thumbnails_dir))
                      or os.path.getsize(get_thumbnail_path(f, thumbnails_dir)) == 0]
        progress['total'] = len(to_process)
        if not to_process:
            progress.update({'status': 'completed', 'percentage': 100})
            return
        for i, filename in enumerate(to_process):
            progress['current_file'] = filename
            ensure_thumbnail(filename, music_dir, thumbnails_dir)
            progress['processed'] = i + 1
            progress['percentage'] = int(((i + 1) / len(to_process)) * 100)
        progress.update({'status': 'completed', 'percentage': 100, 'current_file': ''})
    except Exception as e:
        progress.update({'status': 'error', 'error': str(e)})


def start_thumbnail_processing(user_id=None, music_dir=None, thumbnails_dir=None):
    uid = user_id or 'global'
    with _global_lock:
        prog = _thumbnail_progress.get(uid, {})
        if prog.get('status') == 'processing':
            return False
    thread = threading.Thread(
        target=_process_thumbnails_for_user,
        args=(uid, music_dir or MUSIC_DIR, thumbnails_dir or THUMBNAILS_DIR),
        daemon=True
    )
    thread.start()
    return True


def get_thumbnail_progress(user_id=None):
    uid = user_id or 'global'
    with _global_lock:
        return _thumbnail_progress.get(uid, {
            'status': 'idle', 'total': 0, 'processed': 0,
            'percentage': 0, 'current_file': '', 'error': None
        }).copy()
