# ChatBI Frontend - Ultimate Cheat Sheet

## Quick Start

```bash
cd /Users/chenjieming/Desktop/chatbi && source chatbi/bin/activate && export DEEPSEEK_API_KEY="key" && pip install streamlit==1.32.2 pandas matplotlib plotly && streamlit run chatbi_frontend.py
```

## Core Commands

| Task | Command |
|-----|------|
| Start the local app | `streamlit run chatbi_frontend.py` |
| Start with the script | `bash start_frontend.sh` |
| Start with Docker | `docker-compose up -d` |
| Show Docker logs | `docker-compose logs -f` |
| Stop Docker | `docker-compose down` |
| Rebuild the image | `docker-compose up -d --build` |

## Required Configuration

```bash
# Set the API key (required)
export DEEPSEEK_API_KEY="your-key-here"

# Verify it is set
echo $DEEPSEEK_API_KEY
```

## Key Files

```text
chatbi/
├── chatbi_frontend.py           <- Main app entry point
├── pipeline_frontend.py         <- Backend adapter
├── Dockerfile                   <- Docker image config
├── docker-compose.yml           <- Container orchestration
├── .streamlit/config.toml       <- UI config
├── QUICK_START.md               <- 5-minute guide
├── FRONTEND_GUIDE.md            <- Detailed feature guide
├── DEPLOYMENT_GUIDE.md          <- Deployment options
└── FRONTEND_README.md           <- Full documentation
```

## Access URLs

| Deployment Mode | URL |
|--------|-----|
| Local | http://localhost:8501 |
| Docker | http://localhost:8501 |
| Docker (Nginx) | http://localhost |
| Cloud example | https://chatbi.streamlit.app |

## Quick Query Examples

```text
Which category has the highest revenue?
Which customers have placed more than 3 orders?
What were the monthly order counts and total amounts in 2024?
Which products have stock below 20 units?
Which brand has the highest positive review rate?
How much have customers in Beijing spent in total?
Rank cities by average order amount.
Which category has the most products?
```

## Deployment Options

```text
Fast         Local run              2 minutes
             Script start
             ↓
Standard     Docker container       5 minutes
             Local Docker
             ↓
Production   Streamlit Cloud        10 minutes
             Railway/Render
             Cloud host (Nginx)
```

## Troubleshooting

| Issue | Solution |
|-----|--------|
| Streamlit is not installed | `pip install streamlit==1.32.2` |
| API key is not set | `export DEEPSEEK_API_KEY="key"` |
| Port is already in use | `streamlit run app.py --server.port 9000` |
| Docker fails to start | `docker-compose down && docker-compose up -d --build` |
| Queries fail | Check logs: `docker-compose logs chatbi-frontend` |

## Documentation Guide

```text
Want to get started in 5 minutes?  -> QUICK_START.md
Want to learn every feature?       -> FRONTEND_GUIDE.md
Want to deploy online?             -> DEPLOYMENT_GUIDE.md
Want the full project overview?    -> FRONTEND_README.md
Want deeper technical details?     -> proposal.md
```

## Common Customizations

### Change the color theme
Edit `.streamlit/config.toml`:

```toml
[theme]
primaryColor = "#667eea"
```

### Change the layout

```python
# Change this in chatbi_frontend.py
st.set_page_config(layout="centered")  # default was "wide"
```

### Change the port

```bash
streamlit run chatbi_frontend.py --server.port 9000
```

## Data Export

- CSV format: click the "Download CSV" button
- JSON format: use the "Export Options" panel in the sidebar
- Charts: right-click and save the chart

## Advanced Configuration

### Increase upload size / timeout-related limits
`.streamlit/config.toml`:

```toml
[client]
maxUploadSize = 200
```

### Enable dark mode
`.streamlit/config.toml`:

```toml
[theme]
base = "dark"
```

### Disable the toolbar
`.streamlit/config.toml`:

```toml
[client]
toolbarMode = "minimal"
```

## Performance Metrics

| Item | Value | Notes |
|-----|----|----|
| Startup time | 3-5s | First load may be slower |
| Query latency | 0.5-2s | Depends on the LLM |
| Concurrent users | 10+ | Depends on hardware |
| Database size | ~10MB | SQLite |

## Production Checklist

- [ ] Configure the API key
- [ ] Set up HTTPS/SSL
- [ ] Configure an Nginx reverse proxy
- [ ] Enable logging
- [ ] Schedule regular backups
- [ ] Configure monitoring and alerts
- [ ] Optimize memory usage
- [ ] Run concurrency tests

## Quick FAQ

**Q: Does it support Windows?**  
A: Yes, use `start_frontend.bat`.

**Q: Does it support mobile devices?**  
A: Yes, the UI is fully responsive.

**Q: Can it be used offline?**  
A: It requires the DeepSeek API, so network access is needed.

**Q: Where is the performance bottleneck?**  
A: In the LLM API response, not the frontend.

**Q: Will data be uploaded to the cloud?**  
A: No. The database stays local; only the query request is sent to DeepSeek.

## Common Use Cases

| Use Case | Recommended Setup |
|-----|--------|
| Personal learning | Local run |
| Internal team usage | Local Docker |
| Public demo | Streamlit Cloud |
| Enterprise deployment | Cloud host + Nginx |
| High concurrency | FastAPI + Kubernetes |

## Best Practices

**DO**
- Store API keys in environment variables
- Back up the SQLite database regularly
- Use debug mode when you need to inspect execution flow
- Use Docker to keep environments consistent
- Review performance metrics regularly

**DON'T**
- Hardcode API keys
- Expose sensitive information in code
- Use root/admin accounts directly
- Ignore logs and monitoring
- Use `debug=True` in production

## One-Click Command Set

```bash
# Start the app
streamlit run chatbi_frontend.py

# Start with debug logging
streamlit run --logger.level=debug chatbi_frontend.py

# Start Docker
docker-compose up -d --build

# View Docker logs
docker-compose logs -f

# Restart Docker
docker-compose restart

# Stop Docker
docker-compose down

# Enter the Docker container
docker-compose exec chatbi-frontend bash

# Export the database
docker-compose exec chatbi-frontend sqlite3 Ecommerce.db ".dump" > backup.sql

# Clear cache
docker-compose exec chatbi-frontend rm -rf .streamlit/cache
```

## Learning Resources

- Streamlit docs: https://docs.streamlit.io
- Python docs: https://docs.python.org
- SQL tutorial: https://sqlzoo.net
- Prompt engineering reference: https://www.prompt.tips

---

**Last Updated**: 2026-04-04  
**Version**: 1.0.0  
**Status**: Production ready
