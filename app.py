#!/usr/bin/env python3
# app.py - VideoCitrix Server principal con bibliotecas por usuario y panel de administración

from flask import Flask, render_template, jsonify, send_file, send_from_directory, request, session, redirect, url_for
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_cors import CORS
from functools import wraps
import os
import urllib.parse
import threading
import uuid
import shutil
from datetime import datetime
import yt_dlp

import library_manager as lm
import db

app = Flask(__name__)
app.secret_key = 'cambia_esta_clave_por_una_segura_videocloud789'
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
CORS(app)

# -------------------------------------------------------------------
# Directorios base
# -------------------------------------------------------------------
BASE_VIDEO_DIR      = '/mnt/exfat_disco'
BASE_THUMBNAILS_DIR = os.path.expanduser('~/.cache/yt-video/thumbnails')
BASE_CACHE_DIR      = os.path.expanduser('~/.cache/yt-video/cache')
BASE_YOUTUBE_DIR    = os.path.expanduser('~/YouTube_Downloads')

for _d in (BASE_VIDEO_DIR, BASE_THUMBNAILS_DIR, BASE_CACHE_DIR, BASE_YOUTUBE_DIR):
    os.makedirs(_d, exist_ok=True)

lm.init_directories(BASE_VIDEO_DIR, BASE_THUMBNAILS_DIR, BASE_CACHE_DIR)

YOUTUBE_DOWNLOADS = {}


# -------------------------------------------------------------------
# Helpers de directorios por usuario
# -------------------------------------------------------------------
def get_user_video_dir(user_id):
    path = os.path.join(BASE_VIDEO_DIR, f'user_{user_id}')
    os.makedirs(path, exist_ok=True)
    return path

def get_user_thumbnails_dir(user_id):
    path = os.path.join(BASE_THUMBNAILS_DIR, f'user_{user_id}')
    os.makedirs(path, exist_ok=True)
    return path

def get_user_downloads_dir(user_id):
    path = os.path.join(BASE_YOUTUBE_DIR, f'user_{user_id}')
    os.makedirs(path, exist_ok=True)
    return path


# -------------------------------------------------------------------
# Decoradores
# -------------------------------------------------------------------
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'No autorizado'}), 401
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'No autorizado'}), 401
        user = db.get_user_by_id(session['user_id'])
        if not user or user.get('role') != 'admin':
            return jsonify({'error': 'Se requieren permisos de administrador'}), 403
        return f(*args, **kwargs)
    return decorated


# -------------------------------------------------------------------
# Rutas HTML
# -------------------------------------------------------------------
@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect('/login')
    return render_template('index.html')

@app.route('/login')
def login_page():
    if 'user_id' in session:
        return redirect('/')
    return render_template('login.html')

@app.route('/register')
def register_page():
    if 'user_id' in session:
        return redirect('/')
    return render_template('register.html')


# -------------------------------------------------------------------
# API de autenticación
# -------------------------------------------------------------------
@app.route('/api/register', methods=['POST'])
def api_register():
    data     = request.json or {}
    username = data.get('username', '').strip()
    email    = data.get('email', '').strip()
    password = data.get('password', '')
    if not username or not email or not password:
        return jsonify({'error': 'Todos los campos son obligatorios'}), 400
    if len(password) < 6:
        return jsonify({'error': 'La contraseña debe tener al menos 6 caracteres'}), 400
    user = db.create_user(username, email, password)
    if user:
        get_user_video_dir(user['id'])
        return jsonify({'success': True, 'user': user})
    return jsonify({'error': 'Usuario o email ya existe'}), 400

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.json or {}
    user = db.authenticate_user(data.get('username', '').strip(), data.get('password', ''))
    if user:
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['role'] = user.get('role', 'user')
        return jsonify({'success': True, 'user': user})
    return jsonify({'error': 'Credenciales inválidas'}), 401

@app.route('/api/logout', methods=['POST'])
def api_logout():
    session.clear()
    return jsonify({'success': True})

@app.route('/api/user')
def api_current_user():
    if 'user_id' not in session:
        return jsonify({'error': 'No autenticado'}), 401
    user = db.get_user_by_id(session['user_id'])
    if not user:
        return jsonify({'error': 'Usuario no encontrado'}), 404
    vdir = get_user_video_dir(user['id'])
    user['video_count']     = len(lm.get_sorted_audio_files(vdir))
    user['storage_used_mb'] = round(lm.get_user_storage(vdir) / (1024 * 1024), 1)
    for key in ('created_at', 'last_login'):
        if user.get(key):
            user[key] = str(user[key])
    return jsonify(user)

