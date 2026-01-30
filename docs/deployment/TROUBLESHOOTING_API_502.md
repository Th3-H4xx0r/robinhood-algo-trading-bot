# Troubleshooting: API unreachable / 502 Bad Gateway

When `http://YOUR_IP:8000/docs` can't be reached and the frontend shows **502 Bad Gateway** for `/api/v1/backtests`, the API container is not reachable (from the host or from the frontend container).

## 1. Check the API container is running

On the VPS (or wherever Docker/Dokploy runs):

```bash
# List containers; look for trading-bot-api
docker ps -a | grep -E "api|trading"

# Or with compose
docker-compose -f docker-compose.full.yml ps
```

- If **trading-bot-api** is **missing** or **Exited**, the API is not running.
- If it shows **Up**, go to step 2.

## 2. Check API logs (if container exits or 502 persists)

```bash
# Last 100 lines
docker logs trading-bot-api --tail 100

# Follow live
docker logs trading-bot-api -f
```

Common failures:

- **ImportError / ModuleNotFoundError** – e.g. `trading_bot` or `api` path wrong; fix `PYTHONPATH` or image build.
- **Database error** – e.g. SQLite path not writable; ensure `api-data` volume or `./data` mount exists and the app has write access.
- **Port already in use** – something else is using 8000; stop it or change the API port in compose.

## 3. Open firewall for ports 8000 and 3002

If the API is running but you still can't reach it from your browser, the host firewall may be blocking ports:

```bash
# UFW (Ubuntu/Debian)
sudo ufw allow 8000/tcp
sudo ufw allow 3002/tcp
sudo ufw reload
sudo ufw status

# Or allow from a specific IP only
sudo ufw allow from YOUR_OFFICE_IP to any port 8000
sudo ufw allow from YOUR_OFFICE_IP to any port 3002
```

On cloud VPS (Hetzner, AWS, etc.), also open **8000** and **3002** in the provider’s **security group / firewall** (inbound rules).

## 4. Test from the host

From the same machine that runs Docker:

```bash
# API health (should return JSON)
curl -s http://localhost:8000/api/v1/health/healthz

# API docs (should return HTML)
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/docs
```

- If **localhost:8000** works but **YOUR_IP:8000** does not → firewall or port publishing (step 3 and 5).
- If **localhost:8000** fails → API container not running or not listening (step 1 and 2).

## 5. Dokploy: expose ports 8000 and 3002

If you deploy with **Dokploy**, it may not publish every port from the compose file.

- In the Dokploy app, check **Ports** / **Publish** (or similar).
- Ensure **8000** (API) and **3002** (frontend) are **exposed** or **published** to the host.
- Save and redeploy so the proxy/ingress or host ports match.

## 6. Frontend 502 but direct :8000 works

If `http://YOUR_IP:8000/docs` works but `http://YOUR_IP:3002/api/v1/backtests` returns 502:

- The frontend container cannot reach the API (e.g. wrong network).
- Ensure **frontend** and **api** use the **same Docker network** (e.g. `trading-network` in `docker-compose.full.yml`).
- Restart both so they attach to the same network:

  ```bash
  docker-compose -f docker-compose.full.yml up -d api frontend
  ```

## Quick checklist

| Check | Command / action |
|-------|------------------|
| API container up | `docker ps \| grep trading-bot-api` |
| API logs | `docker logs trading-bot-api --tail 50` |
| API responds on host | `curl -s http://localhost:8000/api/v1/health/healthz` |
| Firewall | `sudo ufw allow 8000/tcp && sudo ufw allow 3002/tcp && sudo ufw reload` |
| Dokploy ports | Expose 8000 and 3002 in Dokploy UI |

After fixing, reload the frontend (e.g. `http://YOUR_IP:3002`) and try `/api/v1/backtests` again.
