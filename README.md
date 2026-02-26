# Production Trading System

## ✅ Fixed Issues

### Critical Bugs Fixed
1. **Pandas DataFrame Assignment Bug** - Day trade model training failure
2. **yfinance 60-Day Limit** - Intraday data download failures  
3. **Blocking Execution** - Model training blocking other jobs
4. **State File Race Conditions** - Concurrent access corruption
5. **No Retry Logic** - API failures causing job failures

### Architectural Issues Fixed
1. **Infinite While-True Loops** → Replaced with cron jobs
2. **schedule Library Polling** → Replaced with system cron
3. **Blocking 30s Sleep** → Each job runs and exits
4. **State Corruption** → File locking implemented
5. **No Process Isolation** → Each job is independent process

---

## Architecture

### Execution Model
```
OLD (Blocking):
start.py → while True:
              time.sleep(30)
              if time_matches: run_job()
           
NEW (Non-Blocking):
Cron → 09:00 → train_model.py → exit(0)
    → 09:29 → generate_signals.py → exit(0)
    → 09:30 → execute_trades.py → exit(0)
    → 11:15 → close_positions.py → exit(0)
```

### Directory Structure
```
trading-system/
├── config/
│   └── config.py                 # Central configuration
├── core/
│   ├── daytrading_model.py       # XGBoost training (FIXED pandas bug)
│   └── signal_engine.py          # Signal generation
├── engine/
│   ├── train_daytrade_model.py   # Cron: 09:00 IST
│   ├── generate_daytrade_signals.py  # Cron: 09:29 IST
│   ├── execute_daytrade.py       # Cron: 09:30 IST
│   ├── close_daytrade.py         # Cron: 11:15 IST
│   ├── momentum_morning.py       # Cron: 09:20 IST
│   ├── momentum_eod.py           # Cron: 15:20 IST
│   └── momentum_refresh_prices.py # Cron: */5 min
├── lib/
│   ├── state_manager.py          # Thread-safe state with file locking
│   ├── market_data.py            # yfinance wrapper with retry (FIXED 60-day limit)
│   ├── portfolio_manager.py      # Capital management
│   ├── risk_manager.py           # Position sizing
│   └── logger.py                 # Structured logging
├── dashboard/
│   └── app.py                    # Read-only Streamlit dashboard
├── storage/
│   ├── state/                    # JSON state files with locks
│   └── logs/                     # Rotating logs
├── setup.sh                      # Automated setup
├── crontab.txt                   # Cron configuration
├── requirements.txt              # Python dependencies
└── DEPLOYMENT.md                 # Deployment guide
```

---

## Quick Start

```bash
# 1. Setup
chmod +x setup.sh
./setup.sh

# 2. Set environment variables
export TELEGRAM_TOKEN='your_token'
export TELEGRAM_CHAT_ID='your_chat_id'

# 3. Test day trade training
python3 engine/train_daytrade_model.py

# 4. Setup cron
crontab crontab.txt

# 5. Start dashboard (optional)
streamlit run dashboard/app.py
```

---

## Cron Schedule

```cron
# IST = UTC + 5:30

# Day Trade
30 3 * * 1-5  python3 engine/train_daytrade_model.py        # 09:00 IST
59 3 * * 1-5  python3 engine/generate_daytrade_signals.py   # 09:29 IST
0  4 * * 1-5  python3 engine/execute_daytrade.py            # 09:30 IST
45 5 * * 1-5  python3 engine/close_daytrade.py              # 11:15 IST

# Momentum
50 3 * * 1-5  python3 engine/momentum_morning.py            # 09:20 IST
50 9 * * 1-5  python3 engine/momentum_eod.py                # 15:20 IST
*/5 3-10 * * 1-5  python3 engine/momentum_refresh_prices.py  # Every 5 min
```

---

## Key Improvements

### 1. No Blocking Execution
- Each job runs independently
- No `while True` loops
- No polling every 30 seconds
- Jobs complete in seconds and exit

### 2. File Locking
```python
class StateManager:
    def _lock(self):
        fcntl.flock(fd, fcntl.LOCK_EX)  # Exclusive lock
        # ... read/write ...
        fcntl.flock(fd, fcntl.LOCK_UN)  # Unlock
```

### 3. Retry Logic
```python
@retry_on_failure  # 3 attempts with 2s delay
def download_data(...):
    return yf.download(...)
```

### 4. Proper Logging
```python
log = setup_logger(__name__)
log.info("Job started")
# Logs to: storage/logs/{job_name}.log
# Auto-rotation at 10MB
```

### 5. Fixed Pandas Bug
```python
# BEFORE (BROKEN):
df["nifty_morn_ret"] = (df["Close"] - df["day_open"]) / df["day_open"]

# AFTER (FIXED):
df["nifty_morn_ret"] = (df["Close"].values - day_open.values) / day_open.values
```

### 6. Fixed yfinance Limit
```python
# BEFORE: days_back * 2 = 70 days (exceeds limit)
# AFTER: min(int(days_back * 1.4), 59) = 42 days (within limit)
```

---

## Monitoring

### Check Job Execution
```bash
# View logs
tail -f storage/logs/train_daytrade.log

# Check cron execution
grep CRON /var/log/syslog

# Verify state
cat storage/state/daytrade_state.json | jq '.model_trained'
```

### Dashboard
```bash
streamlit run dashboard/app.py
# Access at http://localhost:8501
```

---

## Performance

| Job | Duration | Blocking? |
|-----|----------|-----------|
| Train Model | 30-60s | ❌ No (separate process) |
| Generate Signals | 5-10s | ❌ No |
| Execute Trades | 2-5s | ❌ No |
| Close Positions | 5-10s | ❌ No |
| Refresh Prices | 2-5s | ❌ No |

**Total daily compute:** ~2-3 minutes  
**CPU idle time:** 99%+

---

## Production Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for:
- AWS/DigitalOcean setup
- Docker deployment
- Monitoring setup
- Scaling recommendations
- Troubleshooting guide

---

## Migration from Old System

```bash
# 1. Stop old system
pkill -f start.py

# 2. Backup state
cp strategy_state.json storage/state/momentum_state.json.backup
cp daytrade_state.json storage/state/daytrade_state.json.backup

# 3. Start new system
crontab crontab.txt
```

---

## Testing

```bash
# Test each job manually
python3 engine/train_daytrade_model.py
python3 engine/generate_daytrade_signals.py
python3 engine/execute_daytrade.py
python3 engine/close_daytrade.py

# Check exit codes
echo $?  # Should be 0 for success
```

---

## FAQ

**Q: Why not use systemd timers?**  
A: Cron is universal, simpler, and more portable. Systemd timers are equivalent but Linux-specific.

**Q: What if a job fails?**  
A: Jobs are idempotent - you can re-run safely. Logs show errors. Add monitoring/alerts.

**Q: Can I run on Koyeb/Heroku?**  
A: These platforms require web process. Use external cron service (cron-job.org) to trigger HTTP endpoints.

**Q: How to add Telegram alerts?**  
A: Set TELEGRAM_TOKEN and TELEGRAM_CHAT_ID env vars. Jobs will send notifications automatically.

**Q: State file corruption?**  
A: File locking prevents this. If it happens, restore from `.backup_*` files.

---

## License

MIT

---

## Support

For issues, see:
1. Check logs: `storage/logs/*.log`
2. Read DEPLOYMENT.md
3. Test manually: `python3 engine/train_daytrade_model.py`
4. Review state: `cat storage/state/daytrade_state.json`
