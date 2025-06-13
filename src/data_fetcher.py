"""
価格データ取得モジュール
"""
import ccxt
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Any
import time
import os

from .utils.logger import setup_logger
from .config import DEFAULT_SYMBOL

logger = setup_logger("data_fetcher")

class DataFetcher:
    """暗号資産の価格データを取得するクラス"""
    
    # フォールバック用の取引所リスト
    FALLBACK_EXCHANGES = ["kraken", "coinbase", "kucoin", "bybit"]
    
    def __init__(self, exchange_id: str = "kraken", symbol: str = DEFAULT_SYMBOL):
        """
        初期化
        
        Args:
            exchange_id: 取引所ID (デフォルト: "kraken")
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
            
            # API設定を作成
            config = {
                'enableRateLimit': True,  # レート制限を有効化
            }
            
            # 取引所に応じたAPIキー設定
            if self.exchange_id.lower() == 'bybit':
                api_key = os.getenv('BYBIT_API_KEY')
                api_secret = os.getenv('BYBIT_API_SECRET')
                
                if api_key and api_secret:
                    config['apiKey'] = api_key
                    config['secret'] = api_secret
                    logger.info(f"Bybit API credentials loaded successfully")
                else:
                    logger.warning(f"Bybit API credentials not found in environment variables")
            
            self.exchange = exchange_class(config)
            logger.info(f"Exchange {self.exchange_id} initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize exchange {self.exchange_id}: {str(e)}")
            raise
    
    def fetch_ohlcv(self, timeframe: str = '1d', limit: int = 100) -> pd.DataFrame:
        """
        指定されたタイムフレームのOHLCVデータを取得
        複数の取引所を試してデータを取得するフォールバックメカニズムを実装
        
        Args:
            timeframe: 時間枠 ('1m', '5m', '15m', '1h', '4h', '1d', '1w', '1M')
            limit: 取得するデータ点の数
            
        Returns:
            pd.DataFrame: OHLCV データ
        """
        # 現在の取引所で試す
        df = self._try_fetch_from_exchange(self.exchange_id, timeframe, limit)
        if not df.empty:
            return df
            
        # 現在の取引所が失敗した場合、フォールバック取引所を試す
        logger.warning(f"{self.exchange_id} failed. Trying fallback exchanges...")
        
        for fallback_exchange in self.FALLBACK_EXCHANGES:
            # 現在の取引所と同じ場合はスキップ
            if fallback_exchange == self.exchange_id:
                continue
                
            logger.info(f"Trying fallback exchange: {fallback_exchange}")
            
            # 取引所を切り替えて試す
            old_exchange_id = self.exchange_id
            self.exchange_id = fallback_exchange
            
            try:
                self._initialize_exchange()
                df = self._try_fetch_from_exchange(fallback_exchange, timeframe, limit)
                
                if not df.empty:
                    logger.info(f"Successfully fetched data from fallback exchange: {fallback_exchange}")
                    return df
            except Exception as e:
                logger.error(f"Fallback exchange {fallback_exchange} failed: {str(e)}")
                
        # すべての取引所が失敗した場合
        logger.error("All exchanges failed to fetch data")
        return pd.DataFrame(columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        
    def _try_fetch_from_exchange(self, exchange_id: str, timeframe: str, limit: int) -> pd.DataFrame:
        """
        指定された取引所からデータを取得する
        
        Args:
            exchange_id: 取引所ID
            timeframe: 時間枠
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
                    logger.info(f"Fetching {timeframe} OHLCV data for {self.symbol} from {exchange_id}")
                    ohlcv = self.exchange.fetch_ohlcv(self.symbol, timeframe, limit=limit)
                    
                    # DataFrameに変換
                    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                    
                    # Unix timestamp をdatetimeに変換
                    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                    
                    # インデックスを設定
                    df.set_index('timestamp', inplace=True)
                    
                    logger.info(f"Successfully fetched {len(df)} {timeframe} candles from {exchange_id}")
                    
                    return df
                except ccxt.NetworkError as e:
                    if attempt < 2:  # 2回目までは再試行
                        logger.warning(f"Network error with {exchange_id}: {str(e)}. Retrying in 2 seconds...")
                        time.sleep(2)
                    else:
                        raise
        
        except Exception as e:
            logger.error(f"Error fetching OHLCV data from {exchange_id}: {str(e)}")
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
