#!/usr/bin/env python3
"""Test if all imports work"""

print("Testing imports...")

try:
    from config.config import DAYTRADE_CAPITAL, MOMENTUM_CAPITAL
    print("✅ Config imported")
except Exception as e:
    print(f"❌ Config failed: {e}")

try:
    from lib.state_manager import StateManager
    print("✅ State Manager imported")
except Exception as e:
    print(f"❌ State Manager failed: {e}")

try:
    from lib.market_data import download_data
    print("✅ Market Data imported")
except Exception as e:
    print(f"❌ Market Data failed: {e}")

try:
    from lib.portfolio_manager import PortfolioManager
    print("✅ Portfolio Manager imported")
except Exception as e:
    print(f"❌ Portfolio Manager failed: {e}")

try:
    from lib.risk_manager import RiskManager
    print("✅ Risk Manager imported")
except Exception as e:
    print(f"❌ Risk Manager failed: {e}")

try:
    from lib.logger import setup_logger
    print("✅ Logger imported")
except Exception as e:
    print(f"❌ Logger failed: {e}")

try:
    from lib.telegram_notifier import send_message
    print("✅ Telegram Notifier imported")
except Exception as e:
    print(f"❌ Telegram Notifier failed: {e}")

print("\nAll imports tested!")