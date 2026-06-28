# Tech Specifications & Coding Standards

## 1. Project Core Stack
- **Language/Framework:** Python 3.12+, FastAPI
- **Primary AI Tools:** OpenCode
- **Database:** PostgreSQL, Redis

## 2. Coding Standards (Rules the AI MUST follow)
- **Async/Await:** All I/O operations (DB, API calls, File system) must be `async`. No blocking calls.
- **Error Handling:** Every API endpoint must have a `try-except` block. Log errors to console with clear context.
- **Input Validation:** Use Pydantic models for all incoming request bodies. Reject invalid requests with 422.
- **Modularity:** Adhere to Single Responsibility Principle (SRP). Keep functions < 30 lines. Use the Repository Pattern to decouple business logic from DB queries.

## 3. APIs & Documentation & Formatting
- **FastAPI Docs:** https://fastapi.tiangolo.com/
- **Pydantic Docs:** https://docs.pydantic.dev/latest/
- **External API Reference:** [Keep empty, fill during the challenge]
- **API Response Format (STRICT):** All API responses MUST be wrapped in a JSON envelope:
  `{"status": "success/error", "data": ..., "message": "..."}`. No exceptions.

## 4. Security Policy
- **Secrets:** Never hardcode API keys. Use `.env` files and `os.getenv`.
- **Validation:** Sanitize all user inputs before database interaction.