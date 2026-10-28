"""
Figuras da análise de acessibilidade hospitalar (lê gis/saida/, não acessa o banco).

Executar a partir da raiz do projeto, depois de gis/acessibilidade_postgis.py:
    python gis/figuras_acessibilidade.py

Saída em gis/saida/ (PNG 300 dpi + PDF):
    fig_a1_algoritmo.*      fluxo da solução (tabelas -> funções GIS -> resultados)
    fig_a2_mapas.*          distância ao hospital mais próximo; cobertura de 30 km e municípios sem hospital
    fig_a3_relacoes.*       SIH por presença de hospital, dispersão e matriz de Spearman
"""

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import Normalize
from matplotlib.lines import Line2D
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Patch
from matplotlib import patheffects

from figuras import barra_escala
from preparacao import DIR_SAIDA

ARQ_GPKG = DIR_SAIDA / 'acessibilidade_hospitalar_pr.gpkg'
FONTE = 'Fonte: PostGIS (postgiscwb), CadÚnico/MDS, SIH/SUS (2024–2025). Elaboração própria.'
COR_SEM_HOSP = '#d95f02'
COR_COM_HOSP = '#7570b3'

plt.rcParams.update({'font.size': 9, 'axes.titlesize': 10, 'axes.titleweight': 'bold'})


def salvar(fig, nome, rodape=None):
    fig.text(0.01, 0.005, FONTE if rodape is None else f'{FONTE}\n{rodape}', fontsize=7, color='#444444', va='bottom')
    for ext, kw in [('png', {'dpi': 300}), ('pdf', {})]:
        fig.savefig(DIR_SAIDA / f'{nome}.{ext}', facecolor='white', **kw)
    plt.close(fig)
    print(' ', nome)


# ============================================================
# A1 — fluxo da solução
# ============================================================

def caixa(ax, x, y, w, h, titulo, linhas, cor, tam=7.5):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.01,rounding_size=0.012',
                                facecolor=cor, edgecolor='#555555', linewidth=0.8))
    ax.text(x + w / 2, y + h - 0.018, titulo, ha='center', va='top', fontsize=tam + 0.5, fontweight='bold')
    descer = 0.085 if '\n' in titulo else 0.052
    ax.text(x + w / 2, y + h - descer, '\n'.join(linhas), ha='center', va='top', fontsize=tam, linespacing=1.35)


def seta(ax, x0, y0, x1, y1):
    ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle='-|>', mutation_scale=10, color='#444444', lw=1))


