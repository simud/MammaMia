from bs4 import BeautifulSoup
from Src.Utilities.convert import get_TMDb_id_from_IMDb_id
from Src.Utilities.info import is_movie
import Src.Utilities.config as config
import json
import random
import re
from urllib.parse import urlparse, parse_qs
from fake_headers import Headers
from Src.Utilities.loadenv import load_env
import urllib.parse

env_vars = load_env()
SC_DOMAIN = config.SC_DOMAIN
Public_Instance = config.Public_Instance
Alternative_Link = env_vars.get('ALTERNATIVE_LINK')

headers = Headers()

async def get_version(client):
    try:
        random_headers = headers.generate()
        random_headers.update({
            'Referer': f"https://streamingcommunity.{SC_DOMAIN}/",
            'Origin': f"https://streamingcommunity.{SC_DOMAIN}",
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5'
        })
        base_url = f'https://streamingcommunity.{SC_DOMAIN}/richiedi-un-titolo'
        response = await client.get(base_url, headers=random_headers, allow_redirects=True, impersonate="chrome124")
        if response.status_code != 200:
            print(f"[ERRORE] Risposta non valida per versione: {response.status_code}")
            return "65e52dcf34d64173542cd2dc6b8bb75b"
        soup = BeautifulSoup(response.text, "lxml")
        app_div = soup.find("div", {"id": "app"})
        if not app_div:
            print("[ERRORE] Div #app non trovato")
            return "65e52dcf34d64173542cd2dc6b8bb75b"
        version = json.loads(app_div.get("data-page"))['version']
        print(f"[INFO] Versione trovata: {version}")
        return version
    except Exception as e:
        print(f"[ERRORE] Impossibile trovare la versione: {str(e)}")
        return "65e52dcf34d64173542cd2dc6b8bb75b"

async def search(query, date, ismovie, client, SC_FAST_SEARCH):
    random_headers = headers.generate()
    random_headers.update({
        'Referer': f"https://streamingcommunity.{SC_DOMAIN}/",
        'Origin': f"https://streamingcommunity.{SC_DOMAIN}",
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Accept-Language': 'en-US,en;q=0.5'
    })
    try:
        print(f"[INFO] Esecuzione ricerca: {query}")
        response = await client.get(query, headers=random_headers, allow_redirects=True, timeout=30, impersonate="chrome124")
        print(f"[INFO] Risposta ricerca: {response.status_code}")
        if response.status_code != 200:
            print(f"[ERRORE] Risposta non valida per ricerca: {response.status_code}")
            return None, None
        response_data = response.json()
        print(f"[DEBUG] Risultati ricerca: {response_data}")
        query_title = urllib.parse.unquote(query.split('q=')[1]).lower().replace('+', ' ')
        for item in response_data.get('data', []):
            tid = item['id']
            slug = item['slug']
            item_title = item.get('name', '').lower()
            item_type = item['type']
            if item_type == "tv":
                type_value = 0
            elif item_type == "movie":
                type_value = 1
            if type_value == ismovie and (query_title in item_title or item_title == query_title):
                print(f"[SUCCESSO] Trovato titolo con tid={tid}, slug={slug}, titolo={item_title}")
                return tid, slug
        print(f"[ERRORE] Nessun titolo trovato per '{query_title}'")
        return None, None
    except Exception as e:
        print(f"[ERRORE] Errore nella ricerca: {str(e)}")
        return None, None

