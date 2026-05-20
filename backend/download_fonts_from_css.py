import os
import urllib.request
import zipfile
import io
import shutil
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("FontDownloader")

FONTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "static", "assets", "fonts"))
os.makedirs(FONTS_DIR, exist_ok=True)

def download_and_extract_font(font_id, font_name_map):
    url = f"https://gwfh.mranftl.com/api/fonts/{font_id}?download=zip&subsets=latin&formats=ttf&variants=regular,700"
    logger.info(f"Downloading ZIP for {font_id} from {url}...")
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            zip_data = response.read()
            
        logger.info(f"Extracting {font_id} font files...")
        with zipfile.ZipFile(io.BytesIO(zip_data)) as zip_ref:
            for zip_info in zip_ref.infolist():
                filename = zip_info.filename
                # Look for .ttf files
                if filename.endswith(".ttf"):
                    # We map variants 'regular' to 'Regular' and '700' to 'Bold'
                    is_bold = "-700." in filename or "_700." in filename or "700" in filename
                    dest_name = font_name_map["bold"] if is_bold else font_name_map["regular"]
                    dest_path = os.path.join(FONTS_DIR, dest_name)
                    
                    logger.info(f"Saving {filename} as {dest_name}...")
                    with zip_ref.open(zip_info) as source, open(dest_path, "wb") as target:
                        shutil.copyfileobj(source, target)
                        
        logger.info(f"Successfully processed {font_id}!")
        return True
    except Exception as e:
        logger.error(f"Failed to process {font_id}: {e}")
        return False

def main():
    # Clean up old/corrupted files first
    corrupted_files = [
        "InterTight-Regular.ttf", "InterTight-Bold.ttf",
        "PlayfairDisplay-Regular.ttf", "PlayfairDisplay-Bold.ttf"
    ]
    for f in corrupted_files:
        path = os.path.join(FONTS_DIR, f)
        if os.path.exists(path):
            os.remove(path)
            logger.info(f"Removed corrupted font file: {f}")

    # Download Inter Tight
    download_and_extract_font("inter-tight", {
        "regular": "InterTight-Regular.ttf",
        "bold": "InterTight-Bold.ttf"
    })
    
    # Download Playfair Display
    download_and_extract_font("playfair-display", {
        "regular": "PlayfairDisplay-Regular.ttf",
        "bold": "PlayfairDisplay-Bold.ttf"
    })

if __name__ == "__main__":
    main()
