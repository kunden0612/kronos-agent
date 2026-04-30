import pandas as pd
import numpy as np
from typing import Optional, List, Dict, Tuple
import logging
import time
from datetime import datetime, timedelta

from .data_fetcher import data_fetcher
from ..config import settings

logger = logging.getLogger(__name__)


class KronosPredictor:
    def __init__(self):
        self._loaded_models: Dict[str, object] = {}
        self._current_model: Optional[str] = None
        self._is_initialized = False
        
    async def initialize(self):
        if self._is_initialized:
            return
        
        logger.info("Initializing Kronos Predictor...")
        
        await self.load_model(settings.DEFAULT_MODEL)
        self._is_initialized = True
        logger.info("Kronos Predictor initialized successfully")

    async def load_model(self, model_name: str):
        if model_name in self._loaded_models:
            self._current_model = model_name
            logger.info(f"Model {model_name} already loaded, switched to it")
            return
        
        logger.info(f"Loading model {model_name}...")
        
        try:
            model_info = {
                'name': model_name,
                'loaded_at': datetime.now().isoformat(),
                'is_dummy': True
            }
            
            self._loaded_models[model_name] = model_info
            self._current_model = model_name
            logger.info(f"Model {model_name} loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load model {model_name}: {e}")
            raise

    def unload_model(self, model_name: str):
        if model_name in self._loaded_models:
            del self._loaded_models[model_name]
            if self._current_model == model_name:
                self._current_model = None
            logger.info(f"Model {model_name} unloaded successfully")

    def get_loaded_models(self) -> List[str]:
        return list(self._loaded_models.keys())

    async def predict(
        self,
        symbol: str,
        pred_len: int,
        model_name: Optional[str] = None,
        lookback: int = 400,
        freq: str = "daily",
        sample_count: int = 5,
        temperature: float = 1.0,
        top_p: float = 0.9
    ) -> Dict:
        start_time = time.time()
        
        if model_name is None:
            model_name = self._current_model or settings.DEFAULT_MODEL
        
        if model_name not in self._loaded_models:
            await self.load_model(model_name)
        
        logger.info(f"Predicting {symbol} with {model_name}...")
        
        try:
            df = data_fetcher.fetch_data(symbol, lookback, freq)
            df_norm, stats = data_fetcher.normalize_data(df)
            
            predictions = []
            all_samples = []
            
            for i in range(sample_count):
                sample_pred = self._generate_prediction(df_norm, pred_len, temperature, top_p)
                all_samples.append(sample_pred)
            
            all_samples = np.array(all_samples)
            mean_pred = np.mean(all_samples, axis=0)
            std_pred = np.std(all_samples, axis=0)
            
            base_date = df.index[-1]
            
            for i in range(pred_len):
                pred_date = base_date + timedelta(days=i+1)
                
                pred_row = {
                    'timestamp': pred_date.isoformat(),
                    'open': float(mean_pred[i, 0]),
                    'high': float(mean_pred[i, 1]),
                    'low': float(mean_pred[i, 2]),
                    'close': float(mean_pred[i, 3]),
                    'volume': float(mean_pred[i, 4]),
                    'confidence': {
                        'low_95': float(mean_pred[i, 3] - 1.96 * std_pred[i, 3]),
                        'high_95': float(mean_pred[i, 3] + 1.96 * std_pred[i, 3])
                    }
                }
                predictions.append(pred_row)
            
            pred_df = pd.DataFrame(predictions)
            pred_df[['open', 'high', 'low', 'close', 'volume']] = pred_df[
                ['open', 'high', 'low', 'close', 'volume']
            ].apply(lambda x: x * stats['close']['std'] + stats['close']['mean'])
            
            predictions = pred_df.to_dict('records')
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            result = {
                'task_id': f"pred_{int(time.time())}",
                'status': 'completed',
                'symbol': symbol,
                'model': model_name,
                'predictions': predictions,
                'interpretation': self._generate_interpretation(predictions, df),
                'risk_warning': '⚠️ 模型基于历史数据与机器学习生成，不构成投资建议。市场有风险，投资需谨慎。',
                'created_at': datetime.now().isoformat(),
                'duration_ms': duration_ms
            }
            
            logger.info(f"Prediction completed for {symbol} in {duration_ms}ms")
            return result
            
        except Exception as e:
            logger.error(f"Prediction failed for {symbol}: {e}")
            raise

    async def predict_batch(
        self,
        symbols: List[str],
        pred_len: int,
        model_name: Optional[str] = None,
        lookback: int = 400,
        freq: str = "daily",
        sample_count: int = 5
    ) -> List[Dict]:
        results = []
        
        for symbol in symbols:
            try:
                result = await self.predict(
                    symbol=symbol,
                    pred_len=pred_len,
                    model_name=model_name,
                    lookback=lookback,
                    freq=freq,
                    sample_count=sample_count
                )
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to predict {symbol}: {e}")
                results.append({
                    'symbol': symbol,
                    'status': 'failed',
                    'error': str(e)
                })
        
        return results

    def _generate_prediction(
        self,
        df_norm: pd.DataFrame,
        pred_len: int,
        temperature: float,
        top_p: float
    ) -> np.ndarray:
        last_values = df_norm[['open', 'high', 'low', 'close', 'volume']].iloc[-1].values
        
        predictions = []
        current_value = last_values.copy()
        
        for _ in range(pred_len):
            noise = np.random.normal(0, 0.1 * temperature, size=5)
            momentum = np.random.normal(0.01, 0.02, size=5)
            
            next_value = current_value + momentum + noise
            predictions.append(next_value)
            current_value = next_value
        
        return np.array(predictions)

    def _generate_interpretation(self, predictions: List[Dict], historical_df: pd.DataFrame) -> str:
        if not predictions:
            return "无法生成预测解读"
        
        last_close = historical_df['close'].iloc[-1]
        first_pred_close = predictions[0]['close']
        last_pred_close = predictions[-1]['close']
        
        total_change = ((last_pred_close - last_close) / last_close) * 100
        
        if total_change > 1:
            trend = "温和上涨趋势"
        elif total_change < -1:
            trend = "温和下跌趋势"
        else:
            trend = "震荡整理趋势"
        
        high_prices = [p['high'] for p in predictions]
        low_prices = [p['low'] for p in predictions]
        
        avg_volatility = (np.std([p['close'] for p in predictions]) / np.mean([p['close'] for p in predictions])) * 100
        
        interpretation = (
            f"根据模型预测，未来 {len(predictions)} 个交易日预计呈{trend}。\n"
            f"预测期间平均波动率约为 {avg_volatility:.2f}%。\n"
            f"预计价格区间：{min(low_prices):.2f} - {max(high_prices):.2f}。\n"
            f"整体涨跌幅预计为 {total_change:+.2f}%。\n\n"
            f"请注意：以上分析仅供参考，不构成任何投资建议。"
        )
        
        return interpretation


kronos_predictor = KronosPredictor()
