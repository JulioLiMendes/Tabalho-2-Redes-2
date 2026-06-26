#!/usr/bin/env python3
# =============================================================
# run_testes_http.py — Testes automáticos com captura tcpdump
# Autor: JULIO CESAR DE LIMA MENDES | Matrícula: 20249006910
# Uso: python3 /app/scripts/run_testes_http.py [tcp|rudp|todos]
# =============================================================

import os, sys, time, signal, subprocess
from datetime import datetime

sys.path.insert(0, '/app')
from config import LOG_DIR

CENARIOS    = ["A", "B", "C"]
ARQUIVOS    = ["/arquivo_100kb.bin", "/arquivo_500kb.bin", "/arquivo_1mb.bin"]
DOMINIO     = "webserver.local"
N_EXEC      = 10
SETUP_TC    = "/app/scripts/setup_tc.sh"
CLI_TCP     = "/app/cliente/cliente_http_tcp.py"
CLI_RUDP    = "/app/cliente/cliente_http_rudp.py"
PCAP_DIR    = os.path.join(LOG_DIR, "pcap")
PAUSA_TCP   = 1.5
PAUSA_RUDP  = 2.0

os.makedirs(PCAP_DIR, exist_ok=True)

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] [ORQUESTRADOR] {msg}")

def aplicar_cenario(cenario):
    log(f"Aplicando Cenario {cenario}...")
    subprocess.run(["bash", SETUP_TC, cenario], capture_output=True)
    time.sleep(1)

def iniciar_captura(proto, cenario, arquivo):
    ts     = datetime.now().strftime("%Y%m%d_%H%M%S")
    aid    = arquivo.strip("/").replace(".", "_")
    nome   = f"{proto}_{cenario}_{aid}_{ts}.pcap"
    path   = os.path.join(PCAP_DIR, nome)
    filtro = "port 53 or port 80 or port 5001"
    proc   = subprocess.Popen(
        ["tcpdump", "-i", "eth0", "-w", path, "-n", filtro],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    time.sleep(0.5)
    log(f"  tcpdump iniciado: {nome}")
    return proc, path

def encerrar_captura(proc, path):
    proc.send_signal(signal.SIGINT)
    try:
        proc.wait(timeout=5)
    except Exception:
        proc.kill()
    time.sleep(0.3)
    if os.path.exists(path):
        log(f"  tcpdump encerrado: {os.path.basename(path)} ({os.path.getsize(path):,} bytes)")

def executar_lote(cli, proto, cenario, arquivo, pausa):
    log(f"\n=== {proto} | Cenario {cenario} | {arquivo} | {N_EXEC} execucoes ===")
    proc, path = iniciar_captura(proto.lower().replace("-",""), cenario, arquivo)
    for i in range(1, N_EXEC + 1):
        log(f"  Execucao {i}/{N_EXEC}")
        subprocess.run(["python3", cli, DOMINIO, arquivo, cenario, str(i)])
        time.sleep(pausa)
    encerrar_captura(proc, path)

def main():
    modo = sys.argv[1].lower() if len(sys.argv) > 1 else "todos"
    if modo not in ["tcp", "rudp", "todos"]:
        print("Uso: python3 run_testes_http.py [tcp|rudp|todos]")
        sys.exit(1)

    total = N_EXEC * len(CENARIOS) * len(ARQUIVOS) * (2 if modo == "todos" else 1)
    print("=" * 65)
    print(f"  TESTES HTTP | Modo: {modo.upper()} | Total: {total} requisicoes")
    print("  ATENCAO: Certifique-se que os servidores estao rodando!")
    print("=" * 65)

    for cenario in CENARIOS:
        aplicar_cenario(cenario)
        for arquivo in ARQUIVOS:
            if modo in ["tcp", "todos"]:
                executar_lote(CLI_TCP, "HTTP-TCP", cenario, arquivo, PAUSA_TCP)
            if modo in ["rudp", "todos"]:
                executar_lote(CLI_RUDP, "HTTP-RUDP", cenario, arquivo, PAUSA_RUDP)

    subprocess.run(["bash", SETUP_TC, "reset"], capture_output=True)
    print("\n" + "=" * 65)
    print("  TESTES CONCLUIDOS!")
    print(f"  CSVs em    : {LOG_DIR}/")
    print(f"  Capturas em: {PCAP_DIR}/")
    print("=" * 65)

if __name__ == "__main__":
    main()
