"""
Figuras de análise para o artigo (mapas coropléticos, mapa bivariado e gráficos).

Executar a partir da raiz do projeto (depois de gerar_geopackage.py):
    python gis/figuras_analises.py

Saída em gis/saida/ (PNG 300 dpi + PDF):
    fig_01_acesso.*                taxa de internação e % de saída do município
    fig_02_raca_representacao.*    % PPI no Censo, no CadÚnico e nas internações
    fig_03_razao_taxas_raca.*      razão entre taxas de internação PPI / brancas
    fig_04_bivariado_pbf_saida.*   vulnerabilidade (PBF) x saída do município
    fig_05_raca_deslocamento.*     deslocamento por raça/cor
    fig_06_vulnerabilidade.*       dispersão PBF x saída e PBF x taxa de internação
    fig_07_polos.*                 hospitais que mais recebem crianças

Municípios com poucos casos ficam em cinza nos mapas (limiares em MIN_*), pois proporções
e razões calculadas com pouquíssimas internações são instáveis.
"""

import textwrap

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import patheffects
from matplotlib.cm import ScalarMappable
from matplotlib.colors import Normalize
from matplotlib.patches import Patch, Rectangle

from figuras import barra_escala
from preparacao import DIR_SAIDA, preparar_tudo

ARQ_GPKG = DIR_SAIDA / 'internacoes_pediatricas_pr.gpkg'

MIN_INTERNACOES = 30   # mínimo de internações para mapear proporções por município
MIN_POR_GRUPO = 20     # mínimo de internações PPI e de brancas para comparar taxas
COR_SEM_DADO = '#dcdcdc'
FONTE = 'Fonte: SIH/SUS (2024–2025), CadÚnico/MDS, Censo 2022/IBGE. Elaboração própria.'

plt.rcParams.update({'font.size': 9, 'axes.titlesize': 10, 'axes.titleweight': 'bold'})


def salvar(fig, nome, rodape=None):
    texto = FONTE if rodape is None else f'{FONTE}\n{textwrap.fill(rodape, int(fig.get_figwidth() * 14))}'
    fig.text(0.01, 0.005, texto, fontsize=7, color='#444444', va='bottom')
    for ext, kw in [('png', {'dpi': 300}), ('pdf', {})]:
        fig.savefig(DIR_SAIDA / f'{nome}.{ext}', facecolor='white', **kw)
    plt.close(fig)
    print(f'  {nome}')


def carregar():
    mun = gpd.read_file(ARQ_GPKG, layer='municipios')
    reg = gpd.read_file(ARQ_GPKG, layer='regioes_saude')
    # A malha simplificada deixa frestas entre municípios; fechá-las evita traços soltos.
    reg['geometry'] = reg.geometry.buffer(1500).buffer(-1500)
    mun['n_raca'] = mun['internacoes'] - mun['int_sem_info_raca']
    return mun, reg


def mapa(ax, mun, reg, coluna, cmap, norm, mascara=None):
    """Coroplético; `mascara` (série booleana) marca os municípios com dados suficientes."""
    dados = mun.copy()
    if mascara is not None:
        dados.loc[~mascara, coluna] = np.nan
    dados.plot(ax=ax, column=coluna, cmap=cmap, norm=norm, edgecolor='white', linewidth=0.15,
               missing_kwds={'color': COR_SEM_DADO, 'edgecolor': 'white', 'linewidth': 0.15})
    reg.plot(ax=ax, facecolor='none', edgecolor='#444444', linewidth=0.6)
    ax.set_axis_off()
    ax.set_aspect('equal')


def barra_cores(fig, ax, cmap, norm, rotulo, formato=None, ticks=None, rotulos_ticks=None):
    cb = fig.colorbar(ScalarMappable(norm=norm, cmap=cmap), ax=ax, orientation='horizontal',
                      fraction=0.04, pad=0.02, aspect=30, shrink=0.8, ticks=ticks, format=formato)
    if rotulos_ticks is not None:
        cb.ax.set_xticklabels(rotulos_ticks)
    cb.set_label(rotulo, fontsize=8)
    cb.ax.tick_params(labelsize=7)
    cb.outline.set_visible(False)
    return cb