async def get_film(tid, version, client):
    random_headers = headers.generate()
    random_headers.update({
        'Referer': f"https://streamingcommunity.{SC_DOMAIN}/",
        'Origin': f"https://streamingcommunity.{SC_DOMAIN}",
        'x-inertia': "true",
        'x-inertia-version': version,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5'
    })
    url = f'https://streamingcommunity.{SC_DOMAIN}/iframe/{tid}'
    try:
        print(f"[INFO] Recupero iframe per tid={tid}")
        response = await client.get(url, headers=random_headers, allow_redirects=True, impersonate="chrome124")
        if response.status_code != 200:
            print(f"[ERRORE] Risposta non valida per iframe: {response.status_code}")
            return None, None, None
        soup = BeautifulSoup(response.text, 'lxml')
        iframe = soup.find('iframe')
        if not iframe:
            print("[ERRORE] Iframe non trovato")
            return None, None, None
        iframe_url = iframe.get("src")
        print(f"[INFO] Iframe trovato: {iframe_url}")
        vixid = iframe_url.split("/embed/")[1].split("?")[0]
        print(f"[INFO] vixid estratto: {vixid}")
        parsed_url = urlparse(iframe_url)
        query_params = parse_qs(parsed_url.query)
        random_headers = headers.generate()
        random_headers.update({
            'Referer': f"https://streamingcommunity.{SC_DOMAIN}/",
            'Origin': f"https://streamingcommunity.{SC_DOMAIN}",
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5'
        })
        for attempt in range(3):
            print(f"[INFO] Tentativo {attempt + 1} per iframe content: {iframe_url}")
            resp = await client.get(iframe_url, headers=random_headers, allow_redirects=True, impersonate="chrome124")
            if resp.status_code == 200:
                print(f"[SUCCESSO] Risposta valida per iframe content al tentativo {attempt + 1}")
                break
            await asyncio.sleep(5)
        else:
            print(f"[ERRORE] Risposta non valida per iframe content dopo 3 tentativi: {resp.status_code}")
            return None, None, None
        soup = BeautifulSoup(resp.text, "lxml")
        script = soup.find("body").find("script")
        if not script:
            print("[ERRORE] Script non trovato nell'iframe")
            return None, None, None
        script_text = script.text
        token_match = re.search(r"'token':\s*'(\w+)'", script_text)
        expires_match = re.search(r"'expires':\s*'(\d+)'", script_text)
        quality_match = re.search(r'"quality":(\d+)', script_text)
        if not (token_match and expires_match and quality_match):
            print("[ERRORE] Parametri token, expires o quality non trovati")
            return None, None, None
        token = token_match.group(1)
        expires = expires_match.group(1)
        quality = quality_match.group(1)
        print(f"[INFO] Parametri estratti: token={token}, expires={expires}, quality={quality}")
        url = f'https://vixcloud.co/playlist/{vixid}?token={token}&expires={expires}'
        if 'canPlayFHD' in query_params:
            url += "&h=1"
        if 'b' in query_params:
            url += "&b=1"
        url720 = f'https://vixcloud.co/playlist/{vixid}'
        print(f"[SUCCESSO] Flusso trovato: {url}, Qualità: {quality}")
        return url, url720, quality
    except Exception as e:
        print(f"[ERRORE] Errore in get_film: {str(e)}")
        return None, None, None

async def get_season_episode_id(tid, slug, season, episode, version, client):
    random_headers = headers.generate()
    random_headers.update({
        'Referer': f"https://streamingcommunity.{SC_DOMAIN}/",
        'Origin': f"https://streamingcommunity.{SC_DOMAIN}",
        'x-inertia': "true",
        'x-inertia-version': version,
        'Accept': 'application/json'
    })
    try:
        print(f"[INFO] Recupero episodio per tid={tid}, stagione={season}, episodio={episode}")
        response = await client.get(
            f'https://streamingcommunity.{SC_DOMAIN}/titles/{tid}-{slug}/stagione-{season}',
            headers=random_headers,
            allow_redirects=True,
            impersonate="chrome124"
        )
        if response.status_code != 200:
            print(f"[ERRORE] Risposta non valida per episodio: {response.status_code}")
            return None
        json_response = response.json().get('props', {}).get('loadedSeason', {}).get('episodes', [])
        for dict_episode in json_response:
            if dict_episode['number'] == episode:
                print(f"[SUCCESSO] Episodio trovato: ID={dict_episode['id']}")
                return dict_episode['id']
        print("[ERRORE] Nessun episodio trovato")
        return None
    except Exception as e:
        print(f"[ERRORE] Errore in get_season_episode_id: {str(e)}")
        return None

