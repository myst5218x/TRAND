"""
価格データ取得モジュール
"""
import ccxt
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Any
import time

from .utils.logger import setup_logger
from .config import DEFAULT_SYMBOL

logger = setup_logger("data_fetcher")

class DataFetcher:
    """暗号資産の価格データを取得するクラス"""
    
    def __init__(self, exchange_id: str = "binance", symbol: str = DEFAULT_SYMBOL):
        """
        初期化
        
        Args:
            exchange_id: 取引所ID (デフォルト: "binance")
            symbol: 通貨ペア (デフォルト: DEFAULT_SYMBOL)
        """
        self.exchange_id = exchange_id
        self.symbol = symbol
        self.exchange = None
        self._initialize_exchange()
        
    def _initialize_exchange(self) -> None:
        """取引所APIを初期化"""
        try:
            # ccxtライブラリで取引所インスタンスを作成
            exchange_class = getattr(ccxt, self.exchange_id)
            self.exchange = exchange_class({
                'enableRateLimit': True,  # レート制限を有効化
            })
            logger.info(f"Exchange {self.exchange_id} initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize exchange {self.exchange_id}: {str(e)}")
            raise
    
    def fetch_ohlcv(self, timeframe: str = '1d', limit: int = 100) -> pd.DataFrame:
        """
        指定されたタイムフレームのOHLCVデータを取得
        
        Args:
            timeframe: 時間枠 ('1m', '5m', '15m', '1h', '4h', '1d', '1w', '1M')
            limit: 取得するデータ点の数
            
        Returns:
            pd.DataFrame: OHLCV データ
        """
        if not self.exchange:
            self._initialize_exchange()
            
        try:
            # 3回までリトライ
            for attempt in range(3):
                try:
                    logger.info(f"Fetching {timeframe} OHLCV data for {self.symbol} from {self.exchange_id}")
                    ohlcv = self.exchange.fetch_ohlcv(self.symbol, timeframe, limit=limit)
                    
                    # DataFrameに変換
                    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                    
                    # Unix timestamp をdatetimeに変換
                    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                    
                    # インデックスを設定
                    df.set_index('timestamp', inplace=True)
                    
                    logger.info(f"Successfully fetched {len(df)} {timeframe} candles")
                    
                    return df
                except ccxt.NetworkError as e:
                    if attempt < 2:  # 2回目までは再試行
                        logger.warning(f"Network error: {str(e)}. Retrying in 2 seconds...")
                        time.sleep(2)
                    else:
                        raise
        
        except Exception as e:
            logger.error(f"Error fetching OHLCV data: {str(e)}")
            # エラー時は空のDataFrameを返す
            return pd.DataFrame(columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    
    def fetch_multi_timeframe_data(self, timeframes: List[str]) -> Dict[str, pd.DataFrame]:
        """
        複数のタイムフレームのデータを取得
        
        Args:
            timeframes: タイムフレームのリスト
            
        Returns:
            Dict[str, pd.DataFrame]: タイムフレームごとのOHLCVデータ
        """
        result = {}
        
        for tf in timeframes:
            # タイムフレームに応じてデータ量を調整
            if tf == '1d':
                limit = 200  # 約200日分
            elif tf == '4h':
                limit = 500  # 約83日分
            elif tf == '1h':
                limit = 500  # 約20日分
            else:  # 短期間のタイムフレーム
                limit = 500
                
            df = self.fetch_ohlcv(tf, limit)
            if not df.empty:
                result[tf] = df
                
        return result
    
    def get_current_price(self) -> float:
        """
        現在の価格を取得
        
        Returns:
            float: 現在の価格
        """
        try:
            ticker = self.exchange.fetch_ticker(self.symbol)
            return ticker['last']
        except Exception as e:
            logger.error(f"Error fetching current price: {str(e)}")
            return 0.0
