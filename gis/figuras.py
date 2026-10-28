"""
Figura final: destino principal das internações pediátricas de cada município do Paraná.

Executar a partir da raiz do projeto (depois de gerar_geopackage.py):
    python gis/figuras.py

Saída: gis/saida/fig_fluxo_principal.png (300 dpi) e .pdf (vetorial).
Usa as camadas do GeoPackage; nenhum dado é recalculado aqui.
"""

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D
from matplotlib.patches import FancyArrow

from preparacao import DIR_SAIDA

ARQ_GPKG = DIR_SAIDA / 'internacoes_pediatricas_pr.gpkg'
N_DESTINOS = 8  # destinos com cor própria; os demais ficam em cinza

# Paleta categórica (ColorBrewer Dark2): cores bem distintas entre si.
PALETA = ['#1b9e77', '#d95f02', '#7570b3', '#e7298a', '#66a61e', '#e6ab02', '#a6761d', '#1f78b4']
COR_OUTROS = '#9a9a9a'


def barra_escala(ax, km=100, margem=0.04):
    x0, x1 = ax.get_xlim()
    y0, y1 = ax.get_ylim()
    x = x0 + (x1 - x0) * margem
    y = y0 + (y1 - y0) * margem
    ax.plot([x, x + km * 1000], [y, y], color='black', lw=3, solid_capstyle='butt', zorder=10)
    ax.text(x + km * 500, y + (y1 - y0) * 0.012, f'{km} km', ha='center', va='bottom', fontsize=8, zorder=10)


def seta_norte(ax, margem=0.05):
    x0, x1 = ax.get_xlim()
    y0, y1 = ax.get_ylim()
    x = x1 - (x1 - x0) * margem
    y = y1 - (y1 - y0) * 0.12
    ax.add_patch(FancyArrow(x, y, 0, (y1 - y0) * 0.06, width=(x1 - x0) * 0.006,
                            head_width=(x1 - x0) * 0.018, head_length=(y1 - y0) * 0.02,
                            color='black', zorder=10))
    ax.text(x, y - (y1 - y0) * 0.015, 'N', ha='center', va='top', fontsize=10, fontweight='bold', zorder=10)


def main():
    municipios = gpd.read_file(ARQ_GPKG, layer='municipios')
    regioes = gpd.read_file(ARQ_GPKG, layer='regioes_saude')
    fluxo = gpd.read_file(ARQ_GPKG, layer='fluxo_principal')
    polos = gpd.read_file(ARQ_GPKG, layer='polos_hospitalares')

    # Destinos com cor própria: os que são o destino principal do maior número de municípios.
    top = fluxo['nome_estab'].value_counts().head(N_DESTINOS).index.tolist()
    cor = {nome: PALETA[i] for i, nome in enumerate(top)}
    fluxo['cor'] = fluxo['nome_estab'].map(cor).fillna(COR_OUTROS)
    fluxo['ordem'] = fluxo['nome_estab'].isin(top)  # cinzas desenhadas primeiro, embaixo

    # Largura proporcional à raiz do volume (raiz suaviza a diferença entre fluxos grandes e pequenos).
    fluxo['largura'] = 0.4 + 2.2 * np.sqrt(fluxo['internacoes'] / fluxo['internacoes'].max())
    fluxo = fluxo.sort_values(['ordem', 'internacoes'])

    fig, ax = plt.subplots(figsize=(11, 8.5))
    municipios.plot(ax=ax, facecolor='#f4f4f4', edgecolor='#d0d0d0', linewidth=0.2, zorder=1)
    # A malha simplificada deixa frestas entre municípios; fechá-las evita traços soltos no contorno.
    regioes['geometry'] = regioes.geometry.buffer(1500).buffer(-1500)
    regioes.plot(ax=ax, facecolor='none', edgecolor='#555555', linewidth=0.7, zorder=2)

    for _, r in fluxo.iterrows():
        x, y = r.geometry.xy
        ax.plot(x, y, color=r['cor'], lw=r['largura'], alpha=0.65 if r['ordem'] else 0.45,
                solid_capstyle='round', zorder=3 if r['ordem'] else 2.5)

    # Polos: círculo proporcional ao volume recebido; rótulo só nos destinos coloridos.
    polos = polos[polos['sigla_uf_estab'] == 'PR'].sort_values('internacoes_recebidas', ascending=False)
    ax.scatter(polos.geometry.x, polos.geometry.y, s=4 + polos['internacoes_recebidas'] / 40,
               facecolor='white', edgecolor='#333333', linewidth=0.5, zorder=5)
    deslocamento = {'Curitiba': (-8, -12), 'Campo Largo': (-12, 8, 'right'), 'Londrina': (6, 6), 'Maringá': (-6, 8)}
    for _, p in polos[polos['nome_estab'].isin(top)].iterrows():
        dx, dy, *ha = deslocamento.get(p['nome_estab'], (6, 6))
        ax.annotate(p['nome_estab'], (p.geometry.x, p.geometry.y), xytext=(dx, dy),
                    textcoords='offset points', ha=ha[0] if ha else 'left', fontsize=8, fontweight='bold', zorder=6,
                    path_effects=[__import__('matplotlib.patheffects', fromlist=['x']).withStroke(linewidth=2.5, foreground='white')])

    # Enquadra só o Paraná: hospitais de outros estados esticariam os eixos.
    xmin, ymin, xmax, ymax = municipios.total_bounds
    ax.set_xlim(xmin - 20000, xmax + 20000)
    ax.set_ylim(ymin - 20000, ymax + 20000)
    ax.set_axis_off()
    ax.set_aspect('equal')
    barra_escala(ax)
    seta_norte(ax)

    legenda = [Line2D([0], [0], color=cor[n], lw=3, label=n) for n in top]
    legenda.append(Line2D([0], [0], color=COR_OUTROS, lw=3, label='Outros destinos'))
    fig.legend(handles=legenda, title='Destino principal (cor da linha)', loc='lower center',
               bbox_to_anchor=(0.5, 0.075), ncol=5, fontsize=8, title_fontsize=9, frameon=False)
    tam = [Line2D([0], [0], color='#444444', lw=0.4 + 2.2 * np.sqrt(v / fluxo['internacoes'].max()),
                  label=f'{v}') for v in [10, 100, 500, 1000]]
    ax.legend(handles=tam, title='Internações (2024–2025)\nespessura da linha', loc='lower right',
              bbox_to_anchor=(1.0, -0.02), fontsize=8, title_fontsize=9, frameon=False)

    ax.set_title('Destino principal das internações pediátricas, por município de residência\n'
                 'Paraná, 2024–2025', fontsize=12, pad=10)
    fig.text(0.01, 0.01,
             'Fonte: SIH/SUS (internações de 0 a 16 anos, 2024–2025); IBGE. Elaboração própria. SIRGAS 2000 / UTM 22S.\n'
             'Linhas retas entre sedes municipais, sem relação com rotas viárias. Cada município mostra apenas o seu destino '
             'mais frequente fora do próprio município.\nContornos escuros: Regiões de Saúde.',
             fontsize=7, color='#444444', va='bottom')
    fig.subplots_adjust(left=0.01, right=0.99, top=0.93, bottom=0.17)

    for ext, kw in [('png', {'dpi': 300}), ('pdf', {})]:
        fig.savefig(DIR_SAIDA / f'fig_fluxo_principal.{ext}', facecolor='white', **kw)
    print('Destinos coloridos:', top)
    print(f'Figura salva em {DIR_SAIDA}/fig_fluxo_principal.png e .pdf')


if __name__ == '__main__':
    main()
