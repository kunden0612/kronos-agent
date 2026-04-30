from fastapi import APIRouter, HTTPException
from datetime import datetime
import logging

from ....models.schemas import (
    PredictRequest,
    BatchPredictRequest,
    PredictResponse,
    ModelLoadRequest,
    ModelUnloadRequest,
    ModelsResponse,
    HealthResponse
)
from ....services.kronos_predictor import kronos_predictor

router = APIRouter(prefix="/api/v1", tags=["predict"])
logger = logging.getLogger(__name__)


@router.on_event("startup")
async def startup_event():
    await kronos_predictor.initialize()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        models_loaded=kronos_predictor.get_loaded_models()
    )


@router.get("/models", response_model=ModelsResponse)
async def get_models():
    try:
        models = kronos_predictor.get_loaded_models()
        return ModelsResponse(
            models=models,
            current_model=kronos_predictor._current_model
        )
    except Exception as e:
        logger.error(f"Failed to get models: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/models/load")
async def load_model(request: ModelLoadRequest):
    try:
        await kronos_predictor.load_model(request.model_name)
        return {"status": "success", "message": f"Model {request.model_name} loaded successfully"}
    except Exception as e:
        logger.error(f"Failed to load model {request.model_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/models/unload")
async def unload_model(request: ModelUnloadRequest):
    try:
        kronos_predictor.unload_model(request.model_name)
        return {"status": "success", "message": f"Model {request.model_name} unloaded successfully"}
    except Exception as e:
        logger.error(f"Failed to unload model {request.model_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/predict", response_model=PredictResponse)
async def predict(request: PredictRequest):
    try:
        result = await kronos_predictor.predict(
            symbol=request.symbol,
            pred_len=request.pred_len,
            model_name=request.model_name,
            lookback=request.lookback,
            freq=request.freq,
            sample_count=request.sample_count,
            temperature=request.T,
            top_p=request.top_p
        )
        return PredictResponse(**result)
    except Exception as e:
        logger.error(f"Prediction failed for {request.symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/predict/batch")
async def predict_batch(request: BatchPredictRequest):
    try:
        results = await kronos_predictor.predict_batch(
            symbols=request.symbols,
            pred_len=request.pred_len,
            model_name=request.model_name,
            lookback=request.lookback,
            freq=request.freq,
            sample_count=request.sample_count
        )
        return {"status": "success", "results": results}
    except Exception as e:
        logger.error(f"Batch prediction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
