import os
import sys
from ultralytics import YOLO

def export_loki_silvres():
    """
    Script de conversion du modèle YOLO (Loki-Silvres) vers ONNX optimisé.
    Optimisé pour l'inférence CPU via ONNX Runtime et simplify=True.
    """
    
    # Chemins par défaut
    pt_path = os.path.join("backend", "ai_models", "panoramic_model.pt")
    # Si l'utilisateur mentionne spécifiquement best.pt dans un dossier Loki-Silvres
    loki_path = os.path.join("backend", "ai_models", "Loki-Silvres", "best.pt")
    
    if os.path.exists(loki_path):
        source = loki_path
    elif os.path.exists(pt_path):
        source = pt_path
    else:
        print(f"❌ Erreur : Fichier modèle source non trouvé.")
        print(f"Attendu : {loki_path} ou {pt_path}")
        return

    print(f"🚀 Chargement du modèle : {source}")
    try:
        model = YOLO(source)
        
        print("📦 Exportation vers ONNX (simplify=True, opset=12)...")
        # export() génère un fichier .onnx dans le même répertoire que le .pt
        # simplify=True utilise onnxslim ou onnx-simplifier pour fusionner les couches
        # half=False est important pour CPU (FP32 est plus stable sur ONNX/CPU que FP16)
        onnx_path = model.export(
            format="onnx", 
            simplify=True, 
            opset=12,
            imgsz=640
        )
        
        print(f"✅ Exportation réussie : {onnx_path}")
        
    except Exception as e:
        print(f"❌ Erreur lors de l'exportation : {e}")

if __name__ == "__main__":
    # Installation automatique des dépendances d'export si nécessaire
    # Note : Nécessite pip install ultralytics onnx-simplifier onnxslim
    export_loki_silvres()