def fig_algoritmo():
    fig, ax = plt.subplots(figsize=(11, 6.4))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')
    tab = '#e8f1fa'
    gis = '#fdf0e0'
    res = '#e6f4ea'

    ax.text(0.005, 0.985, 'Tabelas de entrada', fontsize=9, fontweight='bold', va='top')
    caixa(ax, 0.005, 0.79, 0.19, 0.16, 'saude."saude_parana_CRM"', ['18.448 estabelecimentos', '956 com nome de hospital'], tab, 7)
    caixa(ax, 0.005, 0.57, 0.19, 0.18, 'bd2_ricardo_divisa_\nmunicipio_parana', ['399 polígonos municipais', 'SRID declarado 4326 (errado)'], tab, 7)

    ax.text(0.27, 0.985, 'Etapas (SQL / funções PostGIS)', fontsize=9, fontweight='bold', va='top')
    caixa(ax, 0.27, 0.79, 0.28, 0.16, '1. Hospitais válidos',
          ['regex no nome · 1 por id_estab · coordenadas no PR', 'ST_Transform → EPSG:29192  (472 hospitais)'], gis)
    caixa(ax, 0.27, 0.60, 0.28, 0.14, '2. Municípios',
          ['ST_SetSRID (corrige o rótulo) · ST_PointOnSurface', 'sede garantidamente dentro do polígono'], gis)
    caixa(ax, 0.27, 0.41, 0.28, 0.14, '3. Junção espacial',
          ['ST_Within(hospital, município)', '→ nº de hospitais no território'], gis)
    caixa(ax, 0.27, 0.22, 0.28, 0.14, '4. Hospital mais próximo',
          ['operador KNN  <->  +  ST_Distance', 'ST_MakeLine(sede, hospital)  (linha)'], gis)
    caixa(ax, 0.27, 0.03, 0.28, 0.14, '5. Cobertura de 30 km',
          ['ST_DWithin (nº de hospitais em 30 km)', 'ST_Buffer → ST_Union → ST_Intersection → ST_Area'], gis)

    ax.text(0.60, 0.985, 'Tabela do grupo', fontsize=9, fontweight='bold', va='top')
    caixa(ax, 0.60, 0.79, 0.19, 0.16, 'bd2_2556553', ['CadÚnico/PBF, município × mês', '67.431 linhas · 399 municípios'], tab, 7)
    caixa(ax, 0.60, 0.59, 0.19, 0.15, '6. Vulnerabilidade',
          ['agrega 2024–2025 (média mensal)', 'PBF/inscritos · % PPI · % pobreza'], gis, 7)
    caixa(ax, 0.60, 0.36, 0.19, 0.18, '7. Junção por nome',
          ['unaccent + UPPER', '+ 2 grafias corrigidas', '(Pinhal de/do · Mello/Melo)'], gis, 7)

    ax.text(0.84, 0.985, 'Resultados', fontsize=9, fontweight='bold', va='top')
    caixa(ax, 0.84, 0.76, 0.15, 0.19, 'Tabela municipal', ['399 linhas', 'acessibilidade +', 'vulnerabilidade'], res)
    caixa(ax, 0.84, 0.44, 0.15, 0.24, 'Estatística', ['Pearson (SQL)', 'Spearman (Python)', '+ cruzamento com', 'o SIH (local)'], res)
    caixa(ax, 0.84, 0.08, 0.15, 0.19, 'GeoPackage', ['municípios · hospitais', 'ligações · cobertura', '(EPSG:29192) → QGIS'], res)

    seta(ax, 0.195, 0.87, 0.265, 0.87)        # CRM -> 1
    seta(ax, 0.195, 0.66, 0.265, 0.66)        # divisa -> 2
    for ya, yb in ((0.79, 0.745), (0.60, 0.555), (0.41, 0.365), (0.22, 0.175)):
        seta(ax, 0.41, ya, 0.41, yb)          # 1 -> 2 -> 3 -> 4 -> 5
    seta(ax, 0.695, 0.79, 0.695, 0.745)       # bd2_2556553 -> 6
    seta(ax, 0.695, 0.59, 0.695, 0.545)       # 6 -> 7
    seta(ax, 0.55, 0.48, 0.60, 0.47)          # 3 -> 7
    seta(ax, 0.55, 0.29, 0.60, 0.40)          # 4 -> 7
    seta(ax, 0.79, 0.50, 0.84, 0.80)          # 7 -> tabela municipal
    seta(ax, 0.915, 0.76, 0.915, 0.695)       # tabela -> estatística
    seta(ax, 0.55, 0.10, 0.84, 0.17)          # 5 -> geopackage
    fig.subplots_adjust(left=0.01, right=0.99, top=0.99, bottom=0.07)
    salvar(fig, 'fig_a1_algoritmo')


# ============================================================
# A2 — mapas
# ============================================================

