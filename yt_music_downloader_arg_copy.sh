#!/bin/bash

# YouTube Downloader - VERSIÓN SOLO ARGUMENTOS 5.3
# No usa cookies del navegador

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# Variables
VERSION="5.3"
DOWNLOAD_DIR="/mnt/exfat_disco"
QUALITY="alta"
INCLUDE_METADATA=true
DOWNLOAD_FORMAT="mp3"
CONFIG_FILE="$HOME/.yt-downloader-config"

# Variables para argumentos
URL_TO_DOWNLOAD=""
DOWNLOAD_TYPE="single"
PLAYLIST_LIMIT=""

# Mostrar ayuda
show_usage() {
    echo -e "${CYAN}YouTube Downloader v$VERSION${NC}"
    echo "Descarga videos/audio de YouTube usando yt-dlp"
    echo ""
    echo "Uso: $0 -u URL [OPCIONES]"
    echo ""
    echo "Opciones obligatorias:"
    echo "  -u, --url URL          URL de YouTube a descargar"
    echo ""
    echo "Opciones opcionales:"
    echo "  -t, --type TYPE        Tipo de descarga: single, playlist (default: single)"
    echo "  -d, --dir DIRECTORIO   Directorio de descarga (default: ~/YouTube_Downloads)"
    echo "  -f, --format FORMATO   Formato: mp3 o mp4 (default: mp3)"
    echo "  -q, --quality CALIDAD  Calidad: alta, media, baja (default: alta)"
    echo "  -m, --metadata         Incluir metadatos (default: sí)"
    echo "  -n, --no-metadata      No incluir metadatos"
    echo "  -l, --limit NUM        Límite de videos (para playlists/mixes)"
    echo "  -c, --config           Mostrar configuración actual"
    echo "  -h, --help             Mostrar esta ayuda"
    echo "  -v, --version          Mostrar versión"
    echo ""
    echo "Ejemplos:"
    echo "  $0 -u \"https://youtube.com/watch?v=abc123\""
    echo "  $0 -u \"https://youtube.com/playlist?list=xyz789\" -t playlist -l 10"
    echo "  $0 -u \"https://youtube.com/watch?v=abc123\" -f mp4 -q media"
    echo "  $0 -u \"https://youtube.com/watch?v=abc123\" -n -d ~/Music"
    echo ""
    exit 0
}

# Mostrar versión
show_version() {
    echo -e "${CYAN}YouTube Downloader v$VERSION${NC}"
    exit 0
}

# Mostrar configuración
show_config() {
    echo -e "${CYAN}Configuración actual:${NC}"
    echo "  Directorio: $DOWNLOAD_DIR"
    echo "  Formato: $DOWNLOAD_FORMAT"
    echo "  Calidad: $QUALITY"
    echo "  Metadatos: $([ "$INCLUDE_METADATA" = true ] && echo "Activados" || echo "Desactivados")"
    echo "  Archivo config: $CONFIG_FILE"
    exit 0
}

# Cargar configuración
load_config() {
    [[ -f "$CONFIG_FILE" ]] && source "$CONFIG_FILE"
}

# Guardar configuración
save_config() {
    echo "DOWNLOAD_DIR=\"$DOWNLOAD_DIR\"" > "$CONFIG_FILE"
    echo "QUALITY=\"$QUALITY\"" >> "$CONFIG_FILE"
    echo "INCLUDE_METADATA=\"$INCLUDE_METADATA\"" >> "$CONFIG_FILE"
    echo "DOWNLOAD_FORMAT=\"$DOWNLOAD_FORMAT\"" >> "$CONFIG_FILE"
}

# Verificar PATH de yt-dlp
check_path() {
    if ! command -v yt-dlp &> /dev/null; then
        echo -e "${RED}ADVERTENCIA: yt-dlp no está en PATH${NC}"
        echo "Ejecuta: export PATH=\"\$HOME/.local/bin:\$PATH\""
        export PATH="$HOME/.local/bin:$PATH"

        if ! command -v yt-dlp &> /dev/null; then
            echo -e "${RED}ERROR: yt-dlp no encontrado${NC}"
            echo "Instala con: pip3 install yt-dlp --break-system-packages"
            return 1
        fi
    fi
    
    # Verificar ffmpeg
    if ! command -v ffmpeg &> /dev/null; then
        echo -e "${YELLOW}ADVERTENCIA: ffmpeg no está instalado${NC}"
        echo "Para mejor calidad de audio, instala: sudo apt install ffmpeg"
    fi
    
    return 0
}




