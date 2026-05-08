import argparse
from ultralytics import YOLO

def convert_model(model_path: str, img_size: int = 1280):
    print(f"🚀 Début de la conversion ONNX pour : {model_path}")
    
    # 1. Chargement du modèle PyTorch (YOLOv8)
    try:
        model = YOLO(model_path)
    except Exception as e:
        print(f"❌ Erreur lors du chargement du modèle PyTorch : {e}")
        return
    
    # 2. Exportation avec optimisation (simplify=True)
    # L'argument simplify=True exécute onnx-simplifier pour fusionner les noeuds constants
    # et réduire l'overhead d'inférence CPU.
    print(f"⏳ Exportation en cours avec simplify=True (Image Size: {img_size}x{img_size})...")
    
    try:
        exported_path = model.export(
            format="onnx",
            imgsz=img_size,       # Taille d'entrée (1280x1280 est standard pour les panoramiques HD)
            simplify=True,        # Optimisation cruciale pour l'inférence CPU
            opset=12,             # Opset 12 offre la meilleure compatibilité avec le runtime ONNX actuel
            half=False,           # FP32 pour CPU (FP16 est souvent plus lent sur CPU standard)
            dynamic=False         # Taille fixe pour des performances optimales
        )
        print(f"✅ Succès ! Le modèle ONNX optimisé est sauvegardé ici : {exported_path}")
    except Exception as e:
        print(f"❌ Erreur lors de l'exportation ONNX : {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convertir un modèle YOLOv8 .pt vers .onnx optimisé pour CPU.")
    parser.add_argument("--model", type=str, default="backend/ai_models/best.pt", help="Chemin vers le fichier .pt")
    parser.add_argument("--imgsz", type=int, default=1280, help="Taille de l'image (défaut: 1280)")
    args = parser.parse_args()
    
    convert_model(args.model, args.imgsz)