@app.route('/api/user/password', methods=['POST'])
@login_required
def change_password():
    data = request.json or {}
    new_pw = data.get('password', '')
    if len(new_pw) < 6:
        return jsonify({'error': 'La contraseña debe tener al menos 6 caracteres'}), 400
    return jsonify({'success': db.update_user_password(session['user_id'], new_pw)})


# -------------------------------------------------------------------
# API de videos (por usuario)
# -------------------------------------------------------------------
@app.route('/api/files')
@login_required
def list_files():
    page     = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    vdir     = get_user_video_dir(session['user_id'])
    tdir     = get_user_thumbnails_dir(session['user_id'])
    files, total, has_more = lm.get_page(page, per_page, vdir, tdir)
    return jsonify({'files': files, 'total': total, 'has_more': has_more})

@app.route('/api/files/more')
@login_required
def load_more_files():
    page     = request.args.get('page', 2, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    vdir     = get_user_video_dir(session['user_id'])
    tdir     = get_user_thumbnails_dir(session['user_id'])
    files, total, has_more = lm.get_page(page, per_page, vdir, tdir)
    return jsonify({'files': files, 'total': total, 'has_more': has_more})

@app.route('/api/cover/<path:filename>')
@login_required
def serve_cover(filename):
    try:
        filename = urllib.parse.unquote(filename)
        tdir     = get_user_thumbnails_dir(session['user_id'])
        vdir     = get_user_video_dir(session['user_id'])
        thumb    = lm.get_thumbnail_path(filename, tdir)
        if os.path.exists(thumb):
            return send_file(thumb, mimetype='image/jpeg')
        thumb = lm.ensure_thumbnail(filename, vdir, tdir)
        if thumb and os.path.exists(thumb):
            return send_file(thumb, mimetype='image/jpeg')
        return send_from_directory('static', 'default-cover.png')
    except Exception as e:
        print(f"Error cover: {e}")
        return send_from_directory('static', 'default-cover.png')

@app.route('/api/stream/<path:filename>')
@login_required
def stream_video(filename):
    filename = urllib.parse.unquote(filename)
    vdir     = get_user_video_dir(session['user_id'])
    response = send_from_directory(vdir, filename)
    response.headers['Cache-Control'] = 'public, max-age=86400'
    return response

@app.route('/api/download/<path:filename>')
@login_required
def download_file(filename):
    try:
        filename  = urllib.parse.unquote(filename)
        safe_name = os.path.basename(filename)
        vdir      = get_user_video_dir(session['user_id'])
        filepath  = os.path.join(vdir, safe_name)
        if not os.path.exists(filepath):
            return jsonify({'error': 'Archivo no encontrado'}), 404
        return send_file(filepath, as_attachment=True, download_name=safe_name)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/upload', methods=['POST'])
@login_required
def upload_file():
    if 'files' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    vdir     = get_user_video_dir(session['user_id'])
    tdir     = get_user_thumbnails_dir(session['user_id'])
    uploaded = []
    for file in request.files.getlist('files'):
        if file and file.filename:
            safe = "".join(c for c in file.filename if c.isalnum() or c in (' ', '-', '_', '.'))
            file.save(os.path.join(vdir, safe))
            lm.ensure_thumbnail(safe, vdir, tdir)
            uploaded.append(safe)
    return jsonify({'success': True, 'files': uploaded})

@app.route('/api/delete/<path:filename>', methods=['DELETE'])
@login_required
def delete_file(filename):
    filename = urllib.parse.unquote(filename)
    vdir     = get_user_video_dir(session['user_id'])
    tdir     = get_user_thumbnails_dir(session['user_id'])
    filepath = os.path.join(vdir, filename)
    if not os.path.exists(filepath):
        return jsonify({'error': 'No encontrado'}), 404
    os.remove(filepath)
    thumb = lm.get_thumbnail_path(filename, tdir)
    if os.path.exists(thumb):
        os.remove(thumb)
    return jsonify({'success': True})

@app.route('/api/search')
@login_required
def search_files():
    query = request.args.get('q', '').lower()
    if not query or len(query) < 2:
        return jsonify([])
    vdir    = get_user_video_dir(session['user_id'])
    tdir    = get_user_thumbnails_dir(session['user_id'])
    results = []
    for f in lm.get_sorted_audio_files(vdir):
        if query in f.lower():
            info = lm.get_audio_info_fast(f, vdir, tdir)
            if info:
                results.append(info)
    return jsonify(results[:50])

@app.route('/api/stats')
@login_required
def get_stats():
    vdir = get_user_video_dir(session['user_id'])
    return jsonify({
        'total_files': len(lm.get_sorted_audio_files(vdir)),
        'total_size': f"{lm.get_user_storage(vdir)/(1024**3):.2f} GB",
        'server_status': 'online'
    })

@app.route('/api/refresh', methods=['POST'])
@login_required
def refresh_library():
    return jsonify({'success': True})


# -------------------------------------------------------------------
# Thumbnails en segundo plano
# -------------------------------------------------------------------
@app.route('/api/thumbnails/process', methods=['POST'])
@login_required
def start_thumbnail_processing():
    uid  = session['user_id']
    vdir = get_user_video_dir(uid)
    tdir = get_user_thumbnails_dir(uid)
    started = lm.start_thumbnail_processing(uid, vdir, tdir)
    return jsonify({'status': 'started' if started else 'already_processing'})

@app.route('/api/thumbnails/progress')
@login_required
def get_thumbnail_progress():
    return jsonify(lm.get_thumbnail_progress(session['user_id']))


# -------------------------------------------------------------------
# YouTube (por usuario) - descarga como MP4
# -------------------------------------------------------------------
def run_download(download_id, url, download_type, effective_limit, user_id):
    dl   = YOUTUBE_DOWNLOADS[download_id]
    vdir = get_user_video_dir(user_id)
    tdir = get_user_thumbnails_dir(user_id)
    ydl_dir = os.path.join(get_user_downloads_dir(user_id), download_id[:8])
    os.makedirs(ydl_dir, exist_ok=True)
    dl.update({'status': 'downloading', 'progress': 0, 'message': 'Conectando con YouTube...'})

    try:
        counter = {'n': 0, 'total': 1, 'last_file': ''}

        def hook(d):
            if d['status'] == 'downloading':
                fname = d.get('filename', '')
                if fname != counter['last_file']:
                    counter['last_file'] = fname
                    counter['n'] += 1
                    if counter['total'] > 1:
                        dl['current_item'] = counter['n']
                        dl['total_items']  = counter['total']
                        dl['message'] = f"Video {counter['n']} de {counter['total']}"
                total_b    = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
                downloaded = d.get('downloaded_bytes', 0)
                if total_b > 0:
                    item_pct = downloaded / total_b
                    overall  = ((counter['n'] - 1 + item_pct) / counter['total']) * 100 if counter['total'] > 1 else item_pct * 88
                    dl['progress'] = round(min(overall, 95), 1)
            elif d['status'] == 'finished':
                dl['message'] = 'Procesando video...'

        ydl_opts = {
            'format': 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=1080]+bestaudio/best',
            'outtmpl': os.path.join(ydl_dir, '%(title)s.%(ext)s'),
            'writethumbnail': True,
            'postprocessors': [
                {'key': 'FFmpegVideoConvertor', 'preferedformat': 'mp4'},
                {'key': 'EmbedThumbnail', 'already_have_thumbnail': False},
            ],
            'progress_hooks': [hook],
            'quiet': True, 'no_warnings': True,
            'ignoreerrors': download_type == 'playlist',
            'retries': 5,
            'fragment_retries': 5,
            'concurrent_fragment_downloads': 1,
            'merge_output_format': 'mp4',
        }
        if download_type == 'playlist' and effective_limit:
            ydl_opts['playlistend'] = effective_limit

        if download_type == 'playlist':
            try:
                with yt_dlp.YoutubeDL({'quiet': True, 'extract_flat': True, 'ignoreerrors': True}) as ydl_flat:
                    flat = ydl_flat.extract_info(url, download=False)
                    if flat and 'entries' in flat:
                        entries = [e for e in flat['entries'] if e]
                        total   = min(len(entries), effective_limit) if effective_limit else len(entries)
                        counter['total']   = max(total, 1)
                        dl['total_items']  = counter['total']
                        dl['message'] = f"Descargando {counter['total']} videos..."
            except Exception:
                counter['total'] = effective_limit or 10
        else:
            counter['total'] = 1
            counter['n']     = 1

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        # Mover MP4s al directorio del usuario
        moved = []
        for f in os.listdir(ydl_dir):
            if f.lower().endswith('.mp4'):
                src = os.path.join(ydl_dir, f)
                dst = os.path.join(vdir, f)
                try:
                    if os.path.exists(dst):
                        os.remove(dst)
                    shutil.move(src, dst)
                    moved.append(f)
                    lm.ensure_thumbnail(f, vdir, tdir)
                except Exception as e:
                    print(f"Error moviendo {f}: {e}")

        try:
            shutil.rmtree(ydl_dir)
        except Exception:
            pass

        dl.update({'status': 'completed', 'progress': 100, 'file_count': len(moved),
                   'message': f'{len(moved)} video(s) descargado(s)',
                   'end_time': datetime.now().isoformat()})
    except Exception as e:
        print(f"Error descarga {download_id}: {e}")
        try:
            shutil.rmtree(ydl_dir)
        except Exception:
            pass
        dl.update({'status': 'error', 'message': f'Error: {str(e)[:300]}',
                   'end_time': datetime.now().isoformat()})


