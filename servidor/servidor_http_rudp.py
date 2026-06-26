# =============================================================
# servidor_http_rudp.py — HTTP/1.1 sobre R-UDP (Stop-and-Wait)
# Autor: JULIO CESAR DE LIMA MENDES | Matrícula: 20249006910
# =============================================================

import socket, os, sys, time
from datetime import datetime

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
APP_ROOT = "/app" if os.path.exists("/app") else PROJECT_ROOT
sys.path.insert(0, APP_ROOT)
from config import HOST_SERVIDOR, PORTA_UDP, X_CUSTOM_AUTH, TAMANHO_CHUNK, LOG_DIR, WWW_DIR

if APP_ROOT != "/app":
    LOG_DIR = os.path.join(PROJECT_ROOT, "logs")
    WWW_DIR = os.path.join(PROJECT_ROOT, "www")
from protocolo_rudp import (
    desmontar_pacote, montar_ack, montar_nack, montar_synack, montar_pacote,
    TIPO_DATA, TIPO_SYN, TIPO_FIN, TIPO_ACK, TAMANHO_CABECALHO
)

os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE    = os.path.join(LOG_DIR, "servidor_http_rudp.log")
BUFFER_SIZE = TAMANHO_CHUNK + TAMANHO_CABECALHO + 64
MAX_TENT    = 10
TIMEOUT_ACK = 3.0

TIPOS_MIME = {
    ".html": "text/html; charset=utf-8",
    ".bin" : "application/octet-stream",
    ".txt" : "text/plain; charset=utf-8",
}

def log(msg):
    linha = f"[{datetime.now().strftime('%H:%M:%S.%f')}] [HTTP-RUDP-SRV] {msg}"
    print(linha)
    with open(LOG_FILE, "a") as f:
        f.write(linha + "\n")

def get_mime(caminho):
    return TIPOS_MIME.get(os.path.splitext(caminho)[1].lower(), "application/octet-stream")

def receber_pkt(sock, addr_cliente, timeout=5.0):
    sock.settimeout(timeout)
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            raw, raddr = sock.recvfrom(BUFFER_SIZE)
            if raddr == addr_cliente:
                return desmontar_pacote(raw)
        except socket.timeout:
            return None
        except Exception:
            return None
    return None

def receber_stream(sock, addr) -> bytes:
    dados   = b""
    seq_esp = 1
    while True:
        pkt = receber_pkt(sock, addr, timeout=10.0)
        if pkt is None:
            log("  Timeout aguardando DATA")
            break
        if pkt["tipo"] == TIPO_FIN:
            sock.sendto(montar_ack(pkt["seq_num"], X_CUSTOM_AUTH), addr)
            break
        if pkt["tipo"] == TIPO_DATA:
            if not pkt["integro"]:
                sock.sendto(montar_nack(pkt["seq_num"], X_CUSTOM_AUTH), addr)
                continue
            if pkt["seq_num"] < seq_esp:
                sock.sendto(montar_ack(pkt["seq_num"], X_CUSTOM_AUTH), addr)
                continue
            if pkt["seq_num"] == seq_esp:
                dados   += pkt["payload"]
                seq_esp += 1
                sock.sendto(montar_ack(pkt["seq_num"], X_CUSTOM_AUTH), addr)
                if b"\r\n\r\n" in dados:
                    break
    return dados

def enviar_stream(sock, addr, dados: bytes, seq_ini: int) -> tuple[int, bool]:
    seq = seq_ini
    offset = 0
    while offset < len(dados):
        chunk = dados[offset:offset + TAMANHO_CHUNK]
        pkt   = montar_pacote(TIPO_DATA, seq, X_CUSTOM_AUTH, chunk)
        ok    = False
        
        for t in range(MAX_TENT):
            sock.sendto(pkt, addr)
            
            # Criamos um sub-loop com base no tempo para ignorar lixo no buffer
            deadline = time.time() + TIMEOUT_ACK
            while time.time() < deadline:
                tempo_restante = deadline - time.time()
                if tempo_restante <= 0:
                    break
                
                resp = receber_pkt(sock, addr, timeout=tempo_restante)
                if resp is None:
                    # Deu timeout real (nenhum pacote chegou no tempo)
                    break
                
                # SE chegou o ACK que queríamos, sucesso!
                if resp["tipo"] == TIPO_ACK and resp["seq_num"] == seq:
                    ok = True
                    break
                
                # Se chegou qualquer outra coisa (ex: GET repetido), o 'while' continua
                # lendo o buffer até esvaziar ou dar o tempo do timeout.
            
            if ok:
                break
            else:
                log(f"  Timeout/Invalido seq={seq} tent {t+1}/{MAX_TENT}")
                
        if not ok:
            log(f"  FALHA seq={seq}")
            return seq, False
            
        offset += len(chunk)
        seq    += 1
        
    return seq, True

