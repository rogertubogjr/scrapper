# Property Search API Access

This guide explains how to call the `/properties` endpoint locally or in Docker after enabling token authentication.

## Prerequisites

- Python application running via `python run.py` or Docker Compose (`docker compose up --build`).
- The app listens on `http://localhost:5001` by default.
- An authentication token configured through environment or instance config:
  - Static token: set `TOKEN=<your_token>`.
  - Or JWT secret: set `SECRET_KEY=<your_secret>` and issue HS256 tokens.

## Authentication

Requests must include one of the following headers:

```
x-access-token: <TOKEN>
```

or

```
Authorization: Bearer <TOKEN>
```

Static tokens must match `TOKEN`. JWTs must be signed with `SECRET_KEY` using HS256.

## Request Format

`POST /properties`

- Body accepts raw text, JSON, or form data. When JSON or a form is provided, the server stringifies the payload before processing.
- Primary field is a free-form prompt describing the destination and preferences.

### Example Payload

```json
{
  "prompt": "Find family friendly hotels in Barcelona with beach access for next weekend."
}
```

## cURL Examples

### Static Token

```bash
curl -X POST \
  http://localhost:5001/properties \
  -H 'Content-Type: application/json' \
  -H 'x-access-token: YOUR_STATIC_TOKEN' \
  -d '{"prompt": "Need a boutique hotel in Paris for two adults"}'
```

### JWT

```bash
curl -X POST \
  http://localhost:5001/properties \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer YOUR_JWT' \
  -d '{"prompt": "Looking for beachfront resorts in Bali"}'
```

## Response

Successful responses contain:

```json
{
  "destination": "Barcelona",
  "count": 12,
  "items": [
    {
      "title": "Hotel Example",
      "link": "https://www.booking.com/...",
      "location": "District, City",
      "rating_reviews": "Rated 8.6 Excellent 10,000 reviews",
      "room_info": "Family room, 2 adults, 2 children",
      "price": "$250"
    }
  ],
  "source": "crawl4ai"
}
```

If authentication fails, the API returns `401 Unauthorized` with a JSON error message.

## Troubleshooting

- `401 Unauthorized`: confirm header name and token value.
- `504 Gateway Timeout`: rerun or adjust scraping settings; ensure Playwright is installed when running locally without Docker.
- `Event loop is closed`: ensure the server was restarted after configuration changes.

## Notes

- Keep scraping respectful; Booking.com may rate-limit automated requests.
- For Docker deployments, ensure the `.env` file contains the token configuration and that port `5001` is exposed.