# Procesar argumentos
process_arguments() {
    local has_url=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            -u|--url)
                if [[ -z "$2" ]] || [[ "$2" == -* ]]; then
                    echo -e "${RED}ERROR: Se requiere URL después de -u${NC}"
                    exit 1
                fi
                URL_TO_DOWNLOAD="$2"
                has_url=true
                shift 2
                ;;
            -t|--type)
                if [[ -z "$2" ]] || [[ "$2" == -* ]]; then
                    echo -e "${RED}ERROR: Se requiere tipo después de -t${NC}"
                    exit 1
                fi
                if [[ "$2" != "single" && "$2" != "playlist" ]]; then
                    echo -e "${RED}ERROR: Tipo debe ser 'single' o 'playlist'${NC}"
                    exit 1
                fi
                DOWNLOAD_TYPE="$2"
                shift 2
                ;;
            -d|--dir)
                if [[ -z "$2" ]] || [[ "$2" == -* ]]; then
                    echo -e "${RED}ERROR: Se requiere directorio después de -d${NC}"
                    exit 1
                fi
                DOWNLOAD_DIR="$2"
                shift 2
                ;;
            -f|--format)
                if [[ -z "$2" ]] || [[ "$2" == -* ]]; then
                    echo -e "${RED}ERROR: Se requiere formato después de -f${NC}"
                    exit 1
                fi
                if [[ "$2" != "mp3" && "$2" != "mp4" ]]; then
                    echo -e "${RED}ERROR: Formato debe ser 'mp3' o 'mp4'${NC}"
                    exit 1
                fi
                DOWNLOAD_FORMAT="$2"
                shift 2
                ;;
            -q|--quality)
                if [[ -z "$2" ]] || [[ "$2" == -* ]]; then
                    echo -e "${RED}ERROR: Se requiere calidad después de -q${NC}"
                    exit 1
                fi
                if [[ "$2" != "alta" && "$2" != "media" && "$2" != "baja" ]]; then
                    echo -e "${RED}ERROR: Calidad debe ser 'alta', 'media' o 'baja'${NC}"
                    exit 1
                fi
                QUALITY="$2"
                shift 2
                ;;
            -m|--metadata)
                INCLUDE_METADATA=true
                shift
                ;;
            -n|--no-metadata)
                INCLUDE_METADATA=false
                shift
                ;;
            -l|--limit)
                if [[ -z "$2" ]] || [[ "$2" == -* ]]; then
                    echo -e "${RED}ERROR: Se requiere número después de -l${NC}"
                    exit 1
                fi
                if ! [[ "$2" =~ ^[0-9]+$ ]]; then
                    echo -e "${RED}ERROR: Límite debe ser un número positivo${NC}"
                    exit 1
                fi
                PLAYLIST_LIMIT="$2"
                shift 2
                ;;
            -c|--config)
                show_config
                ;;
            -v|--version)
                show_version
                ;;
            -h|--help)
                show_usage
                ;;
            *)
                echo -e "${RED}ERROR: Argumento desconocido: $1${NC}"
                show_usage
                ;;
        esac
    done
    
    # Verificar que se proporcionó URL
    if [ "$has_url" = false ]; then
        echo -e "${RED}ERROR: Se requiere URL con -u${NC}"
        echo "Usa $0 -h para ver ayuda"
        exit 1
    fi
}

