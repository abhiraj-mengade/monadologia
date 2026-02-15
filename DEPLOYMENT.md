# Deployment Guide for VPS

## Quick Start

1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd monadologia
   ```

2. **Start the server (auto-installs dependencies):**
   ```bash
   ./start_server.sh
   ```
   
   The script will:
   - Create a virtual environment (if needed)
   - Install all dependencies from `requirements.txt`
   - Start the server **in background** on port 3335
   - Save logs to `monadologia.log`
   
   Or manually:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   uvicorn server.main:app --host 0.0.0.0 --port 3335
   ```

3. **Server Management:**
   ```bash
   ./start_server.sh      # Start server in background
   ./stop_server.sh       # Stop server
   ./restart_server.sh    # Restart server
   ./update_server.sh     # Pull latest code and restart
   ./server_status.sh     # Check status and view logs
   tail -f monadologia.log # Follow logs in real-time
   ```

4. **Access the server:**
   - API: `http://YOUR_VPS_IP:3335`
   - API Docs: `http://YOUR_VPS_IP:3335/docs`
   - Root endpoint: `http://YOUR_VPS_IP:3335/`

## Updating the Server

When new code is pushed to the repository:

```bash
./update_server.sh
```

This script will:
1. Stop the running server (if running)
2. Pull the latest changes from git
3. Reinstall dependencies if `requirements.txt` changed
4. Restart the server automatically

**Manual update process:**
```bash
# Stop server
./stop_server.sh

# Pull changes
git pull

# Reinstall dependencies if needed
source venv/bin/activate
pip install -r requirements.txt

# Restart
./start_server.sh
```

## Configuration

### Port
Default port is **3335** (configured for Oracle VPS). To change:
```bash
PORT=8080 uvicorn server.main:app --host 0.0.0.0
```

### Host
Default host is `0.0.0.0` (listens on all interfaces). To change:
```bash
HOST=0.0.0.0 uvicorn server.main:app --port 3335
```

### Auto-tick Interval
World advances automatically every N seconds (default: 30):
```bash
TICK_INTERVAL=60 uvicorn server.main:app --host 0.0.0.0 --port 3335
```

## Data Storage

**⚠️ IMPORTANT: All data is stored in-memory.**

- **No persistence** - World state resets on server restart
- Agent data, relationships, gossip, parties - all ephemeral
- Perfect for demo/testing, but not production-ready for persistent worlds

To add persistence, you would need to:
- Add a database (PostgreSQL, MongoDB, etc.)
- Implement save/load methods in `Building` class
- Add periodic snapshots or event sourcing

## Running as a Service (systemd)

Create `/etc/systemd/system/monadologia.service`:

```ini
[Unit]
Description=The Monad - Category Theory Social Simulation
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/monadologia
Environment="PORT=3335"
Environment="HOST=0.0.0.0"
ExecStart=/path/to/monadologia/venv/bin/uvicorn server.main:app --host 0.0.0.0 --port 3335
Restart=always

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl enable monadologia
sudo systemctl start monadologia
sudo systemctl status monadologia
```

## Firewall

Make sure port 3335 is open:
```bash
# UFW
sudo ufw allow 3335/tcp

# firewalld
sudo firewall-cmd --add-port=3335/tcp --permanent
sudo firewall-cmd --reload
```

## HTTPS Setup (Required for Vercel Frontend)

**⚠️ IMPORTANT:** If your frontend is on Vercel (HTTPS), your backend MUST also be HTTPS, or browsers will block requests (mixed content error).

### Option 1: Nginx Reverse Proxy with Let's Encrypt (Recommended)

```bash
# Install nginx and certbot
sudo apt update
sudo apt install nginx certbot python3-certbot-nginx

# Create nginx config
sudo nano /etc/nginx/sites-available/monadologia

# Add this config:
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:3335;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Enable site
sudo ln -s /etc/nginx/sites-available/monadologia /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# Get SSL certificate
sudo certbot --nginx -d your-domain.com

# Update Vercel env var:
# NEXT_PUBLIC_API_URL=https://your-domain.com
```

### Option 2: Cloudflare Tunnel (No Domain Needed)

```bash
# Install cloudflared
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64
chmod +x cloudflared-linux-amd64
sudo mv cloudflared-linux-amd64 /usr/local/bin/cloudflared

# Create tunnel
cloudflared tunnel --url http://localhost:3335

# Use the HTTPS URL it provides in Vercel env var
```

### Option 3: ngrok (Quick Testing)

```bash
# Install ngrok
wget https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz
tar -xzf ngrok-v3-stable-linux-amd64.tgz
sudo mv ngrok /usr/local/bin/

# Create tunnel
ngrok http 3335

# Use the HTTPS URL (e.g., https://abc123.ngrok.io) in Vercel
```

## Health Check

Test the server:
```bash
curl http://YOUR_VPS_IP:3335/
```

You should see JSON with world information.
