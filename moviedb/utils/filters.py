

def tmdb_image(path):
    if not path:
        return ""
    return f"https://image.tmdb.org/t/p/w500{path}"
