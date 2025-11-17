# Backend Extensions

This backend now includes:
- JWT authentication with access/refresh rotation.
- Google OAuth ID token verification (lightweight placeholder; requires OAUTH_GOOGLE_CLIENT_ID).
- Storage service with local/S3/GCS backends (presigned upload/download endpoints).
- Payment provider abstraction with mock/Stripe/Razorpay placeholders and webhook endpoint.
- Admin analytics routes (sales by day, top books, summary).
- CORS configuration via environment.

See `.env.example` for all required environment variables.
