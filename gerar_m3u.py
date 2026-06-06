import requests
import json

# URL da API mestre da Soul TV
URL_MASTER = "https://cms.soultv.com.br/v1/brand?country=US&language=pt&platform=web"

# Link definitivo do seu EPG no GitHub que será injetado no topo da lista
LINK_EPG_GITHUB = "https://raw.githubusercontent.com/JulioCesarXY/EPG-SOULTV/refs/heads/main/soul_tv_guia.xml"

# Clonagem exata dos cabeçalhos que funcionam na API
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

# Dicionário de tradução das categorias obtidas da API
MAPA_CATEGORIAS = {
    "1": "Agronegócios",
    "2": "Cultura",
    "3": "Esportes / Games",
    "4": "Entretenimento",
    "5": "Gastronomia",
    "6": "Internacional",
    "8": "Minas",
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
    print("Conectando ao banco mestre de canais Soul TV...")
    response = requests.get(URL_MASTER, headers=headers, timeout=20)
    
    if response.status_code == 200:
        dados_plataforma = response.json()
        
        # Salva o dump JSON mestre que o script de EPG vai ler depois
        with open("soul_tv_api_mestre.json", "w", encoding="utf-8") as f:
            json.dump(dados_plataforma, f, indent=4, ensure_ascii=False)
        print("[OK] Resposta bruta salva em 'soul_tv_api_mestre.json'")
        
        lista_canais = dados_plataforma.get("data", [])
        
        if lista_canais:
            # INTERVENÇÃO AQUI: Injeta o x-tvg-url apontando para o seu repositório no topo da lista
            m3u_linhas = [f'#EXTM3U x-tvg-url="{LINK_EPG_GITHUB}"\n']
            contagem = 0
            
            for canal in lista_canais:
                nome = canal.get("name")
                id_tv = canal.get("id")
                logo = canal.get("image") or canal.get("image2") or ""
                stream_url = canal.get("url_live_streaming")
                categorias_canal = canal.get("category", [])
                
                # Só processa canais com transmissão ativa
                if nome and stream_url:
                    # Mapeia o grupo do canal (excluindo a tag global 'ALL')
                    nome_categoria = "Variedades"
                    for cat_id in categorias_canal:
                        if cat_id != "ALL" and cat_id in MAPA_CATEGORIAS:
                            nome_categoria = MAPA_CATEGORIAS[cat_id]
                            break
                    
                    # Cria a linha estruturada com ID do EPG (tvg-id) combinando com o XML
                    m3u_linhas.append(
                        f'#EXTINF:-1 tvg-id="{id_tv}" tvg-logo="{logo}" group-title="{nome_categoria}",{nome}\n'
                    )
                    m3u_linhas.append(f'{stream_url}\n')
                    contagem += 1
            
            # Grava a lista M3U final categorizada e linkada com o EPG
            with open("soul_tv_categorizado.m3u", "w", encoding="utf-8") as f_m3u:
                f_m3u.writelines(m3u_linhas)
                
            print(f"\n[SUCESSO] Lista 'soul_tv_categorizado.m3u' gerada com {contagem} canais e vinculada ao EPG!")
        else:
            print("Erro: A API retornou sucesso, mas a lista de canais veio vazia.")
    else:
        print(f"Erro {response.status_code} ao bater na API da plataforma.")

except Exception as e:
    print(f"Erro crítico durante a execução do M3U: {e}")
