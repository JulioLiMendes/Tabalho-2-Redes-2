# =============================================================
# cliente_dns.py — Cliente DNS simplificado
# Autor: JULIO CESAR DE LIMA MENDES | Matrícula: 20249006910
# =============================================================

import socket, struct, random, time, os, sys
from datetime import datetime

HOST_DNS       = "172.20.0.30"
PORTA_DNS      = 53
TIMEOUT_DNS    = 2.0
MAX_TENT_DNS   = 5
LOG_FILE       = "/app/logs/cliente_dns.log"
os.makedirs("/app/logs", exist_ok=True)

def log(msg):
    linha = f"[{datetime.now().strftime('%H:%M:%S.%f')}] [DNS-CLIENTE] {msg}"
    print(linha)
    with open(LOG_FILE, "a") as f:
        f.write(linha + "\n")

def resolver(nome):
    dns_id   = random.randint(1, 65535)
    nome_enc = nome.encode()
    query    = struct.pack("!H H B", dns_id, 0x0000, len(nome_enc)) + nome_enc

    inicio = time.perf_counter()
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.settimeout(TIMEOUT_DNS)
        for t in range(1, MAX_TENT_DNS + 1):
            s.sendto(query, (HOST_DNS, PORTA_DNS))
            log(f"  Query enviada | ID={dns_id} | tentativa {t}/{MAX_TENT_DNS}")
            try:
                raw, _ = s.recvfrom(512)
                fim = time.perf_counter()
                tempo_ms = (fim - inicio) * 1000

                dns_id_r, flags, nome_len = struct.unpack("!H H B", raw[:5])
                if dns_id_r != dns_id:
                    continue
                nome_r = raw[5:5+nome_len].decode(errors="ignore")
                if flags == 0x8003:
                    log(f"  NXDOMAIN: '{nome}' ({tempo_ms:.2f}ms)")
                    return None, tempo_ms, t
                ip = socket.inet_ntoa(raw[5+nome_len:5+nome_len+4])
                log(f"  Resolvido: '{nome}' -> {ip} ({tempo_ms:.2f}ms, {t} tentativa(s))")
                return ip, tempo_ms, t
            except socket.timeout:
                log(f"  Timeout na tentativa {t}/{MAX_TENT_DNS}")

    fim = time.perf_counter()
    return None, (fim - inicio)*1000, MAX_TENT_DNS

if __name__ == "__main__":
    nome = sys.argv[1] if len(sys.argv) > 1 else "webserver.local"
    ip, ms, t = resolver(nome)
    print(f"\nResultado: {nome} -> {ip} ({ms:.2f}ms)")
