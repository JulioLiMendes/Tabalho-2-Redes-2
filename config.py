# =============================================================
# config.py — Configurações globais do projeto v2
# Autor: JULIO CESAR DE LIMA MENDES | Matrícula: 20249006910
# =============================================================

import hashlib

# ── Identificação ────────────────────────────────────────────
MATRICULA = "20249006910"
NOME      = "JULIO CESAR DE LIMA MENDES"

X_CUSTOM_AUTH = hashlib.sha256(
    (MATRICULA + NOME).encode()
).hexdigest()

# ── Rede ─────────────────────────────────────────────────────
HOST_SERVIDOR = "172.20.0.10"
HOST_DNS      = "172.20.0.30"
HOST_CLIENTE  = "172.20.0.20"

PORTA_TCP     = 5000
PORTA_UDP     = 5001
PORTA_HTTP    = 80
PORTA_DNS     = 53

# ── Domínio ───────────────────────────────────────────────────
DOMINIO_WEB   = "webserver.local"

# ── Transferência ─────────────────────────────────────────────
TAMANHO_CHUNK  = 4096
TIMEOUT_RUDP   = 2.0
MAX_TENTATIVAS = 10

# ── DNS ───────────────────────────────────────────────────────
TIMEOUT_DNS        = 2.0
MAX_TENTATIVAS_DNS = 5

# ── Paths ─────────────────────────────────────────────────────
LOG_DIR = "/app/logs"
WWW_DIR = "/app/www"
