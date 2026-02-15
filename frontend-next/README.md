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

### Mixed Content Error (HTTPS/HTTP)

**Problem:** Vercel serves over HTTPS, but your backend is HTTP. Browsers block mixed content.

**Error:** `Mixed Content: The page was loaded over HTTPS, but requested an insecure resource`

**Solutions:**

1. **Set up HTTPS for backend (Recommended):**
   ```bash
   # Using nginx + Let's Encrypt
   sudo apt install nginx certbot python3-certbot-nginx
   sudo certbot --nginx -d your-domain.com
   ```
   Then update `NEXT_PUBLIC_API_URL` to `https://your-domain.com`

2. **Use Cloudflare Tunnel (Free, Easy):**
   ```bash
   # Install cloudflared
   cloudflared tunnel --url http://localhost:3335
   # Use the HTTPS URL it provides
   ```

3. **Use Cloudflare Proxy (If you have a domain):**
   - Add your domain to Cloudflare
   - Create an A record pointing to your VPS IP
   - Enable "Proxy" (orange cloud)
   - Use `https://your-domain.com` as API URL

4. **Temporary: Use HTTP frontend (Not recommended for production):**
   - Deploy to a service that supports HTTP (not Vercel)
   - Or use `localhost` for development only

### Other Issues

If you see "(DEMO) mode" or "OFFLINE":
- Check that `NEXT_PUBLIC_API_URL` is set correctly in Vercel
- Verify your backend is running and accessible
- Check browser console for CORS errors
- Ensure backend CORS allows your Vercel domain

## Local Development

```bash
npm install
npm run dev
```

The frontend will connect to `http://80.225.209.87:3335` by default, or use `.env.local`:

```
NEXT_PUBLIC_API_URL=http://localhost:3335
```
