# Railway Procfile
# Defines processes that run on Railway

# Main scheduler (runs trading jobs at scheduled times)
worker: python3 railway/scheduler.py

# Telegram bot (24/7 monitoring and commands)
telegram: python3 services/telegram_bot.py

# Dashboard (web interface - optional)
web: streamlit run dashboard/app.py --server.port=$PORT --server.address=0.0.0.0
