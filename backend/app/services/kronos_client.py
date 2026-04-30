import httpx
import logging
from typing import Dict, Any, Optional

from ..core.config import settings

logger = logging.getLogger(__name__)


class KronosClient:
    """Kronos 服务客户端"""
    
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or settings.KRONOS_SERVICE_URL
        self.timeout = 60.0
    
    async def predict(
        self,
        symbol: str,
        pred_len: int,
        model_name: Optional[str] = None,
        lookback: int = 400,
        freq: str = "daily",
        sample_count: int = 5,
        T: float = 1.0,
        top_p: float = 0.9
    ) -> Dict[str, Any]:
        """调用 Kronos 预测接口"""
        url = f"{self.base_url}/api/v1/predict"
        
        payload = {
            "symbol": symbol,
            "pred_len": pred_len,
            "lookback": lookback,
            "freq": freq,
            "sample_count": sample_count,
            "T": T,
            "top_p": top_p
        }
        
        if model_name:
            payload["model_name"] = model_name
        
        logger.info(f"Calling Kronos predict API for {symbol}")
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                result = response.json()
                logger.info(f"Kronos prediction successful for {symbol}")
                return result
        except httpx.HTTPError as e:
            logger.error(f"HTTP error calling Kronos API: {e}")
            raise Exception(f"调用 Kronos 服务失败：{str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error calling Kronos API: {e}")
            raise
    
    async def get_models(self) -> Dict[str, Any]:
        """获取已加载的模型列表"""
        url = f"{self.base_url}/api/v1/models"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error getting models: {e}")
            return {"models": [], "current_model": None}
    
    async def health_check(self) -> Dict[str, Any]:
        """检查 Kronos 服务健康状态"""
        url = f"{self.base_url}/api/v1/health"
        
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.warning(f"Kronos health check failed: {e}")
            return {
                "status": "unhealthy",
                "timestamp": "",
                "models_loaded": []
            }


kronos_client = KronosClient()
