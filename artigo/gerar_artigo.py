"""
Gera o artigo em PDF (artigo/artigo_BD2.pdf) com a seção 3 (solução do problema GIS) e o anexo de SQL.

Executar a partir da raiz do projeto, depois de gis/acessibilidade_postgis.py e gis/figuras_acessibilidade.py:
    python artigo/gerar_artigo.py

Todos os números do texto vêm dos CSVs de gis/saida/ (nada é digitado à mão), e o anexo
reproduz os arquivos de gis/sql/ sem alteração.
"""

import textwrap
from pathlib import Path

import pandas as pd
from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont as RLFont
from reportlab.platypus import (Image, KeepTogether, PageBreak, Paragraph, Preformatted,
                                SimpleDocTemplate, Spacer, Table, TableStyle)

RAIZ = Path(__file__).resolve().parent.parent
SAIDA = RAIZ / 'gis' / 'saida'
SQL = RAIZ / 'gis' / 'sql'
FONTES = Path(__file__).resolve().parent / 'fontes'
PDF = Path(__file__).resolve().parent / 'artigo_BD2.pdf'
URW = Path('/usr/share/fonts/opentype/urw-base35')


# ============================================================
# Fontes: Nimbus Roman (equivalente métrico do Times, usada no modelo SBC original)
# ============================================================

def otf_para_ttf(origem, destino):
    """O ReportLab só lê TTF; converte as curvas CFF (OTF) para quadráticas."""
    from fontTools.pens.cu2quPen import Cu2QuPen
    from fontTools.pens.ttGlyphPen import TTGlyphPen
    from fontTools.ttLib import TTFont, newTable
    f = TTFont(origem)
    gs, ordem = f.getGlyphSet(), f.getGlyphOrder()
    glifos = {}
    for nome in ordem:
        pen = TTGlyphPen(gs)
        gs[nome].draw(Cu2QuPen(pen, 1.0, reverse_direction=True))
        glifos[nome] = pen.glyph()
    f['loca'] = newTable('loca')
    t = f['glyf'] = newTable('glyf')
    t.glyphOrder, t.glyphs = ordem, glifos
    del f['CFF ']
    f.sfntVersion = '\x00\x01\x00\x00'
    if 'VORG' in f:
        del f['VORG']
    m = f['maxp'] = newTable('maxp')
    m.tableVersion = 0x00010000
    for a in ('maxZones', 'maxTwilightPoints', 'maxStorage', 'maxFunctionDefs', 'maxInstructionDefs',
              'maxStackElements', 'maxSizeOfInstructions', 'maxComponentElements'):
        setattr(m, a, 0)
    m.maxZones, m.maxPoints, m.maxContours = 1, 0, 0
    m.maxCompositePoints = m.maxCompositeContours = m.maxComponentDepth = 0
    m.numGlyphs = len(ordem)
    f['head'].glyphDataFormat = 0
    f['post'].formatType = 2.0
    f['post'].extraNames, f['post'].mapping, f['post'].glyphOrder = [], {}, ordem
    f.save(destino)


def registrar_fontes():
    FONTES.mkdir(exist_ok=True)
    mapa = {'NR': 'NimbusRoman-Regular', 'NR-B': 'NimbusRoman-Bold', 'NR-I': 'NimbusRoman-Italic',
            'NR-BI': 'NimbusRoman-BoldItalic', 'NM': 'NimbusMonoPS-Regular', 'NM-B': 'NimbusMonoPS-Bold'}
    for nome, arq in mapa.items():
        ttf = FONTES / f'{arq}.ttf'
        if not ttf.exists():
            otf_para_ttf(URW / f'{arq}.otf', ttf)
        pdfmetrics.registerFont(RLFont(nome, str(ttf)))
    pdfmetrics.registerFontFamily('NR', normal='NR', bold='NR-B', italic='NR-I', boldItalic='NR-BI')
    pdfmetrics.registerFontFamily('NM', normal='NM', bold='NM-B', italic='NM', boldItalic='NM-B')


# ============================================================
# Estilos (modelo SBC: A4, Times 12 pt no original; aqui 11 pt para caber a seção 3)
# ============================================================

def estilos():
    base = dict(fontName='NR', fontSize=11, leading=13.6, alignment=TA_JUSTIFY)
    s = {
        'corpo': ParagraphStyle('corpo', firstLineIndent=1.0 * cm, spaceAfter=4, **base),
        'corpo_sem': ParagraphStyle('corpo_sem', spaceAfter=4, **base),
        'lista_esq': ParagraphStyle('lista_esq', spaceAfter=4, **{**base, 'alignment': TA_LEFT}),
        'corpo_esq': ParagraphStyle('corpo_esq', spaceAfter=4, firstLineIndent=1.0 * cm, **{**base, 'alignment': TA_LEFT}),
        'titulo': ParagraphStyle('titulo', fontName='NR-B', fontSize=16, leading=19, alignment=TA_CENTER, spaceAfter=10),
        'autores': ParagraphStyle('autores', fontName='NR-B', fontSize=12, leading=14.5, alignment=TA_CENTER, spaceAfter=8),
        'afil': ParagraphStyle('afil', fontName='NR', fontSize=11, leading=13, alignment=TA_CENTER, spaceAfter=10),
        'resumo': ParagraphStyle('resumo', fontName='NR-I', fontSize=10.5, leading=12.6, alignment=TA_JUSTIFY,
                                 leftIndent=1.2 * cm, rightIndent=1.2 * cm, spaceAfter=7),
        'h1': ParagraphStyle('h1', fontName='NR-B', fontSize=13, leading=16, spaceBefore=10, spaceAfter=5, keepWithNext=1),
        'h2': ParagraphStyle('h2', fontName='NR-B', fontSize=11.5, leading=14, spaceBefore=7, spaceAfter=3, keepWithNext=1),
        'legenda': ParagraphStyle('legenda', fontName='NR', fontSize=9.5, leading=11.5, alignment=TA_CENTER,
                                  spaceBefore=3, spaceAfter=9),
        'celula': ParagraphStyle('celula', fontName='NR', fontSize=8.6, leading=10.2, alignment=TA_LEFT),
        'celula_b': ParagraphStyle('celula_b', fontName='NR-B', fontSize=8.6, leading=10.2, alignment=TA_LEFT),
        'codigo': ParagraphStyle('codigo', fontName='NM', fontSize=6.4, leading=7.6, backColor=colors.HexColor('#f3f3f3'),
                                 borderPadding=(4, 4, 4, 4), spaceBefore=4, spaceAfter=8, leftIndent=4, rightIndent=4),
        'pseudo': ParagraphStyle('pseudo', fontName='NM', fontSize=7.3, leading=9, backColor=colors.HexColor('#f3f3f3'),
                                 borderPadding=(5, 5, 5, 5), spaceBefore=4, spaceAfter=9, leftIndent=5, rightIndent=5),
        'ref': ParagraphStyle('ref', fontName='NR', fontSize=10.5, leading=12.6, alignment=TA_LEFT, leftIndent=0.6 * cm,
                              firstLineIndent=-0.6 * cm, spaceAfter=3),
    }
    return s


