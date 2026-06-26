# Redes de Computadores II — Requisições HTTP/1.1 sobre TCP e R-UDP com DNS Local

**Disciplina:** Redes de Computadores II  
**Instituição:** Universidade Federal do Piauí — Campus Senador Helvídio Nunes de Barros  
**Curso:** Bacharelado em Sistemas de Informação  
**Aluno:** Julio Cesar de Lima Mendes  
**Matrícula:** 20249006910  
**X-Custom-Auth (SHA-256):** `2f93fca4ad0be3570264caaf2010c07833a9889bd61b857b9681fd465d2fcf15`

---

## Sobre o projeto

Este repositório implementa um ambiente de laboratório para comparar o desempenho do protocolo HTTP/1.1 quando utilizado sobre duas camadas de transporte diferentes:

- **HTTP sobre TCP**: uso direto de sockets TCP para transferência de arquivos.
- **HTTP sobre R-UDP**: comunicação HTTP encapsulada sobre uma camada de confiabilidade manual implementada no protocolo R-UDP.

Além disso, o projeto inclui um **servidor DNS local** para resolução de nomes e uma automação completa com **Docker**, **tc/netem** e **tcpdump** para simular cenários de rede com perda e atraso.

---

## Arquivos importantes

- **Relatório completo:** [Relatório Trabalho 2.pdf](Relatório%20Trabalho%202.pdf)
- **Link adicional:** [link.txt](link.txt)
- **Repositório GitHub:** https://github.com/JulioLiMendes/Tabalho-2-Redes-2

---

## Estrutura do repositório

```text
redes2_v2/
├── Dockerfile
├── docker-compose.yml
├── config.py
├── protocolo_rudp.py
├── link.txt
├── Relatório Trabalho 2.pdf
├── dns/
│   ├── hosts.txt
│   ├── servidor_dns.py
│   └── cliente_dns.py
├── cliente/
│   ├── cliente_http_tcp.py
│   └── cliente_http_rudp.py
├── servidor/
│   ├── servidor_http_tcp.py
│   └── servidor_http_rudp.py
├── scripts/
│   ├── setup_tc.sh
│   ├── gerar_arquivos_www.py
│   └── run_testes_http.py
├── analise/
│   └── gerar_graficos.py
├── www/
│   ├── index.html
│   ├── arquivo_100kb.bin
│   ├── arquivo_500kb.bin
│   └── arquivo_1mb.bin
└── logs/
```

---

## Fluxo do protocolo

O fluxo abaixo representa uma requisição completa, iniciando com a resolução DNS e seguindo para a transferência do arquivo via HTTP:

```text
CLIENTE                      DNS (172.20.0.30)          SERVIDOR (172.20.0.10)
   |                                 |                             |
   |--- 1. DNS Query --------------->|                             |
   |<-- 2. DNS Response ------------|                             |
   |                                                               |
   |--- 3. HTTP GET (TCP ou R-UDP) ------------------------------->|
   |<-- 4. HTTP 200 OK + Arquivo Binário ------------------------->|
```

---

## Cenários de rede

| Cenário | Perda | Delay | Descrição |
|---------|-------|-------|-----------|
| A       | 0%    | 10ms  | Rede ideal |
| B       | 5%    | 50ms  | Rede degradada |
| C       | 10%   | 100ms | Alta perda |

---

## Como executar

### 1. Subir os containers
```powershell
docker-compose up -d --build
```

### 2. Gerar arquivos de teste
```bash
docker exec -it redes2_servidor bash
python3 /app/scripts/gerar_arquivos_www.py
```

### 3. Iniciar os servidores (terminais separados)
```bash
# Terminal 1 - HTTP sobre TCP
docker exec -it redes2_servidor bash
python3 /app/servidor/servidor_http_tcp.py

# Terminal 2 - HTTP sobre R-UDP
docker exec -it redes2_servidor bash
python3 /app/servidor/servidor_http_rudp.py
```

### 4. Rodar os testes completos
```bash
docker exec -it redes2_cliente bash
python3 /app/scripts/run_testes_http.py todos
```

### 5. Gerar os gráficos
```bash
python3 /app/analise/gerar_graficos.py
```

### 6. Copiar os resultados locais
```powershell
docker cp redes2_cliente:/app/logs "C:\caminho\destino\logs"
```

### Aplicar cenário manualmente
```bash
docker exec -it redes2_cliente bash

bash /app/scripts/setup_tc.sh A
bash /app/scripts/setup_tc.sh B
bash /app/scripts/setup_tc.sh C
bash /app/scripts/setup_tc.sh reset
```

---

## Resultados esperados

O projeto gera:

- arquivos CSV com métricas de tempo, throughput e falhas;
- capturas de tráfego em formato PCAP;
- gráficos comparativos entre TCP e R-UDP;
- logs detalhados dos servidores, clientes e DNS.

---

## Referências

- KUROSE, J. F.; ROSS, K. W. Redes de Computadores e a Internet. 8. ed. Pearson, 2021.
- TANENBAUM, A. S.; WETHERALL, D. Redes de Computadores. 5. ed. Pearson, 2011.
- FIELDING, R. et al. Hypertext Transfer Protocol — HTTP/1.1. RFC 2616, IETF, 1999.
- MOCKAPETRIS, P. Domain Names — Concepts and Facilities. RFC 1034, IETF, 1987.
- POSTEL, J. Transmission Control Protocol. RFC 793, IETF, 1981.
- POSTEL, J. User Datagram Protocol. RFC 768, IETF, 1980.
- PYTHON SOFTWARE FOUNDATION. Socket — Low-level networking interface. Disponível em: https://docs.python.org/3/library/socket.html
- THE PANDAS DEVELOPMENT TEAM. Pandas: powerful Python data analysis toolkit. Disponível em: https://pandas.pydata.org
- HUNTER, J. D. Matplotlib: A 2D graphics environment. Computing in Science & Engineering, v. 9, n. 3, p. 90-95, 2007.
- DOCKER DOCUMENTATION. Docker Compose Overview. Disponível em: https://docs.docker.com
- KERNEL.ORG. tc-netem: Network Emulator Linux Man Page. Disponível em: https://man7.org/linux/man-pages/man8/tc-netem.8.html