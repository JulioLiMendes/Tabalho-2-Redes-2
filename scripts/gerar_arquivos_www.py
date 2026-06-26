#!/usr/bin/env python3
import os
WWW_DIR = "/app/www"
os.makedirs(WWW_DIR, exist_ok=True)
for nome, tam in [("arquivo_100kb.bin", 100*1024),
                  ("arquivo_500kb.bin", 500*1024),
                  ("arquivo_1mb.bin", 1024*1024)]:
    p = os.path.join(WWW_DIR, nome)
    if not os.path.exists(p):
        print(f"Gerando {nome}...")
        with open(p, "wb") as f:
            f.write(os.urandom(tam))
    else:
        print(f"Ja existe: {nome}")
print("Concluido!")
