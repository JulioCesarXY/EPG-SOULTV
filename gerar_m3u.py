import requests
import json

URL_MASTER = "https://cms.soultv.com.br/v1/brand?country=US&language=pt&platform=web"
LINK_EPG_GITHUB = "https://raw.githubusercontent.com/JulioCesarXY/EPG-SOULTV/refs/heads/main/soul_tv_guia.xml"

headers = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
    "Authorization": "token 40d74c5c81385acde170e37cbe45ae74d74f53ed",
    "language": "pt",
    "country": "US",
    "platform": "web",
    "Origin": "https://www.soultv.com.br",
    "Referer": "https://www.soultv.com.br/"
}

MAPA_CATEGORIAS = {
    "1": "Agronegócios", "2": "Cultura", "3": "Esportes / Games", "4": "Entretenimento",
    "5": "Gastronomia", "6": "Internacional", "8": "Minas", "9": "Música",
    "10": "Moda / Beleza", "11": "Religioso", "12": "Regionais", "13": "Shopping",
    "14": "Variedades", "15": "Viagens", "16": "Filmes / Séries", "17": "Pet"
}

try:
    print("Conectando ao banco mestre de canais Soul TV...")
    response = requests.get(URL_MASTER, headers=headers, timeout=20)
    
    if response.status_code == 200:
        dados_plataforma = response.json()
        
        with open("soul_tv_api_mestre.json", "w", encoding="utf-8") as f:
            json.dump(dados_plataforma, f, indent=4, ensure_ascii=False)
        
        lista_canais = dados_plataforma.get("data", [])
        
        if lista_canais:
            # 1. Dicionário para separar os canais dinamicamente por nome de categoria
            canais_por_categoria = {}
            contagem = 0
            
            for canal in lista_canais:
                nome = canal.get("name")
                id_tv = canal.get("id")
                logo = canal.get("image") or canal.get("image2") or ""
                stream_url = canal.get("url_live_streaming")
                categorias_canal = canal.get("category", [])
                
                if nome and stream_url:
                    # Identifica a categoria (ignorando 'ALL')
                    nome_categoria = "Variedades"
                    for cat_id in categorias_canal:
                        if cat_id != "ALL" and cat_id in MAPA_CATEGORIAS:
                            nome_categoria = MAPA_CATEGORIAS[cat_id]
                            break
                    
                    # Inicializa a lista da categoria no dicionário caso não exista
                    if nome_categoria not in canais_por_categoria:
                        canais_por_categoria[nome_categoria] = []
                        
                    # Guarda os dados estruturados do canal na sua respectiva gaveta
                    canais_por_categoria[nome_categoria].append({
                        "id": id_tv,
                        "logo": logo,
                        "nome": nome,
                        "url": stream_url
                    })
                    contagem += 1
            
            # 2. Monta o arquivo M3U escrevendo categoria por categoria de forma sequencial
            m3u_linhas = [f'#EXTM3U x-tvg-url="{LINK_EPG_GITHUB}"\n']
            
            # Ordena as chaves alfabeticamente para as pastas ficarem organizadas de A-Z
            for categoria in sorted(canais_por_categoria.keys()):
                print(f" -> Agrupando bloco: {categoria} ({len(canais_por_categoria[categoria])} canais)")
                for c in canais_por_categoria[categoria]:
                    m3u_linhas.append(f'#EXTINF:-1 tvg-id="{c["id"]}" tvg-logo="{c["logo"]}" group-title="{categoria}",{c["nome"]}\n')
                    m3u_linhas.append(f'{c["url"]}\n')
            
            with open("soul_tv_categorizado.m3u", "w", encoding="utf-8") as f_m3u:
                f_m3u.writelines(m3u_linhas)
                
            print(f"\n[SUCESSO] Lista ordenada e dividida com {contagem} canais com sucesso!")
        else:
            print("Erro: A lista de canais veio vazia.")
    else:
        print(f"Erro {response.status_code} na API.")

except Exception as e:
    print(f"Erro crítico: {e}")