def fig_mapas(mun, hosp, cob, lig):
    fig, axs = plt.subplots(1, 2, figsize=(13, 6.3))
    infantil = hosp[hosp['infantil']]

    ax = axs[0]
    norm = Normalize(vmin=0, vmax=40)
    mun.plot(ax=ax, column='dist_hosp_km', cmap='YlOrRd', norm=norm, edgecolor='white', linewidth=0.2)
    hosp.plot(ax=ax, color='#222222', markersize=4, zorder=4)
    infantil.plot(ax=ax, color='#1f78b4', marker='*', markersize=95, edgecolor='white', linewidth=0.6, zorder=5)
    for _, r in infantil.iterrows():
        dx, dy, ha = (-8, -13, 'right') if r['cidade'] == 'Campo Largo' else (6, -11, 'left')
        ax.annotate(r['cidade'], (r.geometry.x, r.geometry.y), xytext=(dx, dy), ha=ha, textcoords='offset points', fontsize=7,
                    fontweight='bold', color='#1f78b4',
                    path_effects=[patheffects.withStroke(linewidth=2, foreground='white')])
    ax.set_title('(a) Distância da sede ao hospital mais próximo')
    cb = fig.colorbar(plt.cm.ScalarMappable(norm=norm, cmap='YlOrRd'), ax=ax, orientation='horizontal',
                      fraction=0.04, pad=0.02, aspect=30, shrink=0.8)
    cb.set_label('km em linha reta (≥ 40 km no tom mais escuro)', fontsize=8)
    cb.outline.set_visible(False)
    ax.legend(handles=[Line2D([0], [0], marker='o', color='none', markerfacecolor='#222222', markersize=4, label='Hospital'),
                       Line2D([0], [0], marker='*', color='none', markerfacecolor='#1f78b4', markersize=11, label='Hospital infantil')],
              loc='lower left', fontsize=7, frameon=False, bbox_to_anchor=(0.0, 0.13))
    barra_escala(ax, km=100)

    ax = axs[1]
    mun.plot(ax=ax, color='#f2f2f2', edgecolor='white', linewidth=0.2)
    cob.plot(ax=ax, color='#9ecae1', alpha=0.45, edgecolor='none', zorder=2)
    mun[mun['n_hosp_municipio'] == 0].plot(ax=ax, color=COR_SEM_HOSP, alpha=0.55, edgecolor='white', linewidth=0.2, zorder=3)
    mun[mun['n_hosp_30km'] == 0].plot(ax=ax, color='#99000d', edgecolor='white', linewidth=0.2, zorder=3.5)
    lig.plot(ax=ax, color='#555555', linewidth=0.35, alpha=0.6, zorder=3.8)
    hosp.plot(ax=ax, color='#222222', markersize=4, zorder=4)
    n_sem = int((mun['n_hosp_municipio'] == 0).sum())
    n_30 = int((mun['n_hosp_30km'] == 0).sum())
    ax.set_title('(b) Municípios sem hospital e cobertura de 30 km')
    ax.legend(handles=[Patch(facecolor='#9ecae1', alpha=0.6, label='Até 30 km de algum hospital'),
                       Patch(facecolor=COR_SEM_HOSP, alpha=0.6, label=f'Sem hospital no território (n = {n_sem})'),
                       Patch(facecolor='#99000d', label=f'Sem hospital em 30 km da sede (n = {n_30})'),
                       Line2D([0], [0], color='#555555', lw=1, label='Ligação ao hospital mais próximo')],
              loc='lower right', fontsize=7.5, frameon=False, bbox_to_anchor=(1.0, 0.0))
    for a in axs:
        a.set_axis_off()
        a.set_aspect('equal')
    fig.subplots_adjust(left=0.01, right=0.99, top=0.93, bottom=0.14, wspace=0.02)
    fig.suptitle('Acessibilidade hospitalar dos 399 municípios do Paraná', fontsize=12, y=0.99)
    salvar(fig, 'fig_a2_mapas', 'Distâncias entre a sede (ponto interno ao polígono) e o hospital; EPSG:29192. '
                                'Hospitais: nome de hospital na tabela de estabelecimentos (n = 472).')


# ============================================================
# A3 — relações
# ============================================================

