import os
import urllib.request
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("FontDownloader")

FONTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "static", "assets", "fonts"))
os.makedirs(FONTS_DIR, exist_ok=True)

urls = {
    "InterTight-Regular.ttf": [
        "https://github.com/google/fonts/raw/main/ofl/intertight/static/InterTight-Regular.ttf",
        "https://github.com/google/fonts/raw/main/ofl/intertight/InterTight-Regular.ttf"
    ],
    "InterTight-Bold.ttf": [
        "https://github.com/google/fonts/raw/main/ofl/intertight/static/InterTight-Bold.ttf",
        "https://github.com/google/fonts/raw/main/ofl/intertight/InterTight-Bold.ttf"
    ],
    "PlayfairDisplay-Regular.ttf": [
        "https://github.com/google/fonts/raw/main/ofl/playfairdisplay/static/PlayfairDisplay-Regular.ttf",
        "https://github.com/google/fonts/raw/main/ofl/playfairdisplay/PlayfairDisplay-Regular.ttf"
    ],
    "PlayfairDisplay-Bold.ttf": [
        "https://github.com/google/fonts/raw/main/ofl/playfairdisplay/static/PlayfairDisplay-Bold.ttf",
        "https://github.com/google/fonts/raw/main/ofl/playfairdisplay/PlayfairDisplay-Bold.ttf"
    ]
}

def download_all():
    for name, candidates in urls.items():
        dest = os.path.join(FONTS_DIR, name)
        if os.path.exists(dest):
            logger.info(f"Font already exists: {name}")
            continue
            
        success = False
        for url in candidates:
            try:
                logger.info(f"Trying to download {name} from {url}...")
                urllib.request.urlretrieve(url, dest)
                logger.info(f"Successfully downloaded {name} to {dest}!")
                success = True
                break
            except Exception as e:
                logger.warning(f"Failed to download from {url}: {e}")
                
        if not success:
            logger.error(f"Could not download font: {name}")

if __name__ == "__main__":
    download_all()