@app.route('/api/youtube/download', methods=['POST'])
@login_required
def download_youtube_video():
    data          = request.json or {}
    url           = data.get('url', '').strip()
    download_type = data.get('type', 'single')
    limit         = data.get('limit')
    if not url:
        return jsonify({'error': 'URL requerida'}), 400
    effective_limit = int(limit) if limit else (10 if download_type == 'playlist' else None)
    download_id = str(uuid.uuid4())
    YOUTUBE_DOWNLOADS[download_id] = {
        'id': download_id, 'url': url, 'type': download_type,
        'status': 'starting', 'progress': 0, 'message': 'Iniciando...',
        'file_count': 0, 'start_time': datetime.now().isoformat(),
        'end_time': None, 'user_id': session['user_id'],
    }
    threading.Thread(
        target=run_download,
        args=(download_id, url, download_type, effective_limit, session['user_id']),
        daemon=True
    ).start()
    return jsonify({'download_id': download_id, 'success': True})

@app.route('/api/youtube/status/<download_id>')
@login_required
def get_youtube_download_status(download_id):
    dl = YOUTUBE_DOWNLOADS.get(download_id)
    if not dl:
        return jsonify({'error': 'Descarga no encontrada'}), 404
    return jsonify(dl)

@app.route('/api/youtube/downloads')
@login_required
def list_youtube_downloads():
    uid      = session['user_id']
    user_dls = {k: v for k, v in YOUTUBE_DOWNLOADS.items() if v.get('user_id') == uid}
    return jsonify({'downloads': user_dls})

