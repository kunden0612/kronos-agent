import json
import os
from typing import Optional

try:
    from tools.registry import registry
    HERMES_TOOLS_AVAILABLE = True
except ImportError:
    HERMES_TOOLS_AVAILABLE = False
    registry = None

from ..services.kronos_client import kronos_client


def check_kronos_requirements() -> bool:
    """检查 Kronos 服务是否可用"""
    return True


async def kronos_predict_tool(
    symbol: str,
    pred_len: int = 5,
    model_name: Optional[str] = None,
    lookback: int = 400,
    freq: str = "daily",
    sample_count: int = 5,
    T: float = 1.0,
    top_p: float = 0.9,
    task_id: Optional[str] = None
) -> str:
    """
    使用 Kronos 模型预测金融资产的未来走势。
    
    Args:
        symbol: 资产代码，如 "600519.SH" (茅台), "AAPL" (苹果), "BTC/USDT" (比特币)
        pred_len: 预测长度（交易日数量），默认5天
        model_name: 模型名称，默认使用 Kronos-mini
        lookback: 历史回看窗口长度，默认400天
        freq: 频率，支持 daily, 1h, 5min 等
        sample_count: 采样路径数，默认5条
        T: 采样温度，默认1.0
        top_p: 核采样概率，默认0.9
    
    Returns:
        JSON 格式的预测结果，包含 OHLCV 数据、置信区间和 AI 解读
    """
    try:
        result = await kronos_client.predict(
            symbol=symbol,
            pred_len=pred_len,
            model_name=model_name,
            lookback=lookback,
            freq=freq,
            sample_count=sample_count,
            T=T,
            top_p=top_p
        )
        
        return json.dumps({
            "success": True,
            "symbol": symbol,
            "predictions": result.get("predictions", []),
            "interpretation": result.get("interpretation", ""),
            "risk_warning": result.get("risk_warning", ""),
            "duration_ms": result.get("duration_ms", 0)
        }, ensure_ascii=False, indent=2)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e),
            "symbol": symbol
        }, ensure_ascii=False)


async def kronos_batch_predict_tool(
    symbols: list,
    pred_len: int = 5,
    model_name: Optional[str] = None,
    lookback: int = 400,
    freq: str = "daily",
    sample_count: int = 5,
    task_id: Optional[str] = None
) -> str:
    """
    批量预测多个金融资产的未来走势。
    
    Args:
        symbols: 资产代码列表，如 ["600519.SH", "AAPL", "BTC/USDT"]
        pred_len: 预测长度（交易日数量），默认5天
        model_name: 模型名称，默认使用 Kronos-mini
        lookback: 历史回看窗口长度，默认400天
        freq: 频率，支持 daily, 1h, 5min 等
        sample_count: 采样路径数，默认5条
    
    Returns:
        JSON 格式的批量预测结果
    """
    try:
        results = []
        for symbol in symbols:
            result = await kronos_client.predict(
                symbol=symbol,
                pred_len=pred_len,
                model_name=model_name,
                lookback=lookback,
                freq=freq,
                sample_count=sample_count
            )
            results.append({
                "symbol": symbol,
                "status": "success",
                "predictions": result.get("predictions", []),
                "interpretation": result.get("interpretation", "")
            })
        
        return json.dumps({
            "success": True,
            "total": len(symbols),
            "completed": len(results),
            "results": results
        }, ensure_ascii=False, indent=2)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e),
            "symbols": symbols
        }, ensure_ascii=False)


if HERMES_TOOLS_AVAILABLE:
    registry.register(
        name="kronos_predict",
        toolset="kronos",
        schema={
            "name": "kronos_predict",
            "description": "使用 Kronos 深度学习模型预测金融资产的未来走势。支持 A 股（如茅台 600519.SH）、美股（如苹果 AAPL）、加密货币（如比特币 BTC/USDT）。返回 OHLCV 数据、置信区间和 AI 解读。",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "资产代码，例如：600519.SH（茅台）、AAPL（苹果）、BTC/USDT（比特币）"
                    },
                    "pred_len": {
                        "type": "integer",
                        "description": "预测长度（交易日数量）",
                        "default": 5
                    },
                    "model_name": {
                        "type": "string",
                        "description": "模型名称，可选：NeoQuasar/Kronos-mini, NeoQuasar/Kronos-small, NeoQuasar/Kronos-base",
                        "default": "NeoQuasar/Kronos-mini"
                    },
                    "lookback": {
                        "type": "integer",
                        "description": "历史回看窗口长度（天数）",
                        "default": 400
                    },
                    "freq": {
                        "type": "string",
                        "description": "数据频率，如 daily, 1h, 5min",
                        "default": "daily"
                    },
                    "sample_count": {
                        "type": "integer",
                        "description": "采样路径数（用于计算置信区间）",
                        "default": 5
                    },
                    "T": {
                        "type": "number",
                        "description": "采样温度",
                        "default": 1.0
                    },
                    "top_p": {
                        "type": "number",
                        "description": "核采样概率",
                        "default": 0.9
                    }
                },
                "required": ["symbol"]
            }
        },
        handler=lambda args, **kw: kronos_predict_tool(
            symbol=args.get("symbol"),
            pred_len=args.get("pred_len", 5),
            model_name=args.get("model_name"),
            lookback=args.get("lookback", 400),
            freq=args.get("freq", "daily"),
            sample_count=args.get("sample_count", 5),
            T=args.get("T", 1.0),
            top_p=args.get("top_p", 0.9),
            task_id=kw.get("task_id")
        ),
        check_fn=check_kronos_requirements,
        requires_env=[],
    )
    
    registry.register(
        name="kronos_batch_predict",
        toolset="kronos",
        schema={
            "name": "kronos_batch_predict",
            "description": "批量预测多个金融资产的未来走势，提高效率。适用于分析投资组合或多个相关资产。",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbols": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "资产代码列表"
                    },
                    "pred_len": {
                        "type": "integer",
                        "description": "预测长度（交易日数量）",
                        "default": 5
                    },
                    "model_name": {
                        "type": "string",
                        "description": "模型名称",
                        "default": "NeoQuasar/Kronos-mini"
                    },
                    "lookback": {
                        "type": "integer",
                        "description": "历史回看窗口长度（天数）",
                        "default": 400
                    },
                    "freq": {
                        "type": "string",
                        "description": "数据频率",
                        "default": "daily"
                    },
                    "sample_count": {
                        "type": "integer",
                        "description": "采样路径数",
                        "default": 5
                    }
                },
                "required": ["symbols"]
            }
        },
        handler=lambda args, **kw: kronos_batch_predict_tool(
            symbols=args.get("symbols"),
            pred_len=args.get("pred_len", 5),
            model_name=args.get("model_name"),
            lookback=args.get("lookback", 400),
            freq=args.get("freq", "daily"),
            sample_count=args.get("sample_count", 5),
            task_id=kw.get("task_id")
        ),
        check_fn=check_kronos_requirements,
        requires_env=[],
    )
