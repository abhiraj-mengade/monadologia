# Setting Up HTTPS for Backend

Vercel serves your frontend over HTTPS, but your backend is HTTP. Browsers block this "mixed content" for security.

## Quick Solutions

### Option 1: Cloudflare Tunnel (Easiest, Free)

1. **Install cloudflared:**
   ```bash
   # On your VPS
   wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64
   chmod +x cloudflared-linux-amd64
   sudo mv cloudflared-linux-amd64 /usr/local/bin/cloudflared
   ```

2. **Run tunnel:**
   ```bash
   cloudflared tunnel --url http://localhost:3335
   ```
   
   This gives you an HTTPS URL like: `https://random-name.trycloudflare.com`

3. **Update Vercel environment variable:**
   ```
   NEXT_PUBLIC_API_URL=https://random-name.trycloudflare.com
   ```

4. **Make it permanent (systemd service):**
   ```bash
   sudo nano /etc/systemd/system/cloudflared.service
   ```
   
   ```ini
   [Unit]
   Description=Cloudflare Tunnel
   After=network.target

   [Service]
   Type=simple
   User=your-user
   ExecStart=/usr/local/bin/cloudflared tunnel --url http://localhost:3335
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```
   
   ```bash
   sudo systemctl enable cloudflared
   sudo systemctl start cloudflared
   ```

### Option 2: Nginx + Let's Encrypt (Production Ready)

1. **Install nginx and certbot:**
   ```bash
   sudo apt update
   sudo apt install nginx certbot python3-certbot-nginx
   ```

2. **Configure nginx:**
   ```bash
   sudo nano /etc/nginx/sites-available/monadologia
   ```
   
   ```nginx
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
   ```
   
   ```bash
   sudo ln -s /etc/nginx/sites-available/monadologia /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl reload nginx
   ```

3. **Get SSL certificate:**
   ```bash
   sudo certbot --nginx -d your-domain.com
   ```

4. **Update Vercel:**
   ```
   NEXT_PUBLIC_API_URL=https://your-domain.com
   ```

### Option 3: Cloudflare Proxy (If you have a domain)

1. **Add domain to Cloudflare**
2. **Create A record:**
   - Name: `api` (or `@`)
   - Content: Your VPS IP
   - Proxy: **ON** (orange cloud)
3. **Update Vercel:**
   ```
   NEXT_PUBLIC_API_URL=https://api.your-domain.com
   ```

## Testing

After setup, test:
```bash
curl https://your-backend-url/
```

Should return JSON from your API.

## Update Frontend

In Vercel, set environment variable:
```
NEXT_PUBLIC_API_URL=https://your-backend-url
```

Redeploy and the mixed content error should be gone!
