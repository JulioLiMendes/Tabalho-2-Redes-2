# =============================================================
# servidor_dns.py — Servidor DNS local simplificado
# Autor: JULIO CESAR DE LIMA MENDES | Matrícula: 20249006910
# =============================================================

import socket, struct, os, sys
from datetime import datetime

HOST_DNS  = "172.20.0.30"
PORTA_DNS = 53
ZONA_FILE = "/app/dns/hosts.txt"
LOG_FILE  = "/app/logs/servidor_dns.log"
os.makedirs("/app/logs", exist_ok=True)

def log(msg):
    linha = f"[{datetime.now().strftime('%H:%M:%S.%f')}] [DNS] {msg}"
    print(linha)
    with open(LOG_FILE, "a") as f:
        f.write(linha + "\n")

def carregar_zona():
    zona = {}
    with open(ZONA_FILE) as f:
        for linha in f:
            linha = linha.strip()
            if not linha or linha.startswith("#"):
                continue
            partes = linha.split()
            if len(partes) >= 2:
                zona[partes[0].lower()] = partes[1]
    log(f"Zona carregada: {len(zona)} registros")
    return zona

def montar_resposta(dns_id, nome, ip):
    nome_enc = nome.encode()
    ip_bytes = socket.inet_aton(ip)
    return struct.pack("!H H B", dns_id, 0x8000, len(nome_enc)) + nome_enc + ip_bytes

def montar_nxdomain(dns_id, nome):
    nome_enc = nome.encode()
    return struct.pack("!H H B", dns_id, 0x8003, len(nome_enc)) + nome_enc

def desmontar_query(raw):
    dns_id, flags, nome_len = struct.unpack("!H H B", raw[:5])
    nome = raw[5:5+nome_len].decode(errors="ignore")
    return dns_id, nome

def iniciar():
    zona = carregar_zona()
    log(f"Servidor DNS em {HOST_DNS}:{PORTA_DNS}")
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.bind((HOST_DNS, PORTA_DNS))
        log("Aguardando consultas...")
        while True:
            try:
                raw, addr = s.recvfrom(512)
                dns_id, nome = desmontar_query(raw)
                nome_lower = nome.lower()
                log(f"Query de {addr}: '{nome_lower}'")
                if nome_lower in zona:
                    ip = zona[nome_lower]
                    s.sendto(montar_resposta(dns_id, nome_lower, ip), addr)
                    log(f"  -> {nome_lower} = {ip}")
                else:
                    s.sendto(montar_nxdomain(dns_id, nome_lower), addr)
                    log(f"  -> NXDOMAIN")
            except Exception as e:
                log(f"Erro: {e}")

if __name__ == "__main__":
    iniciar()
