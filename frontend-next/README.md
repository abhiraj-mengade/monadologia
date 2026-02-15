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

If you see "(DEMO) mode" or "OFFLINE":
- Check that `NEXT_PUBLIC_API_URL` is set correctly in Vercel
- Verify your backend is running and accessible: `curl http://80.225.209.87:3335/`
- Check browser console for errors
- Note: Vercel (HTTPS) → HTTP backend may have mixed content issues in some browsers

## Local Development

```bash
npm install
npm run dev
```

The frontend will connect to `http://80.225.209.87:3335` by default, or use `.env.local`:

```
NEXT_PUBLIC_API_URL=http://localhost:3335
```