def legenda_sem_dado(ax, texto):
    ax.legend(handles=[Patch(facecolor=COR_SEM_DADO, label=texto)], loc='lower left',
              bbox_to_anchor=(0.0, 0.0), fontsize=7, frameon=False)


# ============================================================
# FIG 1 — ACESSO: taxa de internação e saída do município
# ============================================================

def fig_acesso(mun, reg):
    fig, axs = plt.subplots(1, 2, figsize=(12, 6.2))
    n1 = Normalize(vmin=5, vmax=35)
    mapa(axs[0], mun, reg, 'taxa_int_1000_criancas_ano', 'YlGnBu', n1)
    axs[0].set_title('Taxa de internação pediátrica\n(por 1.000 crianças de 0–16 anos, por ano)')
    barra_cores(fig, axs[0], 'YlGnBu', n1, 'Internações por 1.000 crianças/ano (valores > 35 em azul-escuro)')

    n2 = Normalize(vmin=0, vmax=1)
    mapa(axs[1], mun, reg, 'pct_fora_municipio', 'OrRd', n2, mascara=mun['internacoes'] >= MIN_INTERNACOES)
    axs[1].set_title('Crianças internadas fora do município de residência\n(% das internações)')
    barra_cores(fig, axs[1], 'OrRd', n2, '% internadas em outro município', formato='%.0f%%' if False else None,
                ticks=[0, .25, .5, .75, 1], rotulos_ticks=['0%', '25%', '50%', '75%', '100%'])
    legenda_sem_dado(axs[1], f'< {MIN_INTERNACOES} internações (não mapeado)')
    barra_escala(axs[0], km=100)
    fig.subplots_adjust(left=0.01, right=0.99, top=0.9, bottom=0.1, wspace=0.02)
    fig.suptitle('Paraná, 2024–2025: onde as crianças são internadas e quem precisa sair do município', fontsize=12, y=0.97)
    salvar(fig, 'fig_01_acesso')


# ============================================================
# FIG 2 — RAÇA/COR: representação em três bases
# ============================================================

def fig_raca_representacao(mun, reg):
    fig, axs = plt.subplots(1, 3, figsize=(15, 5.6))
    norm = Normalize(vmin=0, vmax=0.7)
    cfg = [
        ('pct_ppi_censo_0_16', 'Censo 2022\ncrianças de 0–16 anos', None),
        ('pct_ppi_cadunico', 'CadÚnico\nmédia mensal 2024–2025', None),
        ('pct_ppi_internacoes', 'Internações pediátricas (SIH)\nraça/cor informada pelo hospital', mun['n_raca'] >= MIN_INTERNACOES),
    ]
    for ax, (col, titulo, mascara) in zip(axs, cfg):
        mapa(ax, mun, reg, col, 'YlOrBr', norm, mascara=mascara)
        ax.set_title(titulo)
    barra_cores(fig, axs[1], 'YlOrBr', norm, '% de pretos, pardos e indígenas (PPI)',
                ticks=[0, .2, .4, .6], rotulos_ticks=['0%', '20%', '40%', '60%'])
    legenda_sem_dado(axs[2], f'< {MIN_INTERNACOES} internações com raça informada')
    fig.subplots_adjust(left=0.01, right=0.99, top=0.84, bottom=0.12, wspace=0.02)
    fig.suptitle('A mesma proporção de pretos, pardos e indígenas, medida em três bases diferentes', fontsize=12, y=0.97)
    salvar(fig, 'fig_02_raca_representacao',
           'No SIH a raça/cor é registrada pelo hospital; no Censo e no CadÚnico, é autodeclarada.')


# ============================================================
# FIG 3 — RAZÃO DE TAXAS PPI / BRANCAS
# ============================================================