# Función principal de descarga
perform_download() {
    local url="$1"
    local download_type="$2"
    local playlist_limit="$3"
    
    echo -e "${CYAN}=== YouTube Downloader v$VERSION ===${NC}"
    echo ""
    
    # Mostrar configuración
    echo -e "${YELLOW}Configuración:${NC}"
    echo "  URL: $url"
    echo "  Tipo: $download_type"
    echo "  Formato: $DOWNLOAD_FORMAT"
    echo "  Calidad: $QUALITY"
    echo "  Metadatos: $([ "$INCLUDE_METADATA" = true ] && echo "Sí" || echo "No")"
    echo "  Directorio: $DOWNLOAD_DIR"
    [[ -n "$playlist_limit" ]] && echo "  Límite: $playlist_limit videos"
    echo ""
    
    # Crear directorio si no existe
    mkdir -p "$DOWNLOAD_DIR"
    
    # Construir comando base SIN COOKIES
    local cmd="yt-dlp"
    
    # Configurar formato y calidad
    if [ "$DOWNLOAD_FORMAT" = "mp3" ]; then
        cmd="$cmd --extract-audio --audio-format mp3"
        
        # Calidad de audio
        case $QUALITY in
            alta) cmd="$cmd --audio-quality 0" ;;      # 320kbps
            media) cmd="$cmd --audio-quality 5" ;;     # 192kbps
            baja) cmd="$cmd --audio-quality 9" ;;      # 128kbps
            *) cmd="$cmd --audio-quality 0" ;;
        esac
    else
        # Para MP4 - Configurar calidad de video
        case $QUALITY in
            alta) cmd="$cmd --format 'bestvideo[height<=1080]+bestaudio/best[height<=1080]'" ;;
            media) cmd="$cmd --format 'bestvideo[height<=720]+bestaudio/best[height<=720]'" ;;
            baja) cmd="$cmd --format 'bestvideo[height<=480]+bestaudio/best[height<=480]'" ;;
            *) cmd="$cmd --format 'bestvideo+bestaudio/best'" ;;
        esac
        
        cmd="$cmd --merge-output-format mp4"
    fi
    
    # Configurar metadatos
    if [ "$INCLUDE_METADATA" = true ]; then
        cmd="$cmd --add-metadata --embed-thumbnail"
        if [ "$DOWNLOAD_FORMAT" = "mp3" ]; then
            cmd="$cmd --convert-thumbnails jpg"
        fi
    fi
    
    # Opciones para mejorar estabilidad SIN COOKIES
    cmd="$cmd --retries 5"
    cmd="$cmd --fragment-retries 5"
    cmd="$cmd --socket-timeout 30"
    
    # Manejar playlists
    if [[ "$download_type" == "playlist" ]] || [[ "$url" == *"playlist?list="* ]]; then
        cmd="$cmd --yes-playlist"
        echo -e "${YELLOW}Detectada playlist${NC}"
    fi
    
    # Aplicar límite si es especificado
    if [[ -n "$playlist_limit" ]]; then
        cmd="$cmd --playlist-end $playlist_limit"
    elif [[ "$url" == *"list=RD"* ]]; then
        # Límite por defecto para mixes
        cmd="$cmd --playlist-end 100"
        echo -e "${YELLOW}Detectado mix/radio - Límite: 100 videos${NC}"
    fi
    
    # Configurar patrón de salida
    if [[ "$download_type" == "playlist" || "$url" == *"playlist?list="* ]]; then
        if [ "$DOWNLOAD_FORMAT" = "mp3" ]; then
            cmd="$cmd -o \"$DOWNLOAD_DIR/%(playlist_title)s/%(playlist_index)s - %(title)s.%(ext)s\""
        else
            cmd="$cmd -o \"$DOWNLOAD_DIR/%(playlist_title)s/%(playlist_index)s - %(title)s.mp4\""
        fi
    else
        if [ "$DOWNLOAD_FORMAT" = "mp3" ]; then
            cmd="$cmd -o \"$DOWNLOAD_DIR/%(title)s.%(ext)s\""
        else
            cmd="$cmd -o \"$DOWNLOAD_DIR/%(title)s.mp4\""
        fi
    fi
    
    # Agregar URL al comando
    cmd="$cmd \"$url\""
    
    echo -e "${YELLOW}Iniciando descarga...${NC}"
    echo -e "Comando: ${BLUE}$cmd${NC}"
    echo ""
    
    # Ejecutar descarga
    eval $cmd
    
    # Verificar resultado
    if [[ $? -eq 0 ]]; then
        echo ""
        echo -e "${GREEN}✓ Descarga completada exitosamente${NC}"
        return 0
    else
        echo ""
        echo -e "${RED}✗ Error en la descarga${NC}"
        echo ""
        echo -e "${YELLOW}Sugerencias:${NC}"
        echo "1. Verifica que la URL sea correcta"
        echo "2. Actualiza yt-dlp: pip3 install --upgrade yt-dlp"
        echo "3. Intenta sin metadatos: usa -n"
        echo "4. Prueba con otra calidad: -q media"
        return 1
    fi
}



# ============================================
# INICIO DEL SCRIPT
# ============================================

# Procesar argumentos
process_arguments "$@"

# Cargar configuración previa
load_config

# Verificar dependencias
if ! check_path; then
    exit 1
fi

# Guardar configuración actualizada
save_config

# Realizar descarga
perform_download "$URL_TO_DOWNLOAD" "$DOWNLOAD_TYPE" "$PLAYLIST_LIMIT"
exit_code=$?

# Salir con código apropiado
exit $exit_code
