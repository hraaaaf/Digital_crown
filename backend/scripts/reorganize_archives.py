import os
import shutil
from pathlib import Path

def reorganize():
    base_dir = Path(r"c:\Users\lenovo\Documents\Cabinet\DigitalCrown\backend\static")
    old_archive = base_dir / "archive"
    new_archives = base_dir / "archives"
    target_cabinet = new_archives / "Cabinet_Elite"

    month_map = {
        "Janvier": "01",
        "Fevrier": "02",
        "Mars": "03",
        "Avril": "04",
        "Mai": "05",
        "Juin": "06",
        "Juillet": "07",
        "Aout": "08",
        "Septembre": "09",
        "Octobre": "10",
        "Novembre": "11",
        "Decembre": "12"
    }

    if not old_archive.exists():
        print("Dossier 'archive' inexistant.")
        return

    # Parcourir les types de documents dans l'ancienne structure
    for doc_type_dir in old_archive.iterdir():
        if not doc_type_dir.is_dir(): continue
        doc_type = doc_type_dir.name # Ex: NOTE
        
        # Mappage de type si nécessaire
        final_type = "NOTE_HONORAIRES" if doc_type == "NOTE" else doc_type

        for year_dir in doc_type_dir.iterdir():
            if not year_dir.is_dir(): continue
            year = year_dir.name # Ex: 2026

            for month_dir in year_dir.iterdir():
                if not month_dir.is_dir(): continue
                month_name = month_dir.name # Ex: Avril
                month_num = month_map.get(month_name, "00")

                target_dir = target_cabinet / year / month_num / final_type
                target_dir.mkdir(parents=True, exist_ok=True)

                for file in month_dir.iterdir():
                    if file.is_file():
                        dest = target_dir / file.name
                        print(f"Moving {file.name} to {target_dir}")
                        shutil.move(str(file), str(dest))
                
                # Supprimer le dossier mois s'il est vide
                try: month_dir.rmdir()
                except: pass
            
            # Supprimer le dossier année s'il est vide
            try: year_dir.rmdir()
            except: pass
        
        # Supprimer le dossier type s'il est vide
        try: doc_type_dir.rmdir()
        except: pass

    # Vérifier aussi le dossier '97' bizarre
    old_97 = new_archives / "97"
    if old_97.exists():
        print("Reorganizing '97' into 'Cabinet_Elite'...")
        for item in old_97.iterdir():
            if item.is_dir():
                # On suppose que 97 c'est le cabinet 1 (Elite)
                # Mais le dossier 97 a déjà la structure TYPE/YEAR/MONTH?
                # Non, j'ai vu 97/NOTE_HONORAIRES/2026/...
                for year_d in item.iterdir():
                    if not year_d.is_dir(): continue
                    for month_d in year_d.iterdir():
                        if not month_d.is_dir(): continue
                        
                        target_d = target_cabinet / year_d.name / month_d.name / item.name
                        target_d.mkdir(parents=True, exist_ok=True)
                        
                        for f in month_d.iterdir():
                            if f.is_file():
                                shutil.move(str(f), str(target_d / f.name))
                        try: month_d.rmdir()
                        except: pass
                    try: year_d.rmdir()
                    except: pass
                try: item.rmdir()
                except: pass
        try: old_97.rmdir()
        except: pass

if __name__ == "__main__":
    reorganize()
