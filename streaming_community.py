from bs4 import BeautifulSoup
from Src.Utilities.convert import get_TMDb_id_from_IMDb_id
from Src.Utilities.info import get_info_tmdb, is_movie, get_info_imdb
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
        random_headers['Referer'] = f"https://streamingcommunity.{SC_DOMAIN}/"
        random_headers['Origin'] = f"https://streamingcommunity.{SC_DOMAIN}"
        base_url = f'https://streamingcommunity.{SC_DOMAIN}/richiedi-un-titolo' 
        response = await client.get(base_url, headers=random_headers, allow_redirects=True, impersonate="chrome124")
        soup = BeautifulSoup(response.text, "lxml")
        version = json.loads(soup.find("div", {"id": "app"}).get("data-page"))['version']
        print(f"[INFO] Versione trovata: {version}")
        return version
    except Exception as e:
        print(f"[ERRORE] Impossibile trovare la versione: {str(e)}")
        version = "65e52dcf34d64173542cd2dc6b8bb75b"
        return version

async def search(query, date, ismovie, client, SC_FAST_SEARCH):
    random_headers = headers.generate()
    random_headers['Referer'] = f"https://streamingcommunity.{SC_DOMAIN}/"
    random_headers['Origin'] = f"https://streamingcommunity.{SC_DOMAIN}"
    random_headers['Accept'] = 'application/json'
    random_headers['Content-Type'] = 'application/json'
    try:
        print(f"[INFO] Esecuzione ricerca: {query}")
        response = await client.get(query, headers=random_headers, allow_redirects=True, timeout=30)
        print(f"[INFO] Risposta ricerca: {response.status_code}")
        response_data = response.json()
        print(f"[DEBUG] Risultati ricerca: {response_data}")
        for item in response_data.get('data', []):
            tid = item['id']
            slug = item['slug']
            type = item['type']
            if type == "tv":
                type = 0
            elif type == "movie":
                type = 1
            if type == ismovie: 
                if SC_FAST_SEARCH == "0":
                    random_headers = headers.generate()
                    random_headers['Referer'] = f"https://streamingcommunity.{SC_DOMAIN}/"
                    random_headers['Origin'] = f"https://streamingcommunity.{SC_DOMAIN}"
                    response = await client.get(f'https://streamingcommunity.{SC_DOMAIN}/titles/{tid}-{slug}', headers=random_headers, allow_redirects=True, impersonate="chrome124")
                    pattern = r'<div[^>]*class="features"[^>]*>.*?<span[^>]*>(.*?)<\/span>'
                    match = re.search(pattern, response.text)
                    if match:
                        print(f"[INFO] Anno trovato: {match.group(1).split('-')[0]}")
                        first_air_year = match.group(1).split("-")[0]
                        date = int(date)
                        first_air_year = int(first_air_year)
                        if first_air_year == date:
                            print(f"[SUCCESSO] Trovato titolo con tid={tid}, slug={slug}")
                            return tid, slug
                elif SC_FAST_SEARCH == "1":
                    print(f"[SUCCESSO] Trovato titolo con tid={tid}, slug={slug}")
                    return tid, slug
        print("[ERRORE] Nessun titolo trovato nella ricerca")
        return None, None
    except Exception as e:
        print(f"[ERRORE] Errore nella ricerca: {str(e)}")
        return None, None

async def get_film(tid, version, client):  
    random_headers = headers.generate()
    random_headers['Referer'] = f"https://streamingcommunity.{SC_DOMAIN}/"
    random_headers['Origin'] = f"https://streamingcommunity.{SC_DOMAIN}"
    random_headers['x-inertia'] = "true"
    random_headers['x-inertia-version'] = version
    url = f'https://streamingcommunity.{SC_DOMAIN}/iframe/{tid}'
    try:
        response = await client.get(url, headers=random_headers, allow_redirects=True, impersonate="chrome124")
        iframe = BeautifulSoup(response.text, 'lxml')
        iframe = iframe.find('iframe').get("src")
        vixid = iframe.split("/embed/")[1].split("?")[0]
        parsed_url = urlparse(iframe)
        query_params = parse_qs(parsed_url.query)
        random_headers = headers.generate()
        random_headers['Referer'] = f"https://streamingcommunity.{SC_DOMAIN}/"
        random_headers['Origin'] = f"https://streamingcommunity.{SC_DOMAIN}"
        random_headers['x-inertia'] = "true"
        random_headers['x-inertia-version'] = version
        resp = await client.get(iframe, headers=random_headers, allow_redirects=True, impersonate="chrome124")
        soup = BeautifulSoup(resp.text, "lxml")
        script = soup.find("body").find("script").text
        token = re.search(r"'token':\s*'(\w+)'", script).group(1)
        expires = re.search(r"'expires':\s*'(\d+)'", script).group(1)
        quality = re.search(r'"quality":(\d+)', script).group(1)
        url = f'https://vixcloud.co/playlist/{vixid}.m3u8?token={token}&expires={expires}'
        if 'canPlayFHD' in query_params:
            url += "&h=1"
        if 'b' in query_params:
            url += "&b=1"
        url720 = f'https://vixcloud.co/playlist/{vixid}.m3u8'
        print(f"[SUCCESSO] Flusso trovato: {url}, Qualità: {quality}")
        return url, url720, quality
    except Exception as e:
        print(f"[ERRORE] Errore in get_film: {str(e)}")
        return None, None, None