def esc(t):
    return t.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def m(t):
    """Trecho em fonte monoespaçada (nomes de tabelas, funções)."""
    return f'<font name="NM" size="9.6">{esc(t)}</font>'


# ============================================================
# Números (lidos dos resultados)
# ============================================================

def num(v, c=1):
    return f'{v:,.{c}f}'.replace(',', 'X').replace('.', ',').replace('X', '.')


def pct(v, c=1):
    return num(v * 100, c) + '%'


def carregar():
    d = pd.read_csv(SAIDA / 'acess_05_municipios_sih.csv')
    g = pd.read_csv(SAIDA / 'acess_02_grupos_sql.csv').set_index('tem_hospital_no_municipio')
    sih = pd.read_csv(SAIDA / 'acess_06_sih_por_grupo.csv').set_index('tem_hospital')
    sp = pd.read_csv(SAIDA / 'acess_07_spearman.csv')
    funil = pd.read_csv(SAIDA / 'acess_00_funil_hospitais.csv')
    pea = pd.read_csv(SAIDA / 'acess_03_pearson_sql.csv').iloc[0]
    taxa = pd.read_csv(SAIDA / '05b_taxa_internacao_raca.csv').set_index('grupo')
    hosp = pd.read_csv(SAIDA / 'acess_04_hospitais.csv')
    return d, g, sih, sp, funil, pea, taxa, hosp


def nome_hospital(s):
    pequenas = {'de', 'da', 'do', 'das', 'dos', 'e'}
    pal = s.title().split(' ')
    return ' '.join(w.lower() if (i and w.lower() in pequenas) else w for i, w in enumerate(pal))


def rho(sp, x, y):
    r = sp[(sp['x'] == x) & (sp['y'] == y)].iloc[0]
    return r['rho'], r['p'], int(r['n'])


def fmt_rho(v):
    return num(v, 2).replace('-', '−')


def fmt_p(p):
    if p < 1e-3:
        e = f'{p:.0e}'.split('e')
        return f'p < 10<super>{int(e[1])}</super>' if p < 1e-4 else 'p < 0,001'
    return 'p = ' + num(p, 3)


# ============================================================
# Elementos
# ============================================================

def figura(arquivo, largura_cm, legenda, st):
    p = SAIDA / arquivo
    w, h = PILImage.open(p).size
    img = Image(str(p), width=largura_cm * cm, height=largura_cm * cm * h / w)
    return KeepTogether([img, Paragraph(legenda, st['legenda'])])


def tabela(linhas, larguras_cm, st, cabecalho=True, alinhar_dir=(), legenda=None):
    dados = []
    for i, lin in enumerate(linhas):
        dados.append([Paragraph(str(c), st['celula_b'] if (i == 0 and cabecalho) else st['celula']) for c in lin])
    t = Table(dados, colWidths=[w * cm for w in larguras_cm], repeatRows=1 if cabecalho else 0)
    estilo = [('LINEABOVE', (0, 0), (-1, 0), 0.9, colors.black), ('LINEBELOW', (0, -1), (-1, -1), 0.9, colors.black),
              ('VALIGN', (0, 0), (-1, -1), 'TOP'), ('TOPPADDING', (0, 0), (-1, -1), 2.2),
              ('BOTTOMPADDING', (0, 0), (-1, -1), 2.2), ('LEFTPADDING', (0, 0), (-1, -1), 3), ('RIGHTPADDING', (0, 0), (-1, -1), 3)]
    if cabecalho:
        estilo.append(('LINEBELOW', (0, 0), (-1, 0), 0.5, colors.black))
    t.setStyle(TableStyle(estilo))
    itens = [t]
    if legenda:
        itens.insert(0, Paragraph(legenda, st['legenda']))
    return KeepTogether(itens) if len(linhas) < 14 else itens


def quebrar(texto, largura=112):
    """Quebra linhas longas do SQL (só no PDF; os arquivos .sql não são alterados)."""
    saida = []
    for lin in texto.expandtabs(4).splitlines():
        if len(lin) <= largura:
            saida.append(lin)
            continue
        recuo = len(lin) - len(lin.lstrip()) + 4
        partes = textwrap.wrap(lin, largura, subsequent_indent=' ' * recuo, break_long_words=False)
        saida.extend(partes)
    return '\n'.join(saida)


def rodape(canvas, doc):
    canvas.saveState()
    canvas.setFont('NR', 10)
    canvas.drawCentredString(A4[0] / 2, 1.3 * cm, str(doc.page))
    canvas.restoreState()


# ============================================================
# Conteúdo
# ============================================================

