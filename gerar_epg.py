import requests
import json
from datetime import datetime, timedelta, timezone

# Cabeçalhos autenticados com o seu token válido
headers = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36",
    "Authorization": "token 40d74c5c81385acde170e37cbe45ae74d74f53ed",
    "language": "pt",
    "country": "US",
    "platform": "web"
}

# Define as datas para formatação no XMLTV e na API
agora = datetime.now(timezone.utc)
data_hoje_api = agora.strftime("%d/%m/%Y")

# Formatações de tempo padrão XMLTV (AAAAMMDDHHMMSS +0000)
xml_inicio_fallback = agora.strftime("%Y%m%d000000 +0000")
xml_fim_fallback = (agora + timedelta(days=1)).strftime("%Y%m%d000000 +0000")

try:
    with open("soul_tv_api_mestre.json", "r", encoding="utf-8") as f:
        dados_plataforma = json.load(f)
    lista_canais = dados_plataforma.get("data", [])
except FileNotFoundError:
    print("Erro: 'soul_tv_api_mestre.json' não encontrado. Rode o script de captura primeiro.")
    exit()

# Inicializa a estrutura do documento XMLTV
xml_content = [
    '<?xml version="1.0" encoding="UTF-8"?>\n',
    '<!DOCTYPE tv SYSTEM "xmltv.dtd">\n',
    '<tv generator-info-name="SoulTV_EPG_Fallback_Grabber">\n'
]

print("1/2 - Mapeando canais no arquivo de guia...")
for canal in lista_canais:
    cid = canal.get("id")
    nome = canal.get("name")
    if cid and nome:
        xml_content.append(f'  <channel id="{cid}">\n')
        xml_content.append(f'    <display-name lang="pt">{nome}</display-name>\n')
        xml_content.append(f'  </channel>\n')

print(f"\n2/2 - Baixando e estruturando a programação para {data_hoje_api}...")

for canal in lista_canais:
    cid = canal.get("id")
    nome = canal.get("name")
    desc_canal = canal.get("description") or f"Assista ao canal {nome} ao vivo na Soul TV."
    
    if not cid:
        continue
        
    url_epg = f"https://cms.soultv.com.br/v1/schedules?channel={cid}&start_date={data_hoje_api}&days=1"
    epg_encontrado = False
    
    try:
        response = requests.get(url_epg, headers=headers, timeout=10)
        if response.status_code == 200:
            programas = response.json().get("data", [])
            
            if isinstance(programas, list) and len(programas) > 0:
                epg_encontrado = True
                for prog in programas:
                    titulo = prog.get("title") or "Programação Local"
                    descricao = prog.get("description") or desc_canal
                    
                    # Tratamento e limpeza das strings de data da API para o padrão XMLTV
                    inicio_bruto = prog.get("start_at", "").replace("-", "").replace(":", "").split(".")[0]
                    fim_bruto = prog.get("end_at", "").replace("-", "").replace(":", "").split(".")[0]
                    
                    if inicio_bruto and fim_bruto:
                        xml_content.append(f'  <programme start="{inicio_bruto} +0000" stop="{fim_bruto} +0000" channel="{cid}">\n')
                        xml_content.append(f'    <title lang="pt">{titulo}</title>\n')
                        xml_content.append(f'    <desc lang="pt">{descricao}</desc>\n')
                        xml_content.append(f'  </programme>\n')
                        
    except Exception as e:
        print(f"  -> Conexão falhou para o canal {nome}, aplicando modo contingência.")

    # FALLBACK ATIVO: Se a API não retornou guia, injeta a descrição institucional do canal
    if not epg_encontrado:
        print(f"  -> [FALLBACK] {nome} sem grade ativa. Injetando a descrição da API.")
        xml_content.append(f'  <programme start="{xml_inicio_fallback}" stop="{xml_fim_fallback}" channel="{cid}">\n')
        xml_content.append(f'    <title lang="pt">{nome} ao Vivo</title>\n')
        xml_content.append(f'    <desc lang="pt">{desc_canal}</desc>\n')
        xml_content.append(f'  </programme>\n')
    else:
        print(f"  -> [OK] {nome} grade de programação integrada.")

xml_content.append('</tv>\n')

# Grava o arquivo XML final
with open("soul_tv_guia.xml", "w", encoding="utf-8") as f_xml:
    f_xml.writelines(xml_content)

print("\n[PROCESSO CONCLUÍDO] Arquivo de EPG 'soul_tv_guia.xml' gerado com sucesso!")
