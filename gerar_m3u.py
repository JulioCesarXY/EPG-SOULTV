import json

# Dicionário de tradução baseado no arquivo 'categorias_soul.json' que você capturou
MAPA_CATEGORIAS = {
    "1": "Agronegócios",
    "2": "Cultura",
    "3": "Esportes / Games",
    "4": "Entretenimento",
    "5": "Gastronomia",
    "6": "Internacional",
    "8": "Minas", # ID associado a canais locais de MG como BH Channel
    "9": "Música",
    "10": "Moda / Beleza",
    "11": "Religioso",
    "12": "Regionais",
    "13": "Shopping",
    "14": "Variedades",
    "15": "Viagens",
    "16": "Filmes / Séries",
    "17": "Pet"
}

try:
    # 1. Carrega o banco de dados mestre gerado na etapa anterior
    with open("soul_tv_api_mestre.json", "r", encoding="utf-8") as f:
        dados_plataforma = json.load(f)
        
    lista_canais = dados_plataforma.get("data", [])
    
    if not lista_canais:
        print("Erro: O arquivo 'soul_tv_api_mestre.json' não possui dados válidos de canais.")
        exit()

    m3u_linhas = ["#EXTM3U\n"]
    canais_processados = 0

    print(f"Agrupando {len(lista_canais)} canais por categoria...")

    for canal in lista_canais:
        nome = canal.get("name")
        id_tv = canal.get("id")
        logo = canal.get("image") or canal.get("image2") or ""
        stream_url = canal.get("url_live_streaming")
        categorias_canal = canal.get("category", [])
        
        if not nome or not stream_url:
            continue
            
        # 2. Identifica a categoria correta do canal ignorando a tag global 'ALL'
        nome_categoria = "Variedades" # Categoria padrão caso não encontre correspondência
        
        for cat_id in categorias_canal:
            if cat_id != "ALL" and cat_id in MAPA_CATEGORIAS:
                nome_categoria = MAPA_CATEGORIAS[cat_id]
                break # Pega a primeira categoria válida encontrada
                
        # 3. Monta a linha M3U injetando a tag group-title para separação no player
        m3u_linhas.append(
            f'#EXTINF:-1 tvg-id="{id_tv}" tvg-logo="{logo}" group-title="{nome_categoria}",{nome}\n'
        )
        m3u_linhas.append(f'{stream_url}\n')
        canais_processados += 1

    # 4. Escreve o arquivo final estruturado por grupos
    with open("soul_tv_categorizado.m3u", "w", encoding="utf-8") as f_m3u:
        f_m3u.writelines(m3u_linhas)

    print(f"\n[SUCESSO] Lista dividida em grupos gerada com {canais_processados} canais!")
    print("Arquivo salvo com sucesso como: 'soul_tv_categorizado.m3u'")

except FileNotFoundError:
    print("Erro: Certifique-se de que o arquivo 'soul_tv_api_mestre.json' está no mesmo diretório deste script.")
except Exception as e:
    print(f"Ocorreu um erro inesperado: {e}")
