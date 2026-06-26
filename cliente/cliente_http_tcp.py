# =============================================================
# cliente_http_tcp.py — Cliente HTTP/1.1 sobre TCP com DNS
# Autor: JULIO CESAR DE LIMA MENDES | Matrícula: 20249006910
# Uso: python3 cliente_http_tcp.py <dominio> <caminho> <cenario> [execucao]
# =============================================================

import socket, os, sys, time, csv
from datetime import datetime

sys.path.insert(0, '/app')
sys.path.insert(0, '/app/dns')
from config import PORTA_HTTP, TAMANHO_CHUNK, LOG_DIR, X_CUSTOM_AUTH
from cliente_dns import resolver

os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "cliente_http_tcp.log")
CSV_FILE = os.path.join(LOG_DIR, "resultados_http_tcp.csv")

def log(msg):
    linha = f"[{datetime.now().strftime('%H:%M:%S.%f')}] [HTTP-TCP-CLI] {msg}"
    print(linha)
    with open(LOG_FILE, "a") as f:
        f.write(linha + "\n")

def salvar_csv(cenario, execucao, arquivo, dns_ms, dns_tent, dur, tput, nbytes, status, ok):
    novo = not os.path.exists(CSV_FILE)
    with open(CSV_FILE, "a", newline="") as f:
        w = csv.writer(f)
        if novo:
            w.writerow(["timestamp","protocolo","cenario","execucao","arquivo",
                        "dns_ms","dns_tentativas","duracao_s","throughput_mbps",
                        "bytes_recebidos","status_http","sucesso"])
        w.writerow([datetime.now().isoformat(),"HTTP-TCP",cenario,execucao,arquivo,
                    f"{dns_ms:.4f}",dns_tent,f"{dur:.6f}",f"{tput:.6f}",
                    nbytes,status,ok])

def get(dominio, caminho, cenario, execucao=1):
    log(f"=== Exec {execucao} | Cenario {cenario} | {caminho} ===")

    # 1) DNS
    ip, dns_ms, dns_tent = resolver(dominio)
    if not ip:
        log("ERRO: DNS falhou")
        salvar_csv(cenario, execucao, caminho, dns_ms, dns_tent, 0, 0, 0, 0, False)
        return

    log(f"DNS: {dominio} -> {ip} ({dns_ms:.2f}ms, {dns_tent} tent)")

    # 2) HTTP GET
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(60.0)
            s.connect((ip, PORTA_HTTP))
            req = (f"GET {caminho} HTTP/1.1\r\nHost: {ip}\r\n"
                   f"X-Custom-Auth: {X_CUSTOM_AUTH}\r\nConnection: close\r\n\r\n").encode()
            inicio = time.perf_counter()
            s.sendall(req)
            resp = b""
            while True:
                chunk = s.recv(TAMANHO_CHUNK)
                if not chunk:
                    break
                resp += chunk
            duracao = time.perf_counter() - inicio

        status = int(resp.split(b"\r\n")[0].split()[1]) if resp else 0
        sep    = resp.find(b"\r\n\r\n")
        corpo  = resp[sep+4:] if sep >= 0 else b""
        nbytes = len(corpo)
        tput   = (nbytes * 8) / (duracao * 1_000_000) if duracao > 0 else 0
        log(f"HTTP: {status} | {nbytes}B | {duracao:.4f}s | {tput:.4f} Mbps")
        log(f"Tempo total (DNS+HTTP): {dns_ms/1000+duracao:.4f}s")
        salvar_csv(cenario, execucao, caminho, dns_ms, dns_tent, duracao, tput, nbytes, status, status==200)

    except Exception as e:
        log(f"ERRO HTTP: {e}")
        salvar_csv(cenario, execucao, caminho, dns_ms, dns_tent, 0, 0, 0, 0, False)

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Uso: python3 cliente_http_tcp.py <dominio> <caminho> <cenario> [execucao]")
        sys.exit(1)
    get(sys.argv[1], sys.argv[2], sys.argv[3].upper(),
        int(sys.argv[4]) if len(sys.argv) > 4 else 1)