def montar():
    st = estilos()
    d, g, sih, sp, funil, pea, taxa, hosp = carregar()
    P = lambda t, e='corpo': Paragraph(t, st[e])
    H1 = lambda t: Paragraph(t, st['h1'])
    H2 = lambda t: Paragraph(t, st['h2'])

    n_mun = len(d)
    n_sem = int((d['n_hosp_municipio'] == 0).sum())
    n_com = n_mun - n_sem
    n_sem30 = int((d['n_hosp_30km'] == 0).sum())
    nomes_sem30 = ', '.join(d.loc[d['n_hosp_30km'] == 0, 'nome'].sort_values())
    n_hosp = int(funil.loc[funil['ordem'] == 5, 'n'].iloc[0])
    r_pbf, p_pbf, n_pbf = rho(sp, 'dist_hosp_km', 'pct_bf_inscritos')
    r_ppi, p_ppi, _ = rho(sp, 'dist_hosp_km', 'pct_ppi_cadunico')
    r_pob, p_pob, _ = rho(sp, 'dist_hosp_km', 'pct_bf_pobreza')
    r_n30, p_n30, _ = rho(sp, 'n_hosp_30km', 'pct_bf_inscritos')
    r_n30p, p_n30p, _ = rho(sp, 'n_hosp_30km', 'pct_ppi_cadunico')
    r_saida, p_saida, n_saida = rho(sp, 'dist_hosp_km', 'pct_fora_municipio')
    r_taxa, p_taxa, _ = rho(sp, 'dist_hosp_km', 'taxa_int_1000_criancas_ano')
    r_inf, p_inf, _ = rho(sp, 'dist_hosp_infantil_km', 'taxa_int_1000_criancas_ano')
    inf_med, inf_max = d['dist_hosp_infantil_km'].median(), d['dist_hosp_infantil_km'].max()
    n_inf100 = int((d['dist_hosp_infantil_km'] > 100).sum())
    sem, com = g.loc[False], g.loc[True]
    s_sem, s_com = sih.loc[False], sih.loc[True]
    n_testes = len(sp)
    from scipy.stats import mannwhitneyu
    gsem, gcom = d[d['n_hosp_municipio'] == 0], d[d['n_hosp_municipio'] > 0]
    p_mw = {c: mannwhitneyu(gsem[c], gcom[c]).pvalue for c in ('pct_bf_inscritos', 'pct_ppi_cadunico', 'pct_bf_pobreza')}

    E = []
    # ---------------- cabeçalho ----------------
    E += [Spacer(1, 0.3 * cm),
          P('Associação entre vulnerabilidade socioeconômica<br/>e internações pediátricas no Paraná', 'titulo'),
          P('Julia Mariano Torres da Silva, Giulia de Souza Leite', 'autores'),
          P('Departamento de Informática – Universidade Tecnológica Federal do Paraná (UTFPR)<br/>Curitiba – PR – Brasil', 'afil'),
          P('<b>Abstract.</b> This article describes the structuring and integration of data from three government databases: '
            'the geographic distribution of the Bolsa Família Program (PBF) in Paraná, records of child labor and its geographic '
            'distribution in Paraná, and hospital admission data for the same state. The general characteristics of the entire '
            'process—data detection, cleaning, integration, and analysis—will be presented, along with questions raised to guide '
            'potential future analyses. As a GIS problem, we measure in PostGIS the spatial accessibility of the 399 municipalities '
            'to hospitals and relate it to socioeconomic vulnerability and to the racial composition of the Cadastro Único.', 'resumo'),
          P('<b>Resumo.</b> Este artigo descreve a estruturação e integração de dados de três bases governamentais: a distribuição '
            'etária e geográfica do programa Bolsa Família (PBF) pelo Paraná, os registros de trabalho infantil e sua distribuição '
            'geográfica pelo Paraná, e os dados de internação hospitalar no mesmo estado. Serão apresentadas as características gerais '
            'de todo o processo de extração, limpeza, integração e análise dos dados, bem como questões levantadas para orientar '
            'possíveis análises futuras. Como problema GIS, mede-se em PostGIS a acessibilidade espacial a hospitais dos 399 municípios '
            'e relaciona-se com a vulnerabilidade socioeconômica e a composição racial dos inscritos no Cadastro Único.', 'resumo')]

    # ---------------- 1. Introdução ----------------
    E += [H1('1. Introdução'),
          P('O conjunto de dados utilizado neste estudo veio do cruzamento de dados de hospitais do Paraná, oferecidos pelo banco de '
            'dados postgiscwb, do servidor BIGSEA, da UTFPR, com registros públicos do CadÚnico (programa “Cadastro Único” do Governo '
            'Federal, requisito para solicitar benefícios como Bolsa Família, tarifa social de energia elétrica, benefício de prestação '
            'continuada (BPC), etc.) e registros de saúde pública disponibilizados pelo SUS (Sistema de Informações Hospitalares do SUS '
            '(SIH/SUS)).'),
          P('A consolidação de todos os dados foi organizada em 4 tabelas e centenas de milhares de tuplas, que cobrem dados de todos '
            'os 399 municípios do Paraná ao longo das duas últimas décadas. Todos os dados, com exceção da base 3 (da próxima seção), '
            'estão disponíveis no schema ‘public’ do banco ‘postgiscwb’, do servidor ‘BIGSEA’ da UFPR.'),
          P('Este trabalho desenvolve, sobre essas bases, um problema geográfico: <b>quão acessíveis são os hospitais para cada município '
            'do Paraná e essa acessibilidade é pior onde a vulnerabilidade social é maior?</b> A seção 2 descreve os dados e os problemas '
            'enfrentados; a seção 3 apresenta a pergunta, a metodologia, o algoritmo, a solução e a visualização, todos executados no '
            'PostGIS; a seção 4 lista perguntas para trabalhos futuros. Os comandos SQL utilizados estão no Anexo A.')]

    # ---------------- 2. Dicionário ----------------
    E += [H1('2. Dicionário de dados e atributos'),
          P('Os dados estão divididos em quatro grupos de tabelas:', 'lista_esq'),
          P('1) A tabela ' + m('bd2_2556553') + ', que faz a junção dos dados extraídos do CadÚnico (“Pessoas cadastradas no CadÚnico por '
            'raça e cor”, “Pessoas inscritas no Programa Bolsa Família do Sexo Feminino por Faixa Etária”, “Pessoas inscritas no Programa '
            'Bolsa Família do Sexo Masculino por Faixa Etária”, “Famílias inscritas no CadÚnico com pessoas em situação de trabalho '
            'infantil”) com dados geográficos disponibilizados pelo IBGE das coordenadas centrais dos municípios brasileiros. Todos os '
            'dados do CadÚnico foram cruzados entre si utilizando-se como chave a combinação de município e data (mês/ano). Possui 40 '
            'colunas: ' + m('Municipio') + ', ' + m('Data') + ', as quantidades de pessoas beneficiárias do PBF por faixa de renda, '
            'por sexo e faixa etária, o número de inscritos por raça/cor e as famílias e pessoas do PBF em situação de trabalho '
            'infantil. Contém 67.431 tuplas (399 municípios, 01/2013 a 12/2025).', 'lista_esq'),
          P('2) A tabela ' + m('bd2_2556553_trab_infantil_pbf') + ' mapeia a incidência declarada de trabalho infantil pelo Paraná. As '
            'colunas ' + m('qtd_familias_bf_trab_infantil') + ' e ' + m('qtd_pessoas_bf_trab_infantil') + ' mapeiam, respectivamente, o '
            'número absoluto de famílias no programa com registro de trabalho infantil e a quantidade de indivíduos afetados.', 'lista_esq'),
          P('3) Base 3 (armazenada localmente pelas autoras): internações hospitalares infantis no Paraná (SIH/SUS), microdados de saúde '
            'filtrados para pacientes menores de 16 anos no Paraná. Contém as colunas ' + m('ano') + ', ' + m('mes') + ', ' + m('id_aih') +
            ' (identificação da autorização hospitalar), ' + m('especialidade_leito') + ', ' + m('cep_paciente') + ', ' + m('idade_paciente')
            + ', ' + m('sexo_paciente') + ', ' + m('raca_cor_paciente') + ', ' + m('etnia_paciente') + ', ' + m('grau_instrucao_paciente') +
            ', ' + m('tipo_contraceptivo_principal') + ', ' + m('municipio_paciente') + ', ' + m('municipio_estabelecimento') + ' (município '
            'do hospital em que foi atendido), ' + m('subcategoria') + ' (código da categoria de diagnóstico) e ' + m('diagnostico') +
            '. Para o período analisado (2024–2025) há 70.747 AIHs.', 'lista_esq'),
          P('4) Tabelas geográficas já existentes no banco, usadas na seção 3: os polígonos municipais ' + m('bd2_ricardo_divisa_municipio_parana')
            + ' e os estabelecimentos de saúde do Paraná ' + m('saude."saude_parana_CRM"') + '.', 'lista_esq'),
          H2('2.1 Problemas enfrentados'),
          P('Os problemas enfrentados foram principalmente quanto à procura dos dados (especialmente dados de saúde pública) e '
            'cruzamento de códigos dos dados originais com tabelas de tradução (como, por exemplo, a coluna ' + m('id_municipio') +
            ' da tabela original do SUS, que precisou ser cruzada com um arquivo específico do IBGE, ' + m('id_municipio_6') + ', uma das '
            'variações de identificação dos municípios). Ao desenvolver a solução GIS, a inspeção do banco revelou problemas adicionais, '
            'tratados no SQL e discutidos na seção 3.7:'),
          P('(i) as tabelas ' + m('limites_legais.municipiosbr') + ' e ' + m('limites_legais.divisa_municipio_parana') + ' estão vazias, e ' +
            m('saude.hospital') + ' cobre apenas Curitiba (75 pontos); (ii) a coluna ' + m('geom') + ' dos polígonos municipais declara '
            'SRID 4326 (graus), mas as coordenadas estão em metros (x de 136 mil a 800 mil), o que faz ' + m('ST_Transform') + ' falhar; '
            '(iii) cada estabelecimento aparece duplicado em ' + m('saude_parana_CRM') + ' (956 registros para 478 ' + m('id_estab') + '); '
            '(iv) dois hospitais têm coordenadas fora do Paraná (longitude ≈ −43°); (v) cinco municípios têm grafias diferentes entre a '
            'malha e o CadÚnico (Pinhal de/do São Bento, Munhoz de Mello/Melo, Antonio/Antônio, Nova Cantú/Cantu).', 'corpo_esq')]

    # ---------------- 3. Desenvolvimento ----------------
    E += [H1('3. Desenvolvimento: solução do problema GIS'),
          H2('3.1 Pergunta a ser respondida'),
          P('<b>Pergunta central.</b> Qual é a acessibilidade espacial a hospitais de cada município do Paraná e ela é pior nos municípios '
            'mais vulneráveis (maior proporção de inscritos no CadÚnico atendidos pelo Bolsa Família) ou com maior proporção de pessoas '
            'pretas, pardas e indígenas (PPI)?'),
          P('A pergunta se decompõe em quatro, cada uma correlacionando a tabela ' + m('bd2_2556553') + ' ou os dados de saúde com pelo menos '
            'outra tabela do banco e usando funções GIS distintas (Tabela 1). As perguntas Q1 a Q3 são respondidas inteiramente em SQL no '
            'PostGIS; Q4 valida o resultado com o SIH, que permanece local.'),
          tabela([['', 'Pergunta', 'Tabelas correlacionadas', 'Funções GIS'],
                  ['Q1', 'Quais municípios não têm hospital no território e a que distância fica o hospital mais próximo?',
                   m('saude_parana_CRM') + ' × ' + m('bd2_ricardo_divisa…'), m('ST_SetSRID') + ', ' + m('ST_Transform') + ', ' + m('ST_PointOnSurface') +
                   ', ' + m('ST_Within') + ', operador KNN ' + m('<->') + ', ' + m('ST_Distance') + ', ' + m('ST_MakeLine')],
                  ['Q2', 'Que parcela do território está a até 30 km de algum hospital? Quantos hospitais há nesse raio?',
                   m('saude_parana_CRM') + ' × ' + m('bd2_ricardo_divisa…'), m('ST_DWithin') + ', ' + m('ST_Buffer') + ', ' + m('ST_Union') + ', ' +
                   m('ST_Intersection') + ', ' + m('ST_Area')],
                  ['Q3', 'A acessibilidade se associa à vulnerabilidade (PBF) e à composição racial (PPI) dos inscritos?',
                   m('bd2_2556553') + ' × resultado de Q1/Q2 (junção por nome)', m('unaccent') + ', agregações, ' + m('corr') + ' (Pearson)'],
                  ['Q4', 'Onde não há hospital no município, as crianças internadas saem dele? (validação)',
                   'resultado de Q1 × SIH (local)', 'junção por código IBGE; Spearman em Python']],
                 [0.8, 6.2, 4.3, 4.7], st, legenda='<b>Tabela 1.</b> Perguntas, tabelas correlacionadas e funções GIS utilizadas.'),
          Spacer(1, 3),
          P('<b>Hipótese.</b> Municípios com maior proporção de inscritos atendidos pelo PBF e com maior proporção de PPI estariam mais '
            'distantes de hospitais e teriam menos hospitais em um raio de 30 km (hipótese nula: ausência de associação monotônica).')]

    # ---- 3.2 Dados
    E += [H2('3.2 Dados utilizados'),
          tabela([['Tabela (schema)', 'Linhas', 'Geometria', 'Papel e colunas usadas'],
                  [m('bd2_2556553') + ' (public)', '67.431', '—', 'Vulnerabilidade: faixas de renda do PBF, inscritos por raça/cor; 2024–2025'],
                  [m('bd2_ricardo_divisa_municipio_parana') + ' (public)', '399', 'MULTIPOLYGON, SRID 4326 declarado (coordenadas em metros)',
                   'Polígonos municipais: ' + m('codibge') + ', ' + m('nome') + ', ' + m('geom')],
                  [m('saude_parana_CRM') + ' (saude)', '18.448', 'POINT, 4326', 'Estabelecimentos: ' + m('id_estab') + ', ' + m('nome') + ', ' +
                   m('cidade') + ', ' + m('lat') + ', ' + m('lng') + ', ' + m('geom') + ' (956 registros com nome de hospital)'],
                  ['SIH/SUS (local)', '70.747', '—', 'Validação (Q4): município do paciente e do hospital; 2024–2025']],
                 [4.5, 1.4, 3.8, 6.3], st, legenda='<b>Tabela 2.</b> Dados utilizados na seção 3.'),
          P('A tabela de estabelecimentos não possui coluna de tipo; um hospital é, portanto, definido pelo nome. Dos 956 registros cujo nome '
            'contém “hospital”, “santa casa” ou “maternidade”, o funil da Tabela 3 resulta em <b>' + str(n_hosp) + ' hospitais</b> '
            'únicos e com coordenadas válidas. Apenas quatro têm “infantil” no nome (Pequeno Príncipe, em Curitiba; Waldemar Monastier, em '
            'Campo Largo; Sagrada Família, em Londrina; Materno Infantil, em Apucarana) e formam o subconjunto “hospital infantil”.'),
          tabela([['Etapa', 'n'] ] + [[r['etapa'], num(r['n'], 0)] for _, r in funil.iterrows()],
                 [10.5, 2.0], st, legenda='<b>Tabela 3.</b> Seleção dos hospitais em ' + m('saude_parana_CRM') + '.')]

    # ---- 3.3 Metodologia
    E += [H2('3.3 Metodologia'),
          P('<b>Sistema de referência.</b> Todas as medidas em metros usam SAD 69 / UTM 22S (EPSG:29192). Como o SRID declarado nos polígonos '
            'é inconsistente com as coordenadas, o rótulo foi corrigido com ' + m('ST_SetSRID') + ' (e não reprojetado), e os hospitais '
            '(graus, WGS 84) foram projetados com ' + m('ST_Transform') + '. A escolha entre EPSG:29192 e EPSG:31982 (SIRGAS 2000) foi testada em uma versão '
            'preliminar com 476 candidatos a hospital: os dois produziram o mesmo resultado na junção espacial (475 caem em algum município; 468 coincidem '
            'com a coluna ' + m('cidade') + '). No conjunto final (EPSG:29192), 471 dos 472 hospitais caem em algum município e 464 coincidem com ' + m('cidade') + '. '
            'A diferença entre os datums é da ordem de dezenas de metros, desprezível na escala municipal.'),
          P('<b>Indicadores de acessibilidade</b> (Q1 e Q2), calculados para cada município m, com sede s<sub>m</sub> = ' + m('ST_PointOnSurface') +
            '(polígono), que é garantidamente interna ao polígono (o centroide pode cair fora de municípios côncavos): ' +
            m('n_hosp_municipio') + ', número de hospitais dentro do polígono (' + m('ST_Within') + '); ' + m('dist_hosp_km') + ', distância em linha '
            'reta da sede ao hospital mais próximo (' + m('<->') + ' e ' + m('ST_Distance') + '); ' + m('n_hosp_30km') + ', hospitais a até 30 km da sede '
            '(' + m('ST_DWithin') + '); ' + m('pct_area_ate_30km') + ', fração da área do município a até 30 km de algum hospital (união dos círculos de 30 km '
            'intersectada com o polígono); ' + m('dist_hosp_infantil_km') + ', análoga à primeira para o subconjunto infantil. O raio de 30 km é uma '
            'escolha de ordem de grandeza para o deslocamento regional; não foi calibrado nem se fez análise de sensibilidade.'),
          P('<b>Indicadores de vulnerabilidade</b> (Q3), a partir de ' + m('bd2_2556553') + ', razões calculadas mês a mês e depois '
            'promediadas em 2024–2025 (somente meses com as colunas de raça/cor, ou seja, excluindo abril de 2025): ' + m('pct_bf_inscritos') + ' = pessoas '
            'beneficiárias do PBF ÷ inscritos no CadÚnico, em que PBF = pobreza + baixa renda + acima de ½ salário mínimo (cobertura de 100% '
            'dos meses; a soma por faixa etária difere em média 0,1%) e inscritos = soma das seis categorias de raça/cor; ' + m('pct_ppi_cadunico') + ' '
            '= (pretos + pardos + indígenas) ÷ inscritos; ' + m('pct_bf_pobreza') + ' = beneficiários em faixa de pobreza ÷ beneficiários do PBF. A '
            'junção com a malha é feita pelo nome normalizado (' + m('UPPER(unaccent(...))') + ', sem apóstrofos), com duas correções manuais.'),
          P('<b>Estatística.</b> Correlação de Pearson calculada no SQL (' + m('corr') + ') e correlação de Spearman, robusta a valores extremos, '
            'calculada em Python, com p-valor. Foram feitos ' + str(n_testes) + ' testes; usa-se o limiar de Bonferroni 0,05/' + str(n_testes) +
            ' = 0,0025. Para a validação com o SIH (Q4), só entram municípios com pelo menos 30 internações (n = ' + str(n_saida) + '). A '
            'análise é ecológica (unidade: município) e não permite inferências sobre indivíduos.')]

    # ---- 3.4 Algoritmo
    pseudo = '''Entrada: M (399 polígonos), E (estabelecimentos), C (bd2_2556553)  ->  Saída: tabela A e camadas
1.  H <- {e em E : nome casa "hospital|santa casa|maternidade"
                   e nome não casa "hospital-dia|estética|odonto"
                   e (lng, lat) dentro do retângulo do PR}
    H <- um registro por id_estab;  geom(H) <- ST_Transform(geom, 29192)
2.  para cada município m em M:
        poly(m) <- ST_SetSRID(geom, 29192)
        sede(m) <- ST_PointOnSurface(poly(m))
3.  cob <- ST_Union( ST_Buffer(geom(h), 30000) para todo h em H )
4.  para cada município m:
        n_mun(m)  <- |{h : ST_Within(h, poly(m))}|                  # junção espacial
        n_30(m)   <- |{h : ST_DWithin(h, sede(m), 30000)}|
        h*(m)     <- argmin_h  sede(m) <-> geom(h)                  # vizinho mais próximo
        dist(m)   <- ST_Distance(sede(m), geom(h*)) / 1000
        linha(m)  <- ST_MakeLine(sede(m), geom(h*))
        hi*(m)    <- idem, restrito aos hospitais infantis
        area(m)   <- ST_Area(ST_Intersection(poly(m), cob)) / ST_Area(poly(m))
5.  para cada nome normalizado k em C (2024-2025, meses completos):
        PBF(k), PPI(k), pobreza(k) <- médias das razões mensais
6.  A <- junção de (m, 4) com (k, 5) por nome normalizado (+ 2 correções)
7.  Pearson em SQL;  Spearman e junção com o SIH em Python;  exportar GeoPackage'''
    E += [H2('3.4 Algoritmo'),
          P('A solução é uma única consulta SQL (passos 1 a 6 do pseudocódigo; Anexo A, consulta A.2), '
            'organizada em expressões de tabela comuns (CTEs). Os CTEs ' + m('hosp') + ' e ' + m('mun') + ' são '
            'materializados, para que a projeção seja calculada uma vez por geometria e não a cada par município × hospital. A Figura 1 resume o fluxo e o pseudocódigo detalha cada passo.'),
          P('<b>Complexidade.</b> Com n = ' + str(n_mun) + ' municípios e m = ' + str(n_hosp) + ' hospitais, a busca ingênua do vizinho mais próximo '
            'avalia n·m = ' + num(n_mun * n_hosp, 0) + ' distâncias. Com um índice GiST em ' + m('geom') + ', o operador ' + m('<->') + ' passa a '
            'custar O(log m) por município; a tabela de estabelecimentos não tem índice espacial, e a consulta completa (inclusive a união de ' +
            str(n_hosp) + ' círculos) leva entre 2 e 4 s, o que dispensa criá-lo. A junção ' + m('ST_Within') + ' filtra antes pela caixa '
            'envolvente (n·m comparações baratas) e só testa a geometria exata nos poucos pares candidatos. A conexão é somente leitura.'),
          Preformatted(pseudo, st['pseudo']),
          figura('fig_a1_algoritmo.png', 15.6, '<b>Figura 1.</b> Fluxo da solução: tabelas de entrada, etapas com as funções PostGIS e resultados.', st)]

    # ---- 3.5 Solução
    top = d.sort_values('dist_hosp_km', ascending=False).head(8)
    linhas_top = [['Município', 'Hospital mais próximo', 'km', 'Hosp. infantil (km)', 'PBF/inscritos']]
    for _, r in top.iterrows():
        linhas_top.append([r['nome'], nome_hospital(r['hosp_proximo']), num(r['dist_hosp_km'], 1),
                           num(r['dist_hosp_infantil_km'], 0), pct(r['pct_bf_inscritos'], 0)])
    E += [H2('3.5 Solução e resultados'),
          P('<b>Q1 e Q2.</b> Dos ' + str(n_mun) + ' municípios, <b>' + str(n_sem) + ' (' + pct(n_sem / n_mun, 0) + ') não têm nenhum hospital no '
            'território</b>; os outros ' + str(n_com) + ' reúnem os ' + str(int(d['n_hosp_municipio'].sum())) + ' hospitais localizados em polígonos (de 1 a ' +
            str(int(d['n_hosp_municipio'].max())) + ' por município). Mesmo assim, a acessibilidade física é alta: a distância da sede ao hospital mais '
            'próximo tem média de ' + num(d['dist_hosp_km'].mean()) + ' km (mediana ' + num(d['dist_hosp_km'].median()) + ' km; máximo ' +
            num(d['dist_hosp_km'].max()) + ' km) e, em média, ' + pct(d['pct_area_ate_30km'].mean()) + ' da área de cada município está a até 30 km de um '
            'hospital. Apenas ' + str(n_sem30) + ' municípios não têm hospital a 30 km da sede (' + nomes_sem30 + '; Figura 2b e Tabela 5).'),
          P('O quadro muda quando se consideram os quatro hospitais com “infantil” no nome: a mediana da distância é de ' + num(inf_med, 0) +
            ' km (máximo ' + num(inf_max, 0) + ' km) e ' + str(n_inf100) + ' municípios (' + pct(n_inf100 / n_mun, 0) + ') ficam a mais de 100 km de um. '
            'Esse número deve ser lido com cautela: hospitais gerais costumam ter leitos pediátricos sem “infantil” no nome, e a tabela de '
            'estabelecimentos não informa leitos.'),
          tabela(linhas_top, [3.4, 6.3, 1.3, 2.9, 2.1], st,
                 legenda='<b>Tabela 5.</b> Os oito municípios mais distantes de um hospital (sede até o hospital mais próximo, em linha reta).'),
          P('<b>Q3.</b> A Tabela 4 compara os dois grupos. Municípios sem hospital no território estão em média ' + num(sem['dist_media_km']) +
            ' km do hospital mais próximo, contra ' + num(com['dist_media_km']) + ' km nos demais, e têm ' + pct(sem['pct_area_ate_30km']) + ' (contra ' +
            pct(com['pct_area_ate_30km']) + ') da área a até 30 km. A proporção de inscritos atendidos pelo PBF é maior nos municípios sem hospital (' +
            pct(sem['pct_bf_inscritos']) + ' contra ' + pct(com['pct_bf_inscritos']) + '), mas a diferença é pequena e frágil (teste de Mann–Whitney, ' +
            fmt_p(p_mw['pct_bf_inscritos']) + ', que não resistiria à correção de Bonferroni); a proporção de PPI é praticamente igual (' +
            pct(sem['pct_ppi_cadunico']) + ' e ' + pct(com['pct_ppi_cadunico']) + '; ' + fmt_p(p_mw['pct_ppi_cadunico']) + ').'),
          tabela([['Indicador', 'Sem hospital', 'Com hospital'],
                  ['Municípios', str(int(sem['municipios'])), str(int(com['municipios']))],
                  ['Distância ao hospital mais próximo: média (mediana), km', f"{num(sem['dist_media_km'])} ({num(sem['dist_mediana_km'])})",
                   f"{num(com['dist_media_km'])} ({num(com['dist_mediana_km'])})"],
                  ['Área do município a até 30 km de um hospital', pct(sem['pct_area_ate_30km']), pct(com['pct_area_ate_30km'])],
                  ['PBF ÷ inscritos no CadÚnico (média dos municípios)', pct(sem['pct_bf_inscritos']), pct(com['pct_bf_inscritos'])],
                  ['PPI ÷ inscritos no CadÚnico (média dos municípios)', pct(sem['pct_ppi_cadunico']), pct(com['pct_ppi_cadunico'])],
                  ['Beneficiários em pobreza ÷ beneficiários do PBF', pct(sem['pct_bf_pobreza']), pct(com['pct_bf_pobreza'])],
                  ['<b>SIH:</b> internações pediátricas 2024–2025', num(s_sem['internacoes'], 0), num(s_com['internacoes'], 0)],
                  ['<b>SIH:</b> % das internações fora do município', pct(s_sem['pct_internacoes_fora']), pct(s_com['pct_internacoes_fora'])],
                  ['<b>SIH:</b> municípios em que 100% saem do município', str(int(s_sem['mun_100_por_cento'])), str(int(s_com['mun_100_por_cento']))]],
                 [9.4, 3.2, 3.2], st,
                 legenda='<b>Tabela 4.</b> Municípios com e sem hospital no território: indicadores do PostGIS (consultas 04) e do SIH (local).'),
          P('As correlações (Figura 3c) mostram associações de intensidade pequena a moderada. A distância ao hospital mais próximo '
            'correlaciona-se positivamente com a proporção de inscritos atendidos pelo PBF (Spearman ρ = ' + fmt_rho(r_pbf) + ', ' + fmt_p(p_pbf) +
            ', n = ' + str(n_pbf) + ') e com a proporção em faixa de pobreza (ρ = ' + fmt_rho(r_pob) + '), e a associação mais forte é com o número de '
            'hospitais em 30 km (ρ = ' + fmt_rho(r_n30) + '): onde a vulnerabilidade é maior há menos hospitais por perto. Já a proporção de PPI '
            'tem sinal oposto (ρ = ' + fmt_rho(r_ppi) + ' com a distância e ρ = ' + fmt_rho(r_n30p) + ' com o número de hospitais em 30 km): municípios com '
            'mais PPI tendem a estar mais perto de hospitais, o que contraria a hipótese. A correlação de Pearson do SQL concorda em sinal '
            '(distância × PBF: ' + num(pea['dist_x_pbf'], 2).replace('-', '−') + '; distância × PPI: ' + num(pea['dist_x_ppi'], 2).replace('-', '−') + '). Como ρ² é menor que 0,15 '
            'em todos os casos, a acessibilidade física não é um forte discriminante da vulnerabilidade.'),
          P('<b>Q4 (validação com o SIH).</b> A ausência de hospital no município tem efeito claro e esperado: nos ' + str(n_sem) +
            ' municípios sem hospital, <b>' + pct(s_sem['pct_internacoes_fora']) + '</b> das internações pediátricas ocorrem em outro município (em ' +
            str(int(s_sem['mun_100_por_cento'])) + ' deles, todas); nos ' + str(n_com) + ' com hospital, ainda assim ' + pct(s_com['pct_internacoes_fora']) +
            ' das internações saem (em ' + str(int(s_com['mun_100_por_cento'])) + ' deles, todas). A distância ao hospital mais próximo correlaciona-se com a '
            'saída do município (ρ = ' + fmt_rho(r_saida) + ', n = ' + str(n_saida) + ') mas não com a taxa de internação (ρ = ' + fmt_rho(r_taxa) +
            ', ' + fmt_p(p_taxa) + '), e a distância ao hospital infantil tem associação fraca com ela (ρ = ' + fmt_rho(r_inf) + '). Ou seja, ter um hospital '
            'no território é necessário, mas não suficiente: muitos hospitais não internam crianças.'),
          P('Em análise complementar (fora do escopo desta seção), a taxa de internação pediátrica é de ' + num(taxa.loc['PPI', 'taxa_1000_criancas_ano']) +
            ' por mil crianças PPI contra ' + num(taxa.loc['Branca', 'taxa_1000_criancas_ano']) + ' por mil crianças brancas. Como a proporção de PPI '
            'não está associada a pior acessibilidade física, a diferença não é explicada por distância; os dados não permitem separar barreiras '
            'de acesso não espaciais de sub-registro de raça/cor no SIH, preenchida pelo hospital (e autodeclarada no Censo e no CadÚnico).')]

    # ---- 3.6 Visualização
    E += [H2('3.6 Visualização'),
          P('Os resultados foram exportados do PostGIS para o GeoPackage ' + m('acessibilidade_hospitalar_pr.gpkg') + ' (EPSG:29192), com as '
            'camadas ' + m('municipios_acesso') + ' (polígonos e indicadores), ' + m('hospitais') + ' (pontos), ' + m('ligacao_hospital_proximo') +
            ' (linhas sede–hospital, apenas para municípios sem hospital) e ' + m('cobertura_30km') + ' (união dos círculos). No QGIS, a camada de '
            'municípios recebe simbologia graduada (campo ' + m('dist_hosp_km') + ', paleta sequencial) e as demais são empilhadas por cima '
            '(polígonos, linhas, pontos); filtros por expressão, como ' + m('"n_hosp_municipio" = 0') + ', destacam os municípios sem hospital. '
            'As figuras do artigo reproduzem esse estilo em Python para garantir reprodutibilidade.', 'corpo_esq'),
          figura('fig_a2_mapas.png', 16, '<b>Figura 2.</b> (a) Distância da sede ao hospital mais próximo e hospitais; estrelas: hospitais com “infantil” no nome. '
                 '(b) Cobertura de 30 km (azul), municípios sem hospital no território (laranja) e sem hospital em 30 km da sede (vermelho).', st),
          figura('fig_a3_relacoes.png', 16, '<b>Figura 3.</b> (a) Saída do município para internar, no SIH, segundo a presença de hospital; (b) distância ao hospital '
                 'mais próximo e proporção de inscritos atendidos pelo PBF; (c) correlações de Spearman (* p &lt; 0,0025).', st),
          figura('fig_fluxo_principal.png', 12.6, '<b>Figura 4.</b> Complementar: destino principal das internações pediátricas de cada município (SIH, 2024–2025). Cada linha '
                 'liga a sede do município ao hospital que mais recebe suas crianças; a cor indica o destino.', st)]

    # ---- 3.7 Discussão
    E += [H2('3.7 Discussão e limitações'),
          P('A solução responde à pergunta central com um “sim, mas pouco”: municípios com mais inscritos atendidos pelo PBF estão, em média, um pouco mais longe de hospitais '
            'e têm menos hospitais por perto, enquanto a proporção de PPI segue o sentido oposto; a distância física, porém, é baixa em todo o estado e as associações são fracas. O resultado mais robusto não vem do '
            'banco geográfico e sim do cruzamento com o SIH (Q4): a presença de um hospital no município praticamente decide se a criança é internada '
            'lá, e mesmo com hospital a saída é comum, indicando que a restrição relevante é a disponibilidade de atendimento pediátrico, não a '
            'proximidade de um estabelecimento qualquer.'),
          P('<b>Limitações.</b> (1) Hospital é definido pelo nome, sem tipo nem leitos; hospitais gerais com ala pediátrica e hospitais sem internação '
            'podem estar mal classificados. (2) Distâncias são em linha reta entre a sede (ponto interno ao polígono) e o hospital, não rotas viárias; a '
            'extensão ' + m('pgRouting') + ' está instalada no banco e permitiria o tempo de viagem. (3) O raio de 30 km é arbitrário e não foi testado. '
            '(4) O SRID da malha municipal foi inferido (29192 e 31982 dão o mesmo resultado). (5) O PBF é medido em relação aos inscritos no '
            'CadÚnico, não à população, e a razão entre as somas por renda e por faixa etária varia de 0,92 a 1,13 entre municípios (junho de 2025). (6) A análise é ecológica e os '
            + str(n_testes) + ' testes exigem correção de múltiplas comparações (Bonferroni); correlações com p ≈ 0,02, como ρ = −0,11 entre cobertura '
            'e pobreza, não resistem a ela. (7) A distância a hospitais infantis é uma medida estreita (apenas quatro estabelecimentos).')]

    # ---------------- 4. Perguntas futuras ----------------
    E += [H1('4. Perguntas para trabalhos futuros'),
          P('Das perguntas levantadas inicialmente, a solução da seção 3 responde parcialmente à 3 (renda, via PBF) e à 4 (cor, via PPI); as demais permanecem abertas:', 'corpo_sem'),
          P('1) Como se distribui geograficamente crianças em situação de trabalho infantil no Paraná?<br/>'
            '2) Houve alguma mudança em relação à distribuição de crianças em situação de trabalho infantil depois da implementação do programa Bolsa Família no Paraná?<br/>'
            '3) Qual a proporção e distribuição geográfica de internações infantis no Paraná segmentadas por renda?<br/>'
            '4) Qual a proporção e distribuição geográfica de internações infantis no Paraná segmentadas por cor?<br/>'
            '5) Qual a proporção e distribuição geográfica de internações infantis no Paraná segmentadas por sexo?<br/>'
            '6) Qual a evolução do perfil etário de pessoas beneficiárias do Bolsa Família comparativamente às décadas desde que foi implementado? Há segmentação de gênero?', 'corpo_sem'),
          P('Novas perguntas que a solução sugere: (7) o tempo de viagem por rotas (' + m('pgRouting') + ') altera o quadro obtido com distâncias em linha reta? '
            '(8) Existem agrupamentos espaciais significativos (Moran bivariado local, Anselin, 1995) entre vulnerabilidade e distância a hospitais? '
            '(9) Que capacidade pediátrica (leitos) falta nos municípios com hospital em que 100% das crianças saem?')]

    # ---------------- Referências ----------------
    E += [H1('Referências'),
          P('Anselin, L. (1995). Local indicators of spatial association – LISA. <i>Geographical Analysis</i>, 27(2), 93–115.', 'ref'),
          P('Brasil. Ministério da Cidadania / MDS. <i>Cadastro Único e Programa Bolsa Família: dados do VIS DATA 3 (SAGICAD)</i>. Dados abertos.', 'ref'),
          P('Brasil. Ministério da Saúde. <i>Sistema de Informações Hospitalares do SUS (SIH/SUS)</i>. DATASUS.', 'ref'),
          P('IBGE. <i>Censo Demográfico 2022</i>. Sistema IBGE de Recuperação Automática (SIDRA), tabela 9606.', 'ref'),
          P('Penchansky, R.; Thomas, J. W. (1981). The concept of access: definition and relationship to consumer satisfaction. <i>Medical Care</i>, 19(2), 127–140.', 'ref'),
          P('PostGIS Project. <i>PostGIS 3.5 Manual</i>. https://postgis.net/documentation/', 'ref'),
          P('QGIS Development Team. <i>QGIS Geographic Information System</i>. Open Source Geospatial Foundation Project.', 'ref')]

    # ---------------- Anexo ----------------
    E += [PageBreak(), H1('Anexo A. Comandos SQL utilizados'),
          P('Todos os comandos rodam em uma conexão somente leitura (' + m('default_transaction_read_only = on') + ') no banco ' + m('postgiscwb') +
            ' (PostgreSQL 17, PostGIS 3.5.2, GEOS 3.14, PROJ 9.8), e estão no repositório em ' + m('gis/sql/') + '. As consultas 03 a 06 são continuações da 02: '
            'executam-se substituindo o ' + m('SELECT') + ' final da consulta 02 (a partir do marcador ' + m('-- @@FINAL@@') + ') pelo conteúdo do arquivo, o que '
            'reaproveita os CTEs ' + m('hosp') + ', ' + m('mun') + ', ' + m('cobertura') + ' e ' + m('acesso') + '. O executor ' + m('gis/acessibilidade_postgis.py') +
            ' faz essa composição.', 'corpo_esq')]
    anexo = [('A.1', '01_qualidade.sql', 'Diagnóstico de qualidade: funil dos hospitais, SRID declarado × coordenadas, correspondência de nomes (Q1, seção 2.1).'),
             ('A.2', '02_acessibilidade_municipal.sql', 'Consulta principal (Q1, Q2 e Q3): correlaciona ' + m('bd2_2556553') + ' com a malha municipal e os estabelecimentos.'),
             ('A.3', '03_hospitais.sql', 'Camada de hospitais com junção espacial de conferência (continuação de A.2).'),
             ('A.4', '04_resumo_grupos.sql', 'Resumo por presença de hospital no território (Tabela 4; continuação de A.2).'),
             ('A.5', '05_correlacoes.sql', 'Correlações de Pearson (continuação de A.2).'),
             ('A.6', '06_cobertura.sql', 'Geometria da cobertura de 30 km, para o mapa (continuação de A.2).')]
    for cod, arq, desc in anexo:
        E += [H2(f'{cod} {arq}'), P(desc, 'corpo_sem'),
              Preformatted(quebrar((SQL / arq).read_text()), st['codigo'])]

    return E


def main():
    registrar_fontes()
    doc = SimpleDocTemplate(str(PDF), pagesize=A4, leftMargin=2.5 * cm, rightMargin=2.5 * cm, topMargin=2.3 * cm, bottomMargin=2.2 * cm,
                            title='Associação entre vulnerabilidade socioeconômica e internações pediátricas no Paraná',
                            author='Julia Mariano Torres da Silva, Giulia de Souza Leite')
    doc.build(montar(), onFirstPage=rodape, onLaterPages=rodape)
    print('PDF salvo em', PDF)


if __name__ == '__main__':
    main()