def fig_razao_taxas(mun, reg):
    mascara = (mun['int_ppi'] >= MIN_POR_GRUPO) & (mun['int_branca'] >= MIN_POR_GRUPO)
    d = mun.copy()
    d['log2_razao'] = np.log2(d['razao_taxa_ppi_branca'].replace(0, np.nan))
    norm = Normalize(vmin=-2, vmax=2)  # razão de 0,25 a 4, centrada em 1

    fig, ax = plt.subplots(figsize=(8, 7))
    mapa(ax, d, reg, 'log2_razao', 'PuOr', norm, mascara=mascara)
    barra_cores(fig, ax, 'PuOr', norm, 'Taxa de internação PPI ÷ taxa de internação de brancas',
                ticks=[-2, -1, 0, 1, 2], rotulos_ticks=['0,25', '0,5', '1', '2', '4'])
    legenda_sem_dado(ax, f'< {MIN_POR_GRUPO} internações PPI ou < {MIN_POR_GRUPO} de brancas')
    barra_escala(ax, km=100)
    n = int(mascara.sum())
    abaixo = (mun.loc[mascara, 'razao_taxa_ppi_branca'] < 1).mean() * 100
    ax.set_title(f'Crianças pretas, pardas e indígenas são menos internadas que brancas?\n'
                 f'Razão de taxas por município (n = {n}; razão < 1 em {abaixo:.0f}%)')
    fig.subplots_adjust(left=0.02, right=0.98, top=0.9, bottom=0.15)
    salvar(fig, 'fig_03_razao_taxas_raca',
           'Taxa = internações / 2 anos / crianças de 0–16 anos do grupo (Censo 2022). Razão < 1: PPI menos internadas que brancas. '
           'Pode refletir barreira de acesso e/ou sub-registro de raça/cor no SIH.')


# ============================================================
# FIG 4 — MAPA BIVARIADO: vulnerabilidade x saída do município
# ============================================================

def fig_bivariado(mun, reg):
    # Paleta bivariada 3x3 (Stevens): linhas = % fora do município (baixo -> alto),
    # colunas = % de crianças no PBF (baixo -> alto).
    pal = [['#e8e8e8', '#ace4e4', '#5ac8c8'],
           ['#dfb0d6', '#a5add3', '#5698b9'],
           ['#be64ac', '#8c62aa', '#3b4994']]
    d = mun[mun['internacoes'] >= MIN_INTERNACOES].copy()
    d['cx'] = pd.qcut(d['pct_criancas_bf'], 3, labels=False)
    # Saída do município: classes fixas, pois 43% dos municípios têm exatamente 100% (empates quebrariam tercis).
    d['cy'] = pd.cut(d['pct_fora_municipio'], [-0.01, 0.5, 0.999, 1.01], labels=False)
    q_x = d['pct_criancas_bf'].quantile([1 / 3, 2 / 3]).round(2).tolist()
    d['cor'] = [pal[int(y)][int(x)] for x, y in zip(d['cx'], d['cy'])]

    fig, ax = plt.subplots(figsize=(9, 7.2))
    mun.plot(ax=ax, color=COR_SEM_DADO, edgecolor='white', linewidth=0.15)
    d.plot(ax=ax, color=d['cor'], edgecolor='white', linewidth=0.15)
    reg.plot(ax=ax, facecolor='none', edgecolor='#444444', linewidth=0.6)
    ax.set_axis_off()
    ax.set_aspect('equal')
    barra_escala(ax, km=100)
    ax.set_title('Vulnerabilidade social e necessidade de sair do município para internar', fontsize=11)

    # Legenda 3x3 em eixo próprio, no canto inferior direito.
    li = fig.add_axes([0.70, 0.08, 0.16, 0.16])
    for i in range(3):
        for j in range(3):
            li.add_patch(Rectangle((j, i), 1, 1, facecolor=pal[i][j], edgecolor='white'))
    li.set_xlim(0, 3)
    li.set_ylim(0, 3)
    li.set_xticks([])
    li.set_yticks([])
    for s in li.spines.values():
        s.set_visible(False)
    li.set_xlabel('Crianças no PBF →', fontsize=7)
    li.set_ylabel('Saída do município →', fontsize=7)
    for k, r in enumerate(['< 50%', '50–99%', '100%']):
        li.text(-0.08, k + 0.5, r, ha='right', va='center', fontsize=6)
    li.yaxis.set_label_coords(-0.42, 0.5)
    ax.legend(handles=[Patch(facecolor=COR_SEM_DADO, label=f'< {MIN_INTERNACOES} internações')],
              loc='lower left', fontsize=7, frameon=False)
    fig.subplots_adjust(left=0.01, right=0.99, top=0.93, bottom=0.08)
    salvar(fig, 'fig_04_bivariado_pbf_saida',
           f'Colunas (crianças de 0–15 anos no PBF / população 0–15, em tercis): até {q_x[0]:.0%}, até {q_x[1]:.0%} e acima. '
           'Linhas (% das internações fora do município): menos de 50%, de 50% a 99% e exatamente 100%. '
           'Azul-escuro: alta vulnerabilidade e saída total.')


