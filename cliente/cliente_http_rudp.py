# =============================================================
# cliente_http_rudp.py — Cliente HTTP/1.1 sobre R-UDP com DNS
# Autor: JULIO CESAR DE LIMA MENDES | Matrícula: 20249006910
# Uso: python3 cliente_http_rudp.py <dominio> <caminho> <cenario> [execucao]
# =============================================================

import socket, os, sys, time, csv, json
from datetime import datetime

sys.path.insert(0, '/app')
sys.path.insert(0, '/app/dns')
from config import (PORTA_UDP, TAMANHO_CHUNK, LOG_DIR, X_CUSTOM_AUTH,
                    TIMEOUT_RUDP, MAX_TENTATIVAS)
from cliente_dns import resolver
from protocolo_rudp import (
    montar_pacote, montar_syn, montar_fin, desmontar_pacote,
    TIPO_ACK, TIPO_NACK, TIPO_SYNACK, TIPO_DATA, TIPO_FIN,
    TAMANHO_CABECALHO, nome_tipo
)

os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE    = os.path.join(LOG_DIR, "cliente_http_rudp.log")
CSV_FILE    = os.path.join(LOG_DIR, "resultados_http_rudp.csv")
BUFFER_SIZE = TAMANHO_CHUNK + TAMANHO_CABECALHO + 64
MAX_TENT    = MAX_TENTATIVAS
TIMEOUT_ACK = 3.0

def log(msg):
    linha = f"[{datetime.now().strftime('%H:%M:%S.%f')}] [HTTP-RUDP-CLI] {msg}"
    print(linha)
    with open(LOG_FILE, "a") as f:
        f.write(linha + "\n")

def salvar_csv(cenario, execucao, arquivo, dns_ms, dns_tent,
               dur, tput, nbytes, status, retrans, ok):
    novo = not os.path.exists(CSV_FILE)
    with open(CSV_FILE, "a", newline="") as f:
        w = csv.writer(f)
        if novo:
            w.writerow(["timestamp","protocolo","cenario","execucao","arquivo",
                        "dns_ms","dns_tentativas","duracao_s","throughput_mbps",
                        "bytes_recebidos","status_http","retransmissoes","sucesso"])
        w.writerow([datetime.now().isoformat(),"HTTP-RUDP",cenario,execucao,arquivo,
                    f"{dns_ms:.4f}",dns_tent,f"{dur:.6f}",f"{tput:.6f}",
                    nbytes,status,retrans,ok])

def receber_pkt(sock, addr, timeout=3.0):
    """Recebe próximo pacote do addr, ignorando outros."""
    sock.settimeout(timeout)
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            raw, raddr = sock.recvfrom(BUFFER_SIZE)
            if raddr == addr:
                return desmontar_pacote(raw)
        except socket.timeout:
            return None
        except Exception:
            return None
    return None

def enviar_com_retry(sock, pkt, tipo_esp, seq, addr):
    """Stop-and-Wait: envia e aguarda ACK. Retorna (ok, retrans)."""
    retrans = 0
    for t in range(1, MAX_TENT + 1):
        sock.sendto(pkt, addr)
        if t > 1:
            retrans += 1
            log(f"  Retransmissao seq={seq} tent {t}/{MAX_TENT}")
        resp = receber_pkt(sock, addr, timeout=TIMEOUT_ACK)
        if resp is None:
            log(f"  Timeout seq={seq} tent {t}/{MAX_TENT}")
            continue
        if resp["tipo"] == tipo_esp and resp["seq_num"] == seq:
            return True, retrans
        if resp["tipo"] == TIPO_NACK and resp["seq_num"] == seq:
            continue
    return False, retrans

