#!/usr/bin/env python3
# =============================================================
# gerar_graficos.py — Análise estatística HTTP TCP vs R-UDP
# Autor: JULIO CESAR DE LIMA MENDES | Matrícula: 20249006910
# =============================================================

import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import os

LOG_DIR  = '/app/logs'
GRAFICOS = '/app/logs/graficos'
os.makedirs(GRAFICOS, exist_ok=True)

CENARIOS = ['A', 'B', 'C']
ARQUIVOS = ['arquivo_100kb.bin', 'arquivo_500kb.bin', 'arquivo_1mb.bin']
DESC_CEN = {
    'A': 'Cenario A\n(0% perda/10ms)',
    'B': 'Cenario B\n(5% perda/50ms)',
    'C': 'Cenario C\n(10% perda/100ms)'
}
COR_TCP  = '#2196F3'
COR_RUDP = '#F44336'

def carregar():
    tcp  = pd.read_csv(f'{LOG_DIR}/resultados_http_tcp.csv')
    rudp = pd.read_csv(f'{LOG_DIR}/resultados_http_rudp.csv')
    for df in [tcp, rudp]:
        df['throughput_mbps'] = pd.to_numeric(df['throughput_mbps'], errors='coerce')
        df['duracao_s']       = pd.to_numeric(df['duracao_s'], errors='coerce')
        df['dns_ms']          = pd.to_numeric(df['dns_ms'], errors='coerce')
    tcp  = tcp.dropna(subset=['throughput_mbps'])
    rudp = rudp.dropna(subset=['throughput_mbps'])
    return tcp, rudp

def grafico_throughput_por_arquivo(tcp, rudp):
    fig, axes = plt.subplots(1, 3, figsize=(15, 6))
    fig.suptitle('Throughput Medio por Arquivo e Cenario: HTTP-TCP vs HTTP-R-UDP',
                 fontweight='bold', fontsize=13)
    for i, cenario in enumerate(CENARIOS):
        ax = axes[i]
        x  = np.arange(len(ARQUIVOS))
        w  = 0.35
        labels = ['100KB', '500KB', '1MB']
        m_tcp  = [tcp[(tcp['cenario']==cenario) & (tcp['arquivo'].str.contains(a))]['throughput_mbps'].mean() for a in ARQUIVOS]
        m_rudp = [rudp[(rudp['cenario']==cenario) & (rudp['arquivo'].str.contains(a))]['throughput_mbps'].mean() for a in ARQUIVOS]
        s_tcp  = [tcp[(tcp['cenario']==cenario) & (tcp['arquivo'].str.contains(a))]['throughput_mbps'].std() for a in ARQUIVOS]
        s_rudp = [rudp[(rudp['cenario']==cenario) & (rudp['arquivo'].str.contains(a))]['throughput_mbps'].std() for a in ARQUIVOS]
        ax.bar(x-w/2, m_tcp,  w, yerr=s_tcp,  capsize=5, color=COR_TCP,  alpha=0.85, label='HTTP-TCP')
        ax.bar(x+w/2, m_rudp, w, yerr=s_rudp, capsize=5, color=COR_RUDP, alpha=0.85, label='HTTP-R-UDP')
        ax.set_title(DESC_CEN[cenario], fontsize=10)
        ax.set_xticks(x); ax.set_xticklabels(labels)
        ax.set_ylabel('Throughput (Mbps)' if i==0 else '')
        ax.legend(fontsize=8); ax.grid(axis='y', linestyle='--', alpha=0.5); ax.set_ylim(bottom=0)
    plt.tight_layout()
    plt.savefig(f'{GRAFICOS}/01_throughput_por_arquivo.png', dpi=150); plt.close()
    print('[OK] 01_throughput_por_arquivo.png')

def grafico_dns_tempo(tcp, rudp):
    fig, ax = plt.subplots(figsize=(10, 6))
    x = np.arange(len(CENARIOS)); w = 0.35
    m_tcp  = [tcp[tcp['cenario']==c]['dns_ms'].mean()  for c in CENARIOS]
    m_rudp = [rudp[rudp['cenario']==c]['dns_ms'].mean() for c in CENARIOS]
    s_tcp  = [tcp[tcp['cenario']==c]['dns_ms'].std()   for c in CENARIOS]
    s_rudp = [rudp[rudp['cenario']==c]['dns_ms'].std()  for c in CENARIOS]
    ax.bar(x-w/2, m_tcp,  w, yerr=s_tcp,  capsize=5, color=COR_TCP,  alpha=0.85, label='HTTP-TCP')
    ax.bar(x+w/2, m_rudp, w, yerr=s_rudp, capsize=5, color=COR_RUDP, alpha=0.85, label='HTTP-R-UDP')
    ax.set_xticks(x); ax.set_xticklabels([DESC_CEN[c] for c in CENARIOS])
    ax.set_ylabel('Tempo DNS (ms)')
    ax.set_title('Tempo de Resolucao DNS por Cenario', fontweight='bold')
    ax.legend(); ax.grid(axis='y', linestyle='--', alpha=0.5); ax.set_ylim(bottom=0)
    plt.tight_layout()
    plt.savefig(f'{GRAFICOS}/02_tempo_dns.png', dpi=150); plt.close()
    print('[OK] 02_tempo_dns.png')

