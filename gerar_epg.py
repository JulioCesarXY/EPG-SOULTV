import requests
import json
from datetime import datetime, timedelta, timezone

# Cabeçalhos autenticados
headers = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36",
    "Authorization": "token 40d74c5c81385acde170e37cbe45ae74d74f53ed",
    "language": "pt",
    "country": "US",
    "platform": "web"
}

# Define as datas de hoje (padrão da API e do XMLTV)
agora = datetime.now(timezone.utc)
data_hoje_api = agora.strftime("%d/%m/%Y") # Formato 06/06/2026 para a URL
chave_data_json = agora.strftime("%Y-%m-%d") # Formato 2026-06-06 do nó da resposta

# Padrões de tempo para o Fallback caso o canal não tenha EPG
xml_inicio_fallback = agora.strftime("%Y%m%d000000 +0000")
xml_fim_fallback = (agora + timedelta(days=1)).strftime("%Y%m%d000000 +0000")

try:
    with open("soul_tv_api_mestre.json", "r", encoding="utf-8") as f:
        dados_plataforma = json.load(f)
    lista_canais = dados_plataforma.get("data", [])
except FileNotFoundError:
    print("Erro: 'soul_tv_api_mestre.json' não encontrado. Rode o script de captura primeiro.")
    exit()

# Inicialização do XMLTV
xml_content = [
    '<?xml version="1.0" encoding="UTF-8"?>\n',
    '<!DOCTYPE tv SYSTEM "xmltv.dtd">\n',
    '<tv generator-info-name="SoulTV_EPG_Mestre_Grabber">\n'
]

# 1. Registro dos canais no cabeçalho do XML
print("1/2 - Mapeando IDs de canais para o XML...")
for canal in lista_canais:
    cid = canal.get("id")
    nome = canal.get("name")
    if cid and nome:
        xml_content.append(f'  <channel id="{cid}">\n')
        xml_content.append(f'    <display-name lang="pt">{nome}</display-name>\n')
        xml_content.append(f'  </channel>\n')

print(f"\n2/2 - Extraindo cronogramas dinâmicos para a data: {data_hoje_api}...")

# 2. Varredura e parsing da árvore JSON baseada na sua resposta real
for canal in lista_canais:
    cid = canal.get("id")
    nome = canal.get("name")
    desc_canal = canal.get("description") or f"Assista ao canal {nome} ao vivo na Soul TV."
    
    if not cid:
        continue
        
    url_epg = f"https://cms.soultv.com.br/v1/schedules?channel={cid}&start_date={data_hoje_api}&days=1"
    epg_encontrado = False
    
    try:
        response = requests.get(url_epg, headers=headers, timeout=12)
        if response.status_code == 200:
            resposta_json = response.json()
            container_data = resposta_json.get("data", {})
            
            # Acessa a chave de data correspondente (Ex: dados['data']['2026-06-06'])
            if isinstance(container_data, dict) and chave_data_json in container_data:
                programas = container_data[chave_data_json]
                
                if isinstance(programas, list) and len(programas) > 0:
                    epg_encontrado = True
                    for prog in programas:
                        # Extrai os metadados do programa (priorizando o nó interno 'program')
                        prog_info = prog.get("program") or {}
                        titulo = prog_info.get("name") or prog.get("name") or "Programação Local"
                        descricao = prog_info.get("description") or prog.get("program_description") or desc_canal
                        
                        # Captura os horários de início e término
                        t_start = prog.get("time_start") # Ex: "00:00:00"
                        t_end = prog.get("time_end") # Ex: "01:00:00"
                        
                        if t_start and t_end:
                            # Converte e formata os horários para o padrão XMLTV (AAAAMMDDHHMMSS +0000)
                            stamp_inicio = f"{chave_data_json.replace('-', '')}{t_start.replace(':', '')} +0000"
                            stamp_fim = f"{chave_data_json.replace('-', '')}{t_end.replace(':', '')} +0000"
                            
                            xml_content.append(f'  <programme start="{stamp_inicio}" stop="{stamp_fim}" channel="{cid}">\n')
                            xml_content.append(f'    <title lang="pt">{titulo}</title>\n')
                            xml_content.append(f'    <desc lang="pt">{descricao}</desc>\n')
                            xml_content.append(f'  </programme>\n')
                            
    except Exception as e:
        print(f"  -> Falha de comunicação com o ID {cid}: {e}")

    # IMPLEMENTAÇÃO DO SEU REQUISITO: Fallback Automático usando a descrição institucional da API
    if not epg_encontrado:
        print(f"  -> [FALLBACK ATIVADO] {nome} sem guia oficial. Injetando descrição mestre.")
        xml_content.append(f'  <programme start="{xml_inicio_fallback}" stop="{xml_fim_fallback}" channel="{cid}">\n')
        xml_content.append(f'    <title lang="pt">{nome} ao Vivo</title>\n')
        xml_content.append(f'    <desc lang="pt">{desc_canal}</desc>\n')
        xml_content.append(f'  </programme>\n')
    else:
        print(f"  -> [EPG INTEGRADO] {nome}: Grade processada com sucesso.")

xml_content.append('</tv>\n')

# Criação do arquivo final XMLTV
with open("soul_tv_guia.xml", "w", encoding="utf-8") as f_xml:
    f_xml.writelines(xml_content)

print("\n=== SUCESSO COLETAL ===\nO arquivo 'soul_tv_guia.xml' está pronto e totalmente sincronizado!")
