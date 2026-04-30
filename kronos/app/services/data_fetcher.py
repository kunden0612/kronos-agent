import pandas as pd
import numpy as np
from typing import Optional, Tuple, List
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class AssetType(Enum):
    A_SHARE = "a_share"
    US_STOCK = "us_stock"
    CRYPTO = "crypto"


class DataFetcher:
    def __init__(self):
        self._akshare_initialized = False
        self._yfinance_initialized = False
        self._ccxt_initialized = False

    def _init_akshare(self):
        if not self._akshare_initialized:
            try:
                import akshare as ak
                self.ak = ak
                self._akshare_initialized = True
                logger.info("AkShare initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize AkShare: {e}")
                raise

    def _init_yfinance(self):
        if not self._yfinance_initialized:
            try:
                import yfinance as yf
                self.yf = yf
                self._yfinance_initialized = True
                logger.info("YFinance initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize YFinance: {e}")
                raise

    def _init_ccxt(self):
        if not self._ccxt_initialized:
            try:
                import ccxt
                self.ccxt = ccxt
                self._ccxt_initialized = True
                logger.info("CCXT initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize CCXT: {e}")
                raise

    def _detect_asset_type(self, symbol: str) -> AssetType:
        if symbol.endswith('.SH') or symbol.endswith('.SZ'):
            return AssetType.A_SHARE
        elif '/' in symbol or symbol.isupper() and len(symbol) <= 10:
            return AssetType.CRYPTO
        else:
            return AssetType.US_STOCK

    def _fetch_a_share(self, symbol: str, period: str = "daily", count: int = 400) -> pd.DataFrame:
        self._init_akshare()
        try:
            if symbol.endswith('.SH'):
                symbol_code = symbol.replace('.SH', '')
            elif symbol.endswith('.SZ'):
                symbol_code = symbol.replace('.SZ', '')
            else:
                symbol_code = symbol
            
            df = self.ak.stock_zh_a_hist(symbol=symbol_code, period="daily", 
                                        start_date="", end_date="", adjust="")
            
            df = df.rename(columns={
                '日期': 'date',
                '开盘': 'open',
                '最高': 'high',
                '最低': 'low',
                '收盘': 'close',
                '成交量': 'volume',
                '成交额': 'amount'
            })
            
            df = df.set_index('date')
            df = df.sort_index(ascending=True)
            df = df.tail(count)
            
            return df[['open', 'high', 'low', 'close', 'volume']]
        except Exception as e:
            logger.error(f"Failed to fetch A-share data for {symbol}: {e}")
            raise

    def _fetch_us_stock(self, symbol: str, period: str = "daily", count: int = 400) -> pd.DataFrame:
        self._init_yfinance()
        try:
            ticker = self.yf.Ticker(symbol)
            df = ticker.history(period=f"{count}d")
            
            df = df.rename(columns={
                'Open': 'open',
                'High': 'high',
                'Low': 'low',
                'Close': 'close',
                'Volume': 'volume'
            })
            
            df = df.sort_index(ascending=True)
            df = df.tail(count)
            
            return df[['open', 'high', 'low', 'close', 'volume']]
        except Exception as e:
            logger.error(f"Failed to fetch US stock data for {symbol}: {e}")
            raise

    def _fetch_crypto(self, symbol: str, period: str = "1d", count: int = 400) -> pd.DataFrame:
        self._init_ccxt()
        try:
            exchange = self.ccxt.binance({'enableRateLimit': True})
            
            if '/' not in symbol:
                symbol = f"{symbol}/USDT"
            
            timeframe_map = {
                '1min': '1m',
                '5min': '5m',
                '15min': '15m',
                '1h': '1h',
                'daily': '1d',
                'weekly': '1w'
            }
            
            timeframe = timeframe_map.get(period, '1d')
            
            ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=count)
            
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['date'] = pd.to_datetime(df['timestamp'], unit='ms')
            df = df.set_index('date')
            df = df.sort_index(ascending=True)
            
            return df[['open', 'high', 'low', 'close', 'volume']]
        except Exception as e:
            logger.error(f"Failed to fetch crypto data for {symbol}: {e}")
            raise

    def fetch_data(self, symbol: str, lookback: int = 400, freq: str = "daily") -> pd.DataFrame:
        asset_type = self._detect_asset_type(symbol)
        
        if asset_type == AssetType.A_SHARE:
            df = self._fetch_a_share(symbol, freq, lookback)
        elif asset_type == AssetType.US_STOCK:
            df = self._fetch_us_stock(symbol, freq, lookback)
        else:
            df = self._fetch_crypto(symbol, freq, lookback)
        
        df = self._clean_data(df)
        return df

    def _clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        for col in required_columns:
            if col not in df.columns:
                df[col] = np.nan
        
        df = df.ffill().bfill()
        
        df = df.replace([np.inf, -np.inf], np.nan)
        df = df.dropna()
        
        return df

    def normalize_data(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, dict]:
        df_norm = df.copy()
        stats = {}
        
        for col in ['open', 'high', 'low', 'close', 'volume']:
            if col in df.columns:
                mean = df[col].mean()
                std = df[col].std()
                if std == 0:
                    std = 1
                df_norm[col] = (df[col] - mean) / std
                stats[col] = {'mean': mean, 'std': std}
        
        return df_norm, stats

    def denormalize_data(self, df_norm: pd.DataFrame, stats: dict) -> pd.DataFrame:
        df = df_norm.copy()
        
        for col in ['open', 'high', 'low', 'close', 'volume']:
            if col in df.columns and col in stats:
                mean = stats[col]['mean']
                std = stats[col]['std']
                df[col] = df[col] * std + mean
        
        return df


data_fetcher = DataFetcher()