def get(dominio, caminho, cenario, execucao=1):
    log(f"=== Exec {execucao} | Cenario {cenario} | {caminho} ===")

    # 1) DNS
    ip, dns_ms, dns_tent = resolver(dominio)
    if not ip:
        log("ERRO: DNS falhou")
        salvar_csv(cenario, execucao, caminho, dns_ms, dns_tent, 0, 0, 0, 0, 0, False)
        return

    log(f"DNS: {dominio} -> {ip} ({dns_ms:.2f}ms, {dns_tent} tent)")
    addr = (ip, PORTA_UDP)

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:

        # 2) Handshake SYN
        meta    = json.dumps({"tipo": "HTTP-GET", "caminho": caminho}).encode()
        syn     = montar_syn(X_CUSTOM_AUTH, meta)
        synack_ok = False
        for t in range(1, MAX_TENT + 1):
            sock.sendto(syn, addr)
            resp = receber_pkt(sock, addr, timeout=TIMEOUT_ACK)
            if resp and resp["tipo"] == TIPO_SYNACK:
                log(f"  SYN-ACK recebido na tentativa {t}")
                synack_ok = True
                break
            log(f"  SYN timeout tentativa {t}/{MAX_TENT}")

        if not synack_ok:
            log("ERRO: Sem SYN-ACK")
            salvar_csv(cenario, execucao, caminho, dns_ms, dns_tent, 0, 0, 0, 0, 0, False)
            return

        # 3) Envia request HTTP via DATA
        request = (f"GET {caminho} HTTP/1.1\r\nHost: {ip}\r\n"
                   f"X-Custom-Auth: {X_CUSTOM_AUTH}\r\nConnection: close\r\n\r\n").encode()

        seq        = 1
        retrans    = 0
        inicio     = time.perf_counter()
        offset     = 0

        while offset < len(request):
            chunk = request[offset:offset + TAMANHO_CHUNK]
            pkt   = montar_pacote(TIPO_DATA, seq, X_CUSTOM_AUTH, chunk)
            ok, rt = enviar_com_retry(sock, pkt, TIPO_ACK, seq, addr)
            retrans += rt
            if not ok:
                log(f"ERRO: request seq={seq} falhou")
                salvar_csv(cenario, execucao, caminho, dns_ms, dns_tent, 0, 0, 0, 0, retrans, False)
                return
            offset += len(chunk)
            seq    += 1

        # FIN do request
        fin    = montar_fin(seq, X_CUSTOM_AUTH)
        ok, rt = enviar_com_retry(sock, fin, TIPO_ACK, seq, addr)
        retrans += rt
        seq += 1

        # 4) Recebe resposta HTTP via DATA
        resposta     = b""
        seq_esp      = 1
        sock.settimeout(15.0)

        while True:
            resp = receber_pkt(sock, addr, timeout=15.0)
            if resp is None:
                log("  Timeout aguardando resposta")
                break
            if resp["tipo"] == TIPO_FIN:
                sock.sendto(montar_pacote(TIPO_ACK, resp["seq_num"], X_CUSTOM_AUTH), addr)
                break
            if resp["tipo"] == TIPO_DATA:
                if not resp["integro"]:
                    sock.sendto(montar_pacote(TIPO_NACK, resp["seq_num"], X_CUSTOM_AUTH), addr)
                    retrans += 1
                    continue
                if resp["seq_num"] < seq_esp:
                    sock.sendto(montar_pacote(TIPO_ACK, resp["seq_num"], X_CUSTOM_AUTH), addr)
                    continue
                if resp["seq_num"] == seq_esp:
                    resposta += resp["payload"]
                    seq_esp  += 1
                    sock.sendto(montar_pacote(TIPO_ACK, resp["seq_num"], X_CUSTOM_AUTH), addr)

        duracao = time.perf_counter() - inicio

    # Extrai status e corpo
    try:
        status = int(resposta.split(b"\r\n")[0].split()[1])
    except Exception:
        status = 0
    sep   = resposta.find(b"\r\n\r\n")
    corpo = resposta[sep+4:] if sep >= 0 else b""
    nbytes = len(corpo)
    tput   = (nbytes * 8) / (duracao * 1_000_000) if duracao > 0 else 0

    log(f"HTTP: {status} | {nbytes}B | {duracao:.4f}s | {tput:.4f} Mbps | retrans={retrans}")
    log(f"Tempo total (DNS+HTTP): {dns_ms/1000+duracao:.4f}s")
    salvar_csv(cenario, execucao, caminho, dns_ms, dns_tent,
               duracao, tput, nbytes, status, retrans, status==200)

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Uso: python3 cliente_http_rudp.py <dominio> <caminho> <cenario> [execucao]")
        sys.exit(1)
    get(sys.argv[1], sys.argv[2], sys.argv[3].upper(),
        int(sys.argv[4]) if len(sys.argv) > 4 else 1)