def enviar_fin(sock, addr, seq: int) -> bool:
    fin = montar_pacote(TIPO_FIN, seq, X_CUSTOM_AUTH)
    for _ in range(MAX_TENT):
        sock.sendto(fin, addr)
        resp = receber_pkt(sock, addr, timeout=TIMEOUT_ACK)
        if resp and resp["tipo"] == TIPO_ACK and resp["seq_num"] == seq:
            return True
    return False

def servir_sessao(sock, addr, request_raw: bytes):
    try:
        linha_req = request_raw.decode(errors="ignore").split("\r\n")[0].split()
        if len(linha_req) < 2 or linha_req[0] != "GET":
            return
        caminho = linha_req[1]
        if caminho == "/":
            caminho = "/index.html"
        log(f"{addr} | GET {caminho}")
        arquivo = os.path.join(WWW_DIR, caminho.lstrip("/"))

        if not os.path.isfile(arquivo):
            corpo  = b"<html><body><h1>404 Not Found</h1></body></html>"
            header = (f"HTTP/1.1 404 Not Found\r\nContent-Type: text/html\r\n"
                      f"Content-Length: {len(corpo)}\r\nX-Custom-Auth: {X_CUSTOM_AUTH}\r\n"
                      f"Connection: close\r\n\r\n").encode()
            seq, ok = enviar_stream(sock, addr, header + corpo, 1)
            if ok:
                enviar_fin(sock, addr, seq)
            return

        tamanho = os.path.getsize(arquivo)
        header  = (f"HTTP/1.1 200 OK\r\nContent-Type: {get_mime(arquivo)}\r\n"
                   f"Content-Length: {tamanho}\r\nX-Custom-Auth: {X_CUSTOM_AUTH}\r\n"
                   f"Connection: close\r\n\r\n").encode()

        inicio = time.perf_counter()
        
        # 1. Envia o Header HTTP usando a função enviar_stream
        seq, ok = enviar_stream(sock, addr, header, 1)
        if not ok:
            log("  Falha ao enviar header")
            return

        # 2. Abre e lê o arquivo de uma vez só
        try:
            with open(arquivo, "rb") as f:
                conteudo_arquivo = f.read()
        except Exception as e:
            log(f"  Erro ao ler arquivo: {e}")
            return

        # 3. Envia todo o conteúdo do arquivo usando enviar_stream (ela cuida dos pacotes e sequências)
        seq, ok_corpo = enviar_stream(sock, addr, conteudo_arquivo, seq)
        if not ok_corpo:
            log(f"  Falha corpo seq={seq}")
            return

        bytes_env = len(conteudo_arquivo)
        duracao    = time.perf_counter() - inicio
        throughput = (bytes_env * 8) / (duracao * 1_000_000) if duracao > 0 else 0
        log(f"  -> 200 OK | {caminho} | {bytes_env}B | {duracao:.4f}s | {throughput:.4f} Mbps")

        # 4. Envia o sinalizador de término
        enviar_fin(sock, addr, seq)

    except Exception as e:
        log(f"Erro servindo {addr}: {e}")

def iniciar():
    log(f"Servidor HTTP/R-UDP em {HOST_SERVIDOR}:{PORTA_UDP}")
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.bind((HOST_SERVIDOR, PORTA_UDP))
        sock.settimeout(60)
        log("Aguardando SYN...")
        while True:
            try:
                raw, addr = sock.recvfrom(BUFFER_SIZE)
            except socket.timeout:
                continue
            try:
                pkt = desmontar_pacote(raw)
            except Exception:
                continue
            if pkt["tipo"] == TIPO_SYN:
                log(f"SYN de {addr}")
                sock.sendto(montar_synack(X_CUSTOM_AUTH), addr)
                log(f"  -> SYN-ACK para {addr}")
                request_raw = receber_stream(sock, addr)
                if request_raw:
                    servir_sessao(sock, addr, request_raw)
                log("Sessao encerrada\n")

if __name__ == "__main__":
    iniciar()
