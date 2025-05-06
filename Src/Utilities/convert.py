async def get_TMDb_id_from_IMDb_id(imdb_id, client):
    # Non possiamo convertire senza TMDb, restituiamo None per IMDb
    if imdb_id.startswith("tt"):
        return None
    # Se è un ID TMDb, estraiamo l'ID
    if "tmdb:" in imdb_id:
        return imdb_id.replace("tmdb:", "").split(":")[0]
    return imdb_id
