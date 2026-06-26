# Redes de Computadores II — HTTP/1.1 sobre TCP e R-UDP com DNS Local

**Aluno:** Julio Cesar de Lima Mendes
**Matricula:** 20249006910
**X-Custom-Auth (SHA-256):** `2f93fca4ad0be3570264caaf2010c07833a9889bd61b857b9681fd465d2fcf15`

---

## Estrutura do Projeto

```
redes2_v2/
├── Dockerfile
├── docker-compose.yml
├── config.py
├── protocolo_rudp.py
├── dns/
│   ├── hosts.txt           # Arquivo de zona DNS
│   ├── servidor_dns.py     # Servidor DNS UDP porta 53
│   └── cliente_dns.py      # Cliente DNS com retransmissao
├── servidor/
│   ├── servidor_http_tcp.py   # HTTP/1.1 sobre TCP (porta 80)
│   └── servidor_http_rudp.py  # HTTP/1.1 sobre R-UDP (porta 5001)
├── cliente/
│   ├── cliente_http_tcp.py    # Cliente HTTP TCP com DNS
│   └── cliente_http_rudp.py   # Cliente HTTP R-UDP com DNS
├── scripts/
│   ├── setup_tc.sh            # Aplica cenarios de rede
│   ├── gerar_arquivos_www.py  # Gera arquivos de teste
│   └── run_testes_http.py     # Testes automaticos + tcpdump
├── analise/
│   └── gerar_graficos.py      # Graficos Pandas/Matplotlib
├── www/
│   ├── index.html
│   ├── arquivo_100kb.bin  (gerado)
│   ├── arquivo_500kb.bin    (gerado)
│   └── arquivo_1mb.bin   (gerado)
└── logs/                  (gerado automaticamente)
```

---

## Fluxo do Protocolo

```
CLIENTE                  DNS (172.20.0.30)      SERVIDOR (172.20.0.10)
   |--- DNS Query ------->|                              |
   |<-- DNS Response -----|                              |
   |--- HTTP GET (TCP ou R-UDP) ------------------------>|
   |<-- HTTP 200 OK + arquivo ---------------------------|
```

---

## Cenarios de Rede

| Cenario | Perda | Delay | Descricao        |
|---------|-------|-------|------------------|
| A       | 0%    | 10ms  | Rede ideal       |
| B       | 5%    | 50ms  | Rede degradada   |
| C       | 10%   | 100ms | Alta perda       |

---

## Como Executar

### 1. Subir os containers
```powershell
docker-compose up -d --build
```

### 2. Gerar arquivos de teste
```bash
docker exec -it redes2_servidor bash
python3 /app/scripts/gerar_arquivos_www.py
```

### 3. Iniciar servidores (terminais separados)
```bash
# Terminal 1 - HTTP TCP
docker exec -it redes2_servidor bash
python3 /app/servidor/servidor_http_tcp.py

# Terminal 2 - HTTP R-UDP
docker exec -it redes2_servidor bash
python3 /app/servidor/servidor_http_rudp.py
```

### 4. Rodar testes completos
```bash
docker exec -it redes2_cliente bash
python3 /app/scripts/run_testes_http.py todos
```

### 5. Gerar graficos
```bash
python3 /app/analise/gerar_graficos.py
```

### 6. Copiar resultados
```powershell
docker cp redes2_cliente:/app/logs "C:\caminho\destino\logs"
```