# ============================================================
# FIG 5 — RAÇA/COR x DESLOCAMENTO
# ============================================================

def fig_raca_deslocamento(s):
    ordem = ['Branca', 'Parda', 'Preta', 'Indígena', 'Amarela']
    g = s[s['raca_cor_paciente'].isin(ordem)].groupby('raca_cor_paciente').agg(
        n=('id_aih', 'size'), fora_mun=('fora_municipio', 'mean'),
        fora_reg=('fora_regiao_saude', 'mean'), mais100=('mais_100km', 'mean')).loc[ordem]

    fig, axs = plt.subplots(1, 2, figsize=(12, 4.8), gridspec_kw={'width_ratios': [1.15, 1]})
    ax = axs[0]
    x = np.arange(len(ordem))
    w = 0.26
    for k, (col, rot, cor) in enumerate([('fora_mun', 'Fora do município', '#d95f02'),
                                          ('fora_reg', 'Fora da Região de Saúde', '#7570b3'),
                                          ('mais100', 'A mais de 100 km', '#1b9e77')]):
        b = ax.bar(x + (k - 1) * w, g[col] * 100, w, label=rot, color=cor)
        ax.bar_label(b, fmt='%.0f', fontsize=7, padding=1)
    ax.set_xticks(x)
    ax.set_xticklabels([f'{r}\n(n = {int(g.loc[r, "n"]):,})'.replace(',', '.') for r in ordem])
    ax.set_ylabel('% das internações')
    ax.set_title('Quem sai do município, da região e do raio de 100 km')
    ax.legend(frameon=False, fontsize=8)
    ax.spines[['top', 'right']].set_visible(False)

    # ECDF da distância, só para quem foi internado fora do município.
    ax = axs[1]
    fora = s[s['fora_municipio']]
    for rot, filtro, cor in [('Brancas', fora['raca_grupo'] == 'Branca', '#555555'),
                             ('Pretas, pardas e indígenas', fora['raca_grupo'] == 'PPI', '#d95f02')]:
        d = np.sort(fora.loc[filtro, 'dist_km'].values)
        ax.plot(d, np.arange(1, len(d) + 1) / len(d) * 100, label=f'{rot} (n = {len(d):,})'.replace(',', '.') if False else f'{rot} (n = ' + f'{len(d):,}'.replace(',', '.') + ')',
                color=cor, lw=1.8)
    ax.set_xlim(0, 300)
    ax.set_xlabel('Distância até o hospital (km, linha reta)')
    ax.set_ylabel('% acumulado das internações')
    ax.set_title('Distância percorrida por quem saiu do município')
    ax.legend(frameon=False, fontsize=8, loc='lower right')
    ax.grid(alpha=0.25)
    ax.spines[['top', 'right']].set_visible(False)
    fig.subplots_adjust(left=0.06, right=0.99, top=0.88, bottom=0.2, wspace=0.22)
    salvar(fig, 'fig_05_raca_deslocamento',
           'Crianças indígenas: n pequeno, interpretar com cautela. Distância = centroide do município de residência até o do hospital.')


# ============================================================
# FIG 6 — VULNERABILIDADE (dispersões)
# ============================================================