def fig_relacoes(tab, sih_grupo, sp):
    fig = plt.figure(figsize=(13, 4.8))
    gs = fig.add_gridspec(1, 3, width_ratios=[0.9, 1.1, 1.15], wspace=0.34)

    ax = fig.add_subplot(gs[0])
    g = sih_grupo.set_index('tem_hospital')
    rot = ['Sem hospital\nno município', 'Com hospital\nno município']
    val = [g.loc[False, 'pct_internacoes_fora'] * 100, g.loc[True, 'pct_internacoes_fora'] * 100]
    b = ax.bar(rot, val, color=[COR_SEM_HOSP, COR_COM_HOSP], width=0.6)
    ax.bar_label(b, fmt='%.1f%%', fontsize=9, padding=2)
    for i, k in enumerate([False, True]):
        r = g.loc[k]
        ax.text(i, 6, f'{int(r["municipios"])} municípios\n{int(r["mun_100_por_cento"])} com 100%\nfora', ha='center', fontsize=7.5, color='white')
    ax.set_ylim(0, 100)
    ax.set_ylabel('% das internações pediátricas fora do município (SIH)')
    ax.set_title('(a) Hospital no território\ne saída para internar')
    ax.spines[['top', 'right']].set_visible(False)

    ax = fig.add_subplot(gs[1])
    cores = np.where(tab['tem_hospital'], COR_COM_HOSP, COR_SEM_HOSP)
    ax.scatter(tab['dist_hosp_km'], tab['pct_bf_inscritos'] * 100, c=cores, s=14, alpha=0.65, edgecolor='none')
    r = sp[(sp['x'] == 'dist_hosp_km') & (sp['y'] == 'pct_bf_inscritos')].iloc[0]
    m, c = np.polyfit(tab['dist_hosp_km'], tab['pct_bf_inscritos'] * 100, 1)
    xs = np.linspace(0, tab['dist_hosp_km'].max(), 50)
    ax.plot(xs, m * xs + c, color='#333333', lw=1.2)
    ax.set_xlabel('Distância ao hospital mais próximo (km)')
    ax.set_ylabel('% dos inscritos no CadÚnico que recebem Bolsa Família')
    ax.set_title(f'(b) Distância × vulnerabilidade\nSpearman ρ = {r["rho"]:.2f} (n = {int(r["n"])})')
    ax.legend(handles=[Line2D([0], [0], marker='o', color='none', markerfacecolor=COR_COM_HOSP, label='Com hospital'),
                       Line2D([0], [0], marker='o', color='none', markerfacecolor=COR_SEM_HOSP, label='Sem hospital')],
              frameon=False, fontsize=8, loc='upper left')
    ax.spines[['top', 'right']].set_visible(False)
    ax.grid(alpha=0.2)

    ax = fig.add_subplot(gs[2])
    nomes_x = {'dist_hosp_km': 'Distância ao\nhospital (km)', 'pct_area_ate_30km': '% da área a\naté 30 km',
               'n_hosp_30km': 'Nº de hospitais\nem 30 km', 'dist_hosp_infantil_km': 'Distância ao hosp.\ninfantil (km)'}
    nomes_y = {'pct_bf_inscritos': 'PBF/\ninscritos', 'pct_ppi_cadunico': '% PPI\nCadÚnico', 'pct_bf_pobreza': '% pobreza\nno PBF',
               'pct_fora_municipio': 'Saída do\nmunicípio\n(SIH)', 'taxa_int_1000_criancas_ano': 'Taxa de\ninternação\n(SIH)'}
    piv = sp.pivot(index='x', columns='y', values='rho').loc[list(nomes_x), list(nomes_y)]
    pv = sp.pivot(index='x', columns='y', values='p').loc[list(nomes_x), list(nomes_y)]
    im = ax.imshow(piv.values, cmap='RdBu_r', vmin=-0.5, vmax=0.5, aspect='auto')
    for i in range(piv.shape[0]):
        for j in range(piv.shape[1]):
            sig = pv.values[i, j] < 0.0025   # Bonferroni: 0,05 / 20 testes
            ax.text(j, i, f'{piv.values[i, j]:.2f}' + ('*' if sig else ''), ha='center', va='center', fontsize=8.5,
                    fontweight='bold' if sig else 'normal', color='white' if abs(piv.values[i, j]) > 0.33 else '#222222')
    ax.set_xticks(range(piv.shape[1]))
    ax.set_xticklabels(list(nomes_y.values()), fontsize=6.8)
    ax.set_yticks(range(piv.shape[0]))
    ax.set_yticklabels(list(nomes_x.values()), fontsize=7.5)
    ax.axvline(2.5, color='white', lw=3)
    ax.set_title('(c) Correlação de Spearman\n(* p < 0,0025, Bonferroni)')
    for s in ax.spines.values():
        s.set_visible(False)
    fig.colorbar(im, ax=ax, fraction=0.04, pad=0.02).outline.set_visible(False)
    fig.subplots_adjust(left=0.06, right=0.95, top=0.84, bottom=0.22)
    salvar(fig, 'fig_a3_relacoes',
           'CadÚnico: 399 municípios, média 2024–2025. SIH: municípios com ≥ 30 internações (n = 326), exceto em (a), que soma todas as internações. '
           'Análise ecológica (município), sem inferência individual.')


def main():
    mun = gpd.read_file(ARQ_GPKG, layer='municipios_acesso')
    hosp = gpd.read_file(ARQ_GPKG, layer='hospitais')
    cob = gpd.read_file(ARQ_GPKG, layer='cobertura_30km')
    lig = gpd.read_file(ARQ_GPKG, layer='ligacao_hospital_proximo')
    tab = pd.read_csv(DIR_SAIDA / 'acess_05_municipios_sih.csv')
    sih_grupo = pd.read_csv(DIR_SAIDA / 'acess_06_sih_por_grupo.csv')
    sp = pd.read_csv(DIR_SAIDA / 'acess_07_spearman.csv')
    print('Gerando figuras')
    fig_algoritmo()
    fig_mapas(mun, hosp, cob, lig)
    fig_relacoes(tab, sih_grupo, sp)


if __name__ == '__main__':
    main()