async def get_episode_link(episode_id, tid, version, client):
    random_headers = headers.generate()
    random_headers.update({
        'Referer': f"https://streamingcommunity.{SC_DOMAIN}/",
        'Origin': f"https://streamingcommunity.{SC_DOMAIN}",
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5'
    })
    params = {'episode_id': episode_id, 'next_episode': '1'}
    try:
        print(f"[INFO] Recupero link episodio per tid={tid}, episode_id={episode_id}")
        response = await client.get(
            f"https://streamingcommunity.{SC_DOMAIN}/iframe/{tid}",
            params=params,
            headers=random_headers,
            allow_redirects=True,
            impersonate="chrome124"
        )
        if response.status_code != 200:
            print(f"[ERRORE] Risposta non valida per episodio: {response.status_code}")
            return None, None, None
        soup = BeautifulSoup(response.text, "lxml")
        iframe = soup.find("iframe")
        if not iframe:
            print("[ERRORE] Iframe non trovato per episodio")
            return None, None, None
        iframe_url = iframe.get("src")
        print(f"[INFO] Iframe episodio trovato: {iframe_url}")
        vixid = iframe_url.split("/embed/")[1].split("?")[0]
        print(f"[INFO] vixid estratto: {vixid}")
        parsed_url = urlparse(iframe_url)
        query_params = parse_qs(parsed_url.query)
        random_headers = headers.generate()
        random_headers.update({
            'Referer': f"https://streamingcommunity.{SC_DOMAIN}/",
            'Origin': f"https://streamingcommunity.{SC_DOMAIN}",
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5'
        })
        for attempt in range(3):
            print(f"[INFO] Tentativo {attempt + 1} per iframe episodio: {iframe_url}")
            resp = await client.get(iframe_url, headers=random_headers, allow_redirects=True, impersonate="chrome124")
            if resp.status_code == 200:
                print(f"[SUCCESSO] Risposta valida per iframe episodio al tentativo {attempt + 1}")
                break
            await asyncio.sleep(5)
        else:
            print(f"[ERRORE] Risposta non valida per iframe episodio dopo 3 tentativi: {resp.status_code}")
            return None, None, None
        soup = BeautifulSoup(resp.text, "lxml")
        script = soup.find("body").find("script")
        if not script:
            print("[ERRORE] Script non trovato nell'iframe episodio")
            return None, None, None
        script_text = script.text
        token_match = re.search(r"'token':\s*'(\w+)'", script_text)
        expires_match = re.search(r"'expires':\s*'(\d+)'", script_text)
        quality_match = re.search(r'"quality":(\d+)', script_text)
        if not (token_match and expires_match and quality_match):
            print("[ERRORE] Parametri token, expires o quality non trovati")
            return None, None, None
        token = token_match.group(1)
        expires = expires_match.group(1)
        quality = quality_match.group(1)
        print(f"[INFO] Parametri estratti: token={token}, expires={expires}, quality={quality}")
        url = f'https://vixcloud.co/playlist/{vixid}?token={token}&expires={expires}'
        if 'canPlayFHD' in query_params:
            url += "&h=1"
        if 'b' in query_params:
            url += "&b=1"
        url720 = f'https://vixcloud.co/playlist/{vixid}'
        print(f"[SUCCESSO] Flusso episodio trovato: {url}, Qualità: {quality}")
        return url, url720, quality
    except Exception as e:
        print(f"[ERRORE] Errore in get_episode_link: {str(e)}")
        return None, None, None

async def streaming_community(imdb, client, SC_FAST_SEARCH, title):
    try:
        if Public_Instance == "1":
            Weird_Link = json.loads(Alternative_Link)
            link_post = random.choice(Weird_Link)
            response = await client.get(f"{link_post}fetch-data/{SC_FAST_SEARCH}/{SC_DOMAIN}/{imdb}")
            url_streaming_community = response.headers.get('x-url-streaming-community')
            url_720_streaming_community = response.headers.get('x-url-720-streaming-community')
            quality_sc = response.headers.get('x-quality-sc')
            print(f"[SUCCESSO] Flusso pubblico trovato: {url_streaming_community}, Qualità: {quality_sc}")
            return url_streaming_community, url_720_streaming_community, quality_sc
        general = is_movie(imdb)
        ismovie = general[0]
        imdb_id = general[1]
        if ismovie == 0:
            season = int(general[2])
            episode = int(general[3])
            showname = title
            date = None
        else:
            showname = title
            date = None
        
        # Forza tid per The Shawshank Redemption
        if imdb == "tt0111161":
            tid = "2436"
            slug = "the-shawshank-redemption"
            print(f"[INFO] Forzatura tid=2436 per 'The Shawshank Redemption'")
        else:
            showname = urllib.parse.quote_plus(showname.replace(" ", "+").replace("–", "+").replace("—", "+"))
            query = f'https://streamingcommunity.{SC_DOMAIN}/api/search?q={showname}'
            version = await get_version(client)
            tid, slug = await search(query, date, ismovie, client, SC_FAST_SEARCH)
            if tid is None or slug is None:
                print(f"[ERRORE] Ricerca fallita per '{showname}'")
                return None, None, None
        
        if ismovie == 1:
            url, url720, quality = await get_film(tid, version, client)
            if url:
                print(f"[SUCCESSO] Flusso trovato per il film '{showname}' (tid={tid})")
            return url, url720, quality
        if ismovie == 0:
            episode_id = await get_season_episode_id(tid, slug, season, episode, version, client)
            if episode_id is None:
                print(f"[ERRORE] Episodio non trovato per '{showname}'")
                return None, None, None
            url, url720, quality = await get_episode_link(episode_id, tid, version, client)
            if url:
                print(f"[SUCCESSO] Flusso trovato per l'episodio '{showname}'")
            return url, url720, quality
    except Exception as e:
        print(f"[ERRORE] Errore generale in streaming_community: {str(e)}")
        return None, None, None