async def get_season_episode_id(tid, slug, season, episode, version, client):
    random_headers = headers.generate()
    random_headers['Referer'] = f"https://streamingcommunity.{SC_DOMAIN}/"
    random_headers['Origin'] = f"https://streamingcommunity.{SC_DOMAIN}"
    random_headers['x-inertia'] = "true"
    random_headers['x-inertia-version'] = version
    try:
        response = await client.get(f'https://streamingcommunity.{SC_DOMAIN}/titles/{tid}-{slug}/stagione-{season}', headers=random_headers, allow_redirects=True, impersonate="chrome124")
        json_response = response.json().get('props', {}).get('loadedSeason', {}).get('episodes', [])
        for dict_episode in json_response:
            if dict_episode['number'] == episode:
                print(f"[SUCCESSO] Episodio trovato: ID={dict_episode['id']}")
                return dict_episode['id']
        print("[ERRORE] Nessun episodio trovato per la stagione specificata")
        return None
    except Exception as e:
        print(f"[ERRORE] Errore in get_season_episode_id: {str(e)}")
        return None

async def get_episode_link(episode_id, tid, version, client):
    random_headers = headers.generate()
    random_headers['Referer'] = f"https://streamingcommunity.{SC_DOMAIN}/"
    random_headers['Origin'] = f"https://streamingcommunity.{SC_DOMAIN}"
    params = {
        'episode_id': episode_id, 
        'next_episode': '1'
    }
    try:
        response = await client.get(f"https://streamingcommunity.{SC_DOMAIN}/iframe/{tid}", params=params, headers=random_headers, allow_redirects=True, impersonate="chrome124")
        soup = BeautifulSoup(response.text, "lxml")
        iframe = soup.find("iframe").get("src")
        vixid = iframe.split("/embed/")[1].split("?")[0]
        parsed_url = urlparse(iframe)
        query_params = parse_qs(parsed_url.query)
        random_headers = headers.generate()
        random_headers['Referer'] = f"https://streamingcommunity.{SC_DOMAIN}/"
        random_headers['Origin'] = f"https://streamingcommunity.{SC_DOMAIN}"
        random_headers['x-inertia'] = "true"
        random_headers['x-inertia-version'] = version
        resp = await client.get(iframe, headers=random_headers, allow_redirects=True, impersonate="chrome124")
        soup = BeautifulSoup(resp.text, "lxml")
        script = soup.find("body").find("script").text
        token = re.search(r"'token':\s*'(\w+)'", script).group(1)
        expires = re.search(r"'expires':\s*'(\d+)'", script).group(1)
        quality = re.search(r'"quality":(\d+)', script).group(1)
        url = f'https://vixcloud.co/playlist/{vixid}.m3u8?token={token}&expires={expires}'
        if 'canPlayFHD' in query_params:
            url += "&h=1"
        if 'b' in query_params:
            url += "&b=1"
        url720 = f'https://vixcloud.co/playlist/{vixid}.m3u8'
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
            if SC_FAST_SEARCH == "1":
                type = "StreamingCommunityFS"
                showname = title  # Usa il titolo passato
                date = None
            elif SC_FAST_SEARCH == "0":
                type = "StreamingCommunity"
                tmdba = await get_TMDb_id_from_IMDb_id(imdb_id, client)
                showname = title
                date = None
        else:
            if SC_FAST_SEARCH == "1":
                type = "StreamingCommunityFS"
                showname = title  # Usa il titolo passato
                date = None
            elif SC_FAST_SEARCH == "0":
                type = "StreamingCommunity"
                showname = title
                date = None
        
        showname = showname.replace(" ", "+").replace("–", "+").replace("—", "+")
        showname = urllib.parse.quote_plus(showname)
        query = f'https://streamingcommunity.{SC_DOMAIN}/api/search?q={showname}'
        version = await get_version(client)
        tid, slug = await search(query, date, ismovie, client, SC_FAST_SEARCH)
        if tid is None or slug is None:
            print(f"[ERRORE] Ricerca fallita per '{showname}'")
            return None, None, None
        if ismovie == 1:
            url, url720, quality = await get_film(tid, version, client)
            if url:
                print(f"[SUCCESSO] Flusso trovato per il film '{showname}'")
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
