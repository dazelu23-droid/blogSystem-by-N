# Deploy the blog (including workout site)

## Easiest way — double-click

1. Open `blog-workers` in File Explorer.
2. Double-click **`deploy.bat`**.
3. When your browser opens, click **Allow** on the Cloudflare login page.
4. Wait until you see **Deploy complete** and the live URLs.

## Or run in terminal

```powershell
cd blog-workers
powershell -File deploy.ps1
```

The script will:

- Install portable Node.js automatically if Node is not on your PATH
- Log you into Cloudflare (one-time browser step)
- Sync `workout-blog.html` into `public/`
- Apply the D1 database schema
- Deploy to Workers

## Live URLs after deploy

| Page | URL |
|------|-----|
| Blog home | https://simple-blog-by-n.dazelu.workers.dev/ |
| Workout blog | https://simple-blog-by-n.dazelu.workers.dev/workout-blog.html |
| Short link | https://simple-blog-by-n.dazelu.workers.dev/workout |

## Automatic deploy via GitHub (optional)

Add these secrets in GitHub → **Settings → Secrets and variables → Actions**:

1. `CLOUDFLARE_API_TOKEN` — create at [Cloudflare API tokens](https://dash.cloudflare.com/profile/api-tokens) with **Workers Scripts Edit** and **D1 Edit** permissions.
2. `CLOUDFLARE_ACCOUNT_ID` — found on the Cloudflare dashboard overview page.

Every push to `main` that changes `blog-workers/` or `workout-blog.html` will deploy automatically.