def grafico_duracao_total(tcp, rudp):
    fig, axes = plt.subplots(1, 3, figsize=(15, 6))
    fig.suptitle('Duracao da Transferencia HTTP por Arquivo e Cenario', fontweight='bold', fontsize=13)
    for i, cenario in enumerate(CENARIOS):
        ax = axes[i]; x = np.arange(len(ARQUIVOS)); w = 0.35; labels = ['100KB', '500KB', '1MB']
        m_tcp  = [tcp[(tcp['cenario']==cenario) & (tcp['arquivo'].str.contains(a))]['duracao_s'].mean() for a in ARQUIVOS]
        m_rudp = [rudp[(rudp['cenario']==cenario) & (rudp['arquivo'].str.contains(a))]['duracao_s'].mean() for a in ARQUIVOS]
        ax.bar(x-w/2, m_tcp,  w, color=COR_TCP,  alpha=0.85, label='HTTP-TCP')
        ax.bar(x+w/2, m_rudp, w, color=COR_RUDP, alpha=0.85, label='HTTP-R-UDP')
        ax.set_title(DESC_CEN[cenario], fontsize=10)
        ax.set_xticks(x); ax.set_xticklabels(labels)
        ax.set_ylabel('Duracao (s)' if i==0 else '')
        ax.legend(fontsize=8); ax.grid(axis='y', linestyle='--', alpha=0.5); ax.set_ylim(bottom=0)
    plt.tight_layout()
    plt.savefig(f'{GRAFICOS}/03_duracao_transferencia.png', dpi=150); plt.close()
    print('[OK] 03_duracao_transferencia.png')

def grafico_degradacao(tcp, rudp):
    fig, ax = plt.subplots(figsize=(9, 5))
    m_tcp  = [tcp[tcp['cenario']==c]['throughput_mbps'].mean()  for c in CENARIOS]
    m_rudp = [rudp[rudp['cenario']==c]['throughput_mbps'].mean() for c in CENARIOS]
    ax.plot(CENARIOS, m_tcp,  'o-', color=COR_TCP,  label='HTTP-TCP',   linewidth=2.5, markersize=9)
    ax.plot(CENARIOS, m_rudp, 's-', color=COR_RUDP, label='HTTP-R-UDP', linewidth=2.5, markersize=9)
    for c, v in zip(CENARIOS, m_tcp):
        ax.annotate(f'{v:.3f}', (c,v), textcoords='offset points', xytext=(0,10), ha='center', fontsize=9)
    for c, v in zip(CENARIOS, m_rudp):
        ax.annotate(f'{v:.3f}', (c,v), textcoords='offset points', xytext=(0,-16), ha='center', fontsize=9)
    ax.set_ylabel('Throughput Medio (Mbps)')
    ax.set_title('Degradacao do Throughput HTTP por Cenario', fontweight='bold')
    ax.set_xticklabels([DESC_CEN[c] for c in CENARIOS])
    ax.legend(); ax.grid(linestyle='--', alpha=0.4); ax.set_ylim(bottom=0)
    plt.tight_layout()
    plt.savefig(f'{GRAFICOS}/04_degradacao_cenarios.png', dpi=150); plt.close()
    print('[OK] 04_degradacao_cenarios.png')

def grafico_boxplot(tcp, rudp):
    fig, axes = plt.subplots(1, 3, figsize=(14, 6))
    fig.suptitle('Distribuicao do Throughput HTTP: TCP vs R-UDP', fontweight='bold')
    for i, cenario in enumerate(CENARIOS):
        ax = axes[i]
        d_tcp  = tcp[tcp['cenario']==cenario]['throughput_mbps'].values
        d_rudp = rudp[rudp['cenario']==cenario]['throughput_mbps'].values
        bp = ax.boxplot([d_tcp, d_rudp], tick_labels=['HTTP-TCP','HTTP-R-UDP'],
                        patch_artist=True, medianprops={'color':'black','linewidth':2})
        bp['boxes'][0].set_facecolor(COR_TCP);  bp['boxes'][0].set_alpha(0.7)
        bp['boxes'][1].set_facecolor(COR_RUDP); bp['boxes'][1].set_alpha(0.7)
        ax.set_title(DESC_CEN[cenario], fontsize=10)
        ax.grid(axis='y', linestyle='--', alpha=0.5)
        if i==0: ax.set_ylabel('Throughput (Mbps)')
    plt.tight_layout()
    plt.savefig(f'{GRAFICOS}/05_boxplot_throughput.png', dpi=150); plt.close()
    print('[OK] 05_boxplot_throughput.png')

def main():
    print("="*60)
    print("  ANALISE HTTP — TCP vs R-UDP")
    print("  JULIO CESAR DE LIMA MENDES | 20249006910")
    print("="*60)
    try:
        tcp, rudp = carregar()
        print(f"TCP : {len(tcp)} execucoes | R-UDP: {len(rudp)} execucoes")
        print(f"\nGerando graficos em {GRAFICOS}/ ...")
        grafico_throughput_por_arquivo(tcp, rudp)
        grafico_dns_tempo(tcp, rudp)
        grafico_duracao_total(tcp, rudp)
        grafico_degradacao(tcp, rudp)
        grafico_boxplot(tcp, rudp)
        print("\n5 graficos gerados com sucesso!")
    except FileNotFoundError as e:
        print(f"ERRO: {e}")
        print("Execute os testes primeiro com run_testes_http.py")

if __name__ == "__main__":
    main()
