# Frontend Deployment on Vercel

## Environment Variables

**Required:** Set `NEXT_PUBLIC_API_URL` in Vercel to point to your backend:

```
NEXT_PUBLIC_API_URL=http://80.225.209.87:3335
```

Or if your backend supports HTTPS:
```
NEXT_PUBLIC_API_URL=https://your-backend-domain.com
```

## Setup

1. **Connect your GitHub repo to Vercel**
2. **Set Environment Variable:**
   - Go to Project Settings → Environment Variables
   - Add: `NEXT_PUBLIC_API_URL` = `http://80.225.209.87:3335`
3. **Deploy**

## Troubleshooting

### Mixed Content Error (HTTPS → HTTP)

**Problem:** Vercel serves over HTTPS, but backend is HTTP. Browsers block this.

**Error:** `Mixed Content: The page was loaded over HTTPS, but requested an insecure resource`

**Solutions:**

1. **Set up HTTPS for backend** (Recommended):
   ```bash
   # Using nginx reverse proxy with Let's Encrypt
   sudo apt install nginx certbot python3-certbot-nginx
   sudo certbot --nginx -d your-domain.com
   ```

2. **Use Cloudflare Tunnel** (Free, no domain needed):
   ```bash
   cloudflared tunnel --url http://localhost:3335
   # Use the HTTPS URL it provides
   ```

3. **Use ngrok** (Quick testing):
   ```bash
   ngrok http 3335
   # Use the HTTPS URL it provides
   ```

4. **Update Vercel environment variable:**
   ```
   NEXT_PUBLIC_API_URL=https://your-https-backend-url
   ```

### Other Issues

If you see "(DEMO) mode" or "OFFLINE":
- Check that `NEXT_PUBLIC_API_URL` is set correctly in Vercel
- Verify your backend is running and accessible
- Check browser console for CORS errors
- Ensure CORS is enabled on backend (already configured)

## Local Development

```bash
npm install
npm run dev
```

The frontend will connect to `http://80.225.209.87:3335` by default, or use `.env.local`:

```
NEXT_PUBLIC_API_URL=http://localhost:3335
```
