#!/bin/bash
# start_server.sh - Arranca MySQL y VideoCitrix Server

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="/tmp/videocitrix_server.log"
PID_FILE="/tmp/videocitrix_server.pid"

echo "🎬 Iniciando VideoCitrix..."

# ---- MySQL / MariaDB ----
echo "🗄️  Verificando MySQL..."
if systemctl is-active --quiet mysql 2>/dev/null; then
    echo "   ✅ MySQL ya estaba corriendo"
elif systemctl is-active --quiet mariadb 2>/dev/null; then
    echo "   ✅ MariaDB ya estaba corriendo"
else
    echo "   ▶️  Arrancando MySQL..."
    sudo systemctl start mysql 2>/dev/null || sudo systemctl start mariadb 2>/dev/null || {
        echo "   ❌ No se pudo arrancar MySQL"
        echo "      Prueba: sudo systemctl status mysql"
        exit 1
    }
    sleep 2
    echo "   ✅ MySQL iniciado"
fi

# ---- Matar servidor anterior si existe ----
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if kill -0 "$OLD_PID" 2>/dev/null; then
        echo "🛑  Deteniendo servidor anterior (PID $OLD_PID)..."
        kill "$OLD_PID" 2>/dev/null
        sleep 1
    fi
    rm -f "$PID_FILE"
fi

# Liberar puerto 5002 por si acaso
fuser -k 5002/tcp 2>/dev/null || true
sleep 1

# ---- Flask Server ----
echo "🚀  Arrancando servidor Flask..."
cd "$SCRIPT_DIR"

nohup python3 app.py > "$LOG_FILE" 2>&1 &
SERVER_PID=$!
echo "$SERVER_PID" > "$PID_FILE"

sleep 3

if kill -0 "$SERVER_PID" 2>/dev/null; then
    IP=$(hostname -I | awk '{print $1}')
    echo ""
    echo "   ✅ VideoCitrix corriendo (PID $SERVER_PID)"
    echo "   🌐  http://localhost:5002"
    echo "   🌐  http://${IP}:5002"
    echo ""
    echo "   Log en tiempo real: tail -f $LOG_FILE"
    echo "   Para parar:         kill \$(cat $PID_FILE)"
else
    echo "   ❌ El servidor no arrancó. Log:"
    cat "$LOG_FILE"
    exit 1
fi
