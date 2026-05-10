import * as ort from 'onnxruntime-web';

// Configuration pour WebGPU/WebGL
ort.env.wasm.numThreads = Math.min(4, navigator.hardwareConcurrency || 4);

export interface Detection {
  pathology: string;
  confidence: number;
  fdi?: number; // Dent associée
  bbox: {
    x_min: number;
    y_min: number;
    x_max: number;
    y_max: number;
  };
}

export interface PanoramicResult {
  status: string;
  detections: Detection[];
  processing_time_ms: number;
}

// Les classes cibles Ghost Elite
const CLASSES = [
  "Carie", "Carie Profonde", "Lésion Périapicale", "Dent Incluse",
  // Futures classes
  "Traitement Endodontique", "Implant", "Couronne", "Perte Osseuse", "Tartre"
];

let session: ort.InferenceSession | null = null;

async function loadModel() {
  if (session) return;
  try {
    console.log("Loading ELITE Panoramic Model (WebGPU/WASM)...");
    // Téléchargement depuis le backend (dossier statique)
    session = await ort.InferenceSession.create('/api/static/models/panoramic_model.onnx', {
      executionProviders: ['webgpu', 'webgl', 'wasm']
    });
    console.log("Model loaded successfully!");
  } catch (error) {
    console.error("Failed to load model", error);
    throw error;
  }
}

// Prétraitement d'image (Letterbox)
function preprocess(imageData: ImageData, targetSize = 1280): Float32Array {
  // Simplification pour l'exemple. Il faudrait redimensionner l'image, 
  // appliquer le padding, et normaliser les pixels (0-1).
  // Retourne un Float32Array de la taille [1, 3, targetSize, targetSize]
  const tensorSize = 1 * 3 * targetSize * targetSize;
  return new Float32Array(tensorSize);
}

// Post-traitement (NMS + extraction BBoxes)
function postprocess(output: any): Detection[] {
  // Simulons l'extraction des boîtes YOLO pour le POC
  return [];
}

self.onmessage = async (e: MessageEvent) => {
  const { type, payload } = e.data;

  if (type === 'INIT') {
    try {
      await loadModel();
      self.postMessage({ type: 'INIT_SUCCESS' });
    } catch (err) {
      self.postMessage({ type: 'INIT_ERROR', error: String(err) });
    }
  }

  if (type === 'INFERENCE') {
    if (!session) {
      self.postMessage({ type: 'INFERENCE_ERROR', error: "Model not loaded" });
      return;
    }

    try {
      const startTime = performance.now();
      const { imageData } = payload;
      
      const inputTensor = new ort.Tensor('float32', preprocess(imageData, 1280), [1, 3, 1280, 1280]);
      
      // Inférence
      const feeds: Record<string, ort.Tensor> = {};
      feeds[session.inputNames[0]] = inputTensor;
      
      const results = await session.run(feeds);
      const outputName = session.outputNames[0];
      const outputTensor = results[outputName];

      const detections = postprocess(outputTensor.data);
      
      // Ajout de métadonnées intelligentes (Le Smart Payload)
      const smartPayload = {
        detections,
        metadata: {
          teeth_involved: [...new Set(detections.map(d => d.fdi).filter(Boolean))],
          severity_flags: detections.some(d => d.pathology === 'Carie Profonde') ? 'HIGH' : 'NORMAL'
        }
      };

      const execTime = performance.now() - startTime;
      
      self.postMessage({ 
        type: 'INFERENCE_SUCCESS', 
        result: {
          status: 'SUCCESS',
          detections: smartPayload.detections,
          metadata: smartPayload.metadata,
          processing_time_ms: Math.round(execTime)
        }
      });
      
    } catch (err) {
      self.postMessage({ type: 'INFERENCE_ERROR', error: String(err) });
    }
  }
};