@app.route('/api/youtube/clear', methods=['POST'])
@login_required
def clear_youtube_downloads():
    uid    = session['user_id']
    to_del = [k for k, v in YOUTUBE_DOWNLOADS.items() if v.get('user_id') == uid]
    for k in to_del:
        del YOUTUBE_DOWNLOADS[k]
    return jsonify({'success': True})

@app.route('/api/cache/clear', methods=['POST'])
@login_required
def clear_cache():
    try:
        user_cache = os.path.join(BASE_CACHE_DIR, f'user_{session["user_id"]}')
        if os.path.exists(user_cache):
            shutil.rmtree(user_cache)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# -------------------------------------------------------------------
# API de administración
# -------------------------------------------------------------------
@app.route('/api/admin/users')
@admin_required
def admin_list_users():
    users = db.get_all_users()
    for u in users:
        vdir = get_user_video_dir(u['id'])
        u['video_count'] = len(lm.get_sorted_audio_files(vdir))
        u['storage_mb']  = round(lm.get_user_storage(vdir) / (1024 * 1024), 1)
    return jsonify({'users': users})

@app.route('/api/admin/users/<int:user_id>', methods=['DELETE'])
@admin_required
def admin_delete_user(user_id):
    if user_id == session['user_id']:
        return jsonify({'error': 'No puedes eliminarte a ti mismo'}), 400
    return jsonify({'success': db.delete_user(user_id)})

@app.route('/api/admin/users/<int:user_id>/role', methods=['POST'])
@admin_required
def admin_update_role(user_id):
    data = request.json or {}
    role = data.get('role', 'user')
    return jsonify({'success': db.update_user_role(user_id, role)})

@app.route('/api/admin/stats')
@admin_required
def admin_stats():
    users       = db.get_all_users()
    total_videos = 0
    total_size  = 0
    for u in users:
        vdir = get_user_video_dir(u['id'])
        total_videos += len(lm.get_sorted_audio_files(vdir))
        total_size   += lm.get_user_storage(vdir)
    return jsonify({
        'total_users':  len(users),
        'total_videos': total_videos,
        'total_size_gb': round(total_size / (1024 ** 3), 2),
    })


# -------------------------------------------------------------------
# Estáticos
# -------------------------------------------------------------------
@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)


if __name__ == '__main__':
    print("🎬 VideoCitrix Server iniciado en http://localhost:5002")
    app.run(host='0.0.0.0', port=5002, debug=True, threaded=True)