def fig_vulnerabilidade(mun):
    d = mun[mun['internacoes'] >= MIN_INTERNACOES].copy()
    fig, axs = plt.subplots(1, 2, figsize=(12, 5))
    pares = [('pct_fora_municipio', '% das internações fora do município', 100),
             ('taxa_int_1000_criancas_ano', 'Taxa de internação (por 1.000 crianças/ano)', 1)]
    destaques = ['Colombo', 'Piraquara', 'Almirante Tamandaré', 'Campina Grande do Sul', 'Pato Bragado', 'Curitiba']
    for ax, (col, rotulo, k) in zip(axs, pares):
        ax.scatter(d['pct_criancas_bf'] * 100, d[col] * k, s=np.sqrt(d['internacoes']) * 2.2,
                   color='#3b4994', alpha=0.35, edgecolor='white', linewidth=0.4)
        rho = d['pct_criancas_bf'].corr(d[col], method='spearman')
        ax.set_xlabel('Crianças de 0–15 anos no Bolsa Família (% da população 0–15)')
        ax.set_ylabel(rotulo)
        ax.set_title(f'Spearman ρ = {rho:.2f}  (n = {len(d)} municípios)')
        ajuste = {'Almirante Tamandaré': (-5, -12, 'right'), 'Curitiba': (-6, 6, 'right'),
                  'Piraquara': (6, 5, 'left'), 'Colombo': (6, -11, 'left')}
        for _, r in d[d['nome'].isin(destaques)].iterrows():
            dx, dy, ha = ajuste.get(r['nome'], (5, 4, 'left'))
            ax.annotate(r['nome'], (r['pct_criancas_bf'] * 100, r[col] * k), xytext=(dx, dy), ha=ha,
                        textcoords='offset points', fontsize=7, path_effects=[patheffects.withStroke(linewidth=2, foreground='white')])
        ax.grid(alpha=0.2)
        ax.spines[['top', 'right']].set_visible(False)
    fig.suptitle('Municípios com mais crianças no Bolsa Família mandam mais crianças para fora?', fontsize=12, y=0.98)
    fig.subplots_adjust(left=0.07, right=0.99, top=0.86, bottom=0.17, wspace=0.18)
    salvar(fig, 'fig_06_vulnerabilidade',
           f'Cada ponto é um município com ≥ {MIN_INTERNACOES} internações; tamanho ∝ √internações. Associação ecológica, não individual.')


# ============================================================
# FIG 7 — POLOS
# ============================================================

def fig_polos():
    p = gpd.read_file(ARQ_GPKG, layer='polos_hospitalares')
    p = p[p['sigla_uf_estab'] == 'PR'].sort_values('internacoes_recebidas', ascending=False).head(12).iloc[::-1]
    proprios = p['internacoes_recebidas'] - p['vindas_de_fora']

    fig, ax = plt.subplots(figsize=(9, 5.6))
    y = np.arange(len(p))
    ax.barh(y, proprios, color='#9a9a9a', label='Residentes do próprio município')
    ax.barh(y, p['vindas_de_fora'], left=proprios, color='#d95f02', label='Vindas de outros municípios')
    for yi, (_, r) in zip(y, p.iterrows()):
        ax.text(r['internacoes_recebidas'] + 150, yi,
                f'{r["vindas_de_fora"] / r["internacoes_recebidas"]:.0%} de fora · {int(r["municipios_de_origem"])} municípios',
                va='center', fontsize=7.5)
    ax.set_yticks(y)
    ax.set_yticklabels(p['nome_estab'])
    ax.set_xlabel('Internações pediátricas recebidas, 2024–2025')
    ax.set_xlim(0, p['internacoes_recebidas'].max() * 1.35)
    ax.legend(frameon=False, loc='lower right')
    ax.spines[['top', 'right']].set_visible(False)
    ax.set_title('Os 12 municípios que mais internam crianças do Paraná', fontsize=11)
    fig.subplots_adjust(left=0.22, right=0.98, top=0.9, bottom=0.17)
    salvar(fig, 'fig_07_polos', 'Municípios de origem = quantos municípios do PR enviaram ao menos uma criança.')


def main():
    DIR_SAIDA.mkdir(exist_ok=True)
    mun, reg = carregar()
    internacoes = preparar_tudo()['internacoes']
    print('Gerando figuras em', DIR_SAIDA)
    fig_acesso(mun, reg)
    fig_raca_representacao(mun, reg)
    fig_razao_taxas(mun, reg)
    fig_bivariado(mun, reg)
    fig_raca_deslocamento(internacoes)
    fig_vulnerabilidade(mun)
    fig_polos()


if __name__ == '__main__':
    main()
