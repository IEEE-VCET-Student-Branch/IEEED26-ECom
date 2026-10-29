# Deployment notes

The 2026-10-20 release moved the service to Python 3.11 and SQLAlchemy 2.x. SQLite remains the local and single-region persistence layer. The deployment has no external payment credentials: the provider adapter is deterministic and accepts any non-empty token except `decline`.

The 2026-10-23 release changed request middleware and refreshed the generated OpenAPI document. No schema migration was included. Rollback is the previous image plus the existing SQLite volume.

Health checks are exposed at `/health` and do not require authentication.
