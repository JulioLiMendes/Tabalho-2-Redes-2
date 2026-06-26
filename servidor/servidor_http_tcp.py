# =============================================================
# servidor_http_tcp.py — HTTP/1.1 sobre TCP
# Autor: JULIO CESAR DE LIMA MENDES | Matrícula: 20249006910
# =============================================================

import socket, os, sys, time, csv
from datetime import datetime

sys.path.insert(0, '/app')
from config import HOST_SERVIDOR, PORTA_HTTP, X_CUSTOM_AUTH, TAMANHO_CHUNK, LOG_DIR, WWW_DIR

os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "servidor_http_tcp.log")

TIPOS_MIME = {
    ".html": "text/html; charset=utf-8",
    ".bin" : "application/octet-stream",
    ".txt" : "text/plain; charset=utf-8",
}

def log(msg):
    linha = f"[{datetime.now().strftime('%H:%M:%S.%f')}] [HTTP-TCP-SERVIDOR] {msg}"
    print(linha)
    with open(LOG_FILE, "a") as f:
        f.write(linha + "\n")

def get_mime(caminho):
    return TIPOS_MIME.get(os.path.splitext(caminho)[1].lower(), "application/octet-stream")

def servir(conn, addr):
    try:
        conn.settimeout(10.0)
        raw = b""
        while b"\r\n\r\n" not in raw:
            chunk = conn.recv(4096)
            if not chunk:
                break
            raw += chunk

        linha = raw.decode(errors="ignore").split("\r\n")[0].split()
        if len(linha) < 2 or linha[0] != "GET":
            conn.sendall(b"HTTP/1.1 405 Method Not Allowed\r\n\r\n")
            return

        caminho = linha[1]
        if caminho == "/":
            caminho = "/index.html"

        log(f"{addr} | GET {caminho}")
        arquivo = os.path.join(WWW_DIR, caminho.lstrip("/"))

        if not os.path.isfile(arquivo):
            corpo  = b"<html><body><h1>404 Not Found</h1></body></html>"
            header = (f"HTTP/1.1 404 Not Found\r\nContent-Type: text/html\r\n"
                      f"Content-Length: {len(corpo)}\r\nX-Custom-Auth: {X_CUSTOM_AUTH}\r\n"
                      f"Connection: close\r\n\r\n").encode()
            conn.sendall(header + corpo)
            log(f"  -> 404")
            return

        tamanho = os.path.getsize(arquivo)
        header  = (f"HTTP/1.1 200 OK\r\nContent-Type: {get_mime(arquivo)}\r\n"
                   f"Content-Length: {tamanho}\r\nX-Custom-Auth: {X_CUSTOM_AUTH}\r\n"
                   f"Connection: close\r\n\r\n").encode()
        conn.sendall(header)

        inicio = time.perf_counter()
        bytes_env = 0
        with open(arquivo, "rb") as f:
            while True:
                chunk = f.read(TAMANHO_CHUNK)
                if not chunk:
                    break
                conn.sendall(chunk)
                bytes_env += len(chunk)

        duracao    = time.perf_counter() - inicio
        throughput = (bytes_env * 8) / (duracao * 1_000_000) if duracao > 0 else 0
        log(f"  -> 200 OK | {caminho} | {bytes_env}B | {duracao:.4f}s | {throughput:.4f} Mbps")

    except Exception as e:
        log(f"Erro: {e}")
    finally:
        conn.close()

def iniciar():
    log(f"Servidor HTTP/TCP em {HOST_SERVIDOR}:{PORTA_HTTP}")
    log(f"WWW: {WWW_DIR} | Auth: {X_CUSTOM_AUTH[:16]}...")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST_SERVIDOR, PORTA_HTTP))
        s.listen(10)
        log("Aguardando conexoes...")
        while True:
            conn, addr = s.accept()
            servir(conn, addr)

if __name__ == "__main__":
    iniciar()
