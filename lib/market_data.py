"""
MARKET DATA API
Wrapper for yfinance with retry logic and error handling
"""
import time
import pandas as pd
import yfinance as yf
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from lib.logger import setup_logger
from config.config import RETRY_ATTEMPTS, RETRY_DELAY, REQUEST_TIMEOUT

log = setup_logger(__name__)


def retry_on_failure(func):
    """Decorator for retry logic"""
    def wrapper(*args, **kwargs):
        for attempt in range(RETRY_ATTEMPTS):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if attempt < RETRY_ATTEMPTS - 1:
                    log.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {RETRY_DELAY}s...")
                    time.sleep(RETRY_DELAY)
                else:
                    log.error(f"All {RETRY_ATTEMPTS} attempts failed for {func.__name__}")
                    raise
        return None
    return wrapper


@retry_on_failure
def download_daily_data(symbols: List[str], period: str = "1y") -> Dict[str, pd.DataFrame]:
    """
    Download daily OHLCV data for multiple symbols
    
    Args:
        symbols: List of stock symbols
        period: Data period (e.g., "1y", "6mo")
    
    Returns:
        Dict of {symbol: DataFrame}
    """
    data = {}
    for symbol in symbols:
        try:
            ticker = f"{symbol}.NS"
            df = yf.download(ticker, period=period, progress=False, auto_adjust=True)
            
            if df.empty or len(df) < 50:
                log.debug(f"{symbol}: Insufficient data")
                continue
            
            df = df[["Open", "High", "Low", "Close", "Volume"]].dropna()
            data[symbol] = df
            
        except Exception as e:
            log.warning(f"{symbol}: Download failed - {e}")
    
    return data


@retry_on_failure
def download_intraday_data(
    symbols: List[str],
    days_back: int = 30,
    interval: str = "30m"
) -> Dict[str, pd.DataFrame]:
    """
    Download intraday data with 60-day limit handling
    
    Args:
        symbols: List of stock symbols
        days_back: Trading days to fetch
        interval: Data interval (e.g., "30m", "15m")
    
    Returns:
        Dict of {symbol: DataFrame}
    """
    end = datetime.now()
    # CRITICAL FIX: yfinance intraday limit is 60 days
    calendar_days = min(int(days_back * 1.4), 59)  # 1.4x for weekends, cap at 59
    start = end - timedelta(days=calendar_days)
    
    data = {}
    for symbol in symbols:
        try:
            ticker = f"{symbol}.NS"
            df = yf.download(
                ticker,
                start=start,
                end=end,
                interval=interval,
                progress=False,
                auto_adjust=True
            )
            
            if df.empty or len(df) < 20:
                log.debug(f"{symbol}: Insufficient intraday data")
                continue
            
            df.index = pd.to_datetime(df.index).tz_localize(None)
            df = df[["Open", "High", "Low", "Close", "Volume"]].dropna()
            data[symbol] = df
            
        except Exception as e:
            log.warning(f"{symbol}: Intraday download failed - {e}")
    
    return data


@retry_on_failure
def download_nifty_intraday(days_back: int = 30, interval: str = "30m") -> pd.DataFrame:
    """Download Nifty 50 intraday data"""
    end = datetime.now()
    calendar_days = min(int(days_back * 1.4), 59)
    start = end - timedelta(days=calendar_days)
    
    try:
        df = yf.download(
            "^NSEI",
            start=start,
            end=end,
            interval=interval,
            progress=False,
            auto_adjust=True
        )
        
        if df.empty:
            return pd.DataFrame()
        
        df.index = pd.to_datetime(df.index).tz_localize(None)
        return df[["Open", "High", "Low", "Close", "Volume"]].dropna()
    
    except Exception as e:
        log.warning(f"Nifty download failed: {e}")
        return pd.DataFrame()


@retry_on_failure
def get_current_price(symbol: str) -> Optional[float]:
    """Get current market price for a symbol"""
    try:
        ticker = yf.Ticker(f"{symbol}.NS")
        data = ticker.history(period="1d")
        if not data.empty:
            return float(data['Close'].iloc[-1])
    except Exception as e:
        log.warning(f"{symbol}: Failed to get current price - {e}")
    return None


@retry_on_failure
def get_current_prices(symbols: List[str]) -> Dict[str, float]:
    """Get current prices for multiple symbols"""
    prices = {}
    for symbol in symbols:
        price = get_current_price(symbol)
        if price:
            prices[symbol] = price
    return prices


@retry_on_failure
def get_market_indicators() -> Dict[str, float]:
    """Get Nifty and VIX current values"""
    indicators = {}
    
    try:
        nifty = yf.Ticker("^NSEI")
        nifty_data = nifty.history(period="1d")
        if not nifty_data.empty:
            indicators['nifty'] = float(nifty_data['Close'].iloc[-1])
    except Exception as e:
        log.warning(f"Failed to get Nifty: {e}")
    
    try:
        vix = yf.Ticker("^INDIAVIX")
        vix_data = vix.history(period="1d")
        if not vix_data.empty:
            indicators['vix'] = float(vix_data['Close'].iloc[-1])
    except Exception as e:
        log.warning(f"Failed to get VIX: {e}")
    
    return indicators


# Compatibility alias for older callers
def download_data(symbols: List[str], period: str = "1y") -> Dict[str, pd.DataFrame]:
    """Backward-compatible alias for download_daily_data"""
    return download_daily_data(symbols, period=period)
