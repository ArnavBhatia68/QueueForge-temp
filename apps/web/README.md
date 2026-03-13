# QueueForge Web App

Next.js admin dashboard for QueueForge.

## Scripts

```bash
npm install
npm run dev
npm run build
npm run lint
```

## Environment

Set `NEXT_PUBLIC_API_URL` when deploying (for API rewrites):

```bash
NEXT_PUBLIC_API_URL=https://your-api-domain/api/v1
```

For local development, if unset it defaults to `http://127.0.0.1:8001/api/v1`.

Optional local-only demo banner on login page:

```bash
NEXT_PUBLIC_SHOW_DEMO_CREDENTIALS=true
```
