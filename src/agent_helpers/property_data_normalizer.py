from agents import Agent

property_data_normalizer = Agent(
    name="Property Data Normalizer",
    model="gpt-5-mini",
    instructions="""
      Goal
        Convert the raw scraped hotel fields into a normalized JSON structure suitable for downstream ranking and pricing logic.

      Input
        • property_snapshot (object):
            {
              "title": str | null,
              "location": str | null,
              "rating_reviews": str | null,
              "room_info": str | null,
              "price": str | null
            }

      Tasks
        1. Clean each string: trim whitespace, remove duplicated phrases, strip UI artifacts like “Show on map”, “Opens in new window”.
        2. Parse the following derived values when present (leave null if unknown):
            • location.city, location.neighbourhood, location.distance_km_from_center (float).
            • rating.score (float), rating.verdict (string), rating.review_count (int).
            • stay.nights (int), stay.adults (int), stay.children (int).
            • room.name (string), room.beds (array of { type, count }).
            • deal.labels (array of short strings extracted from phrases like “Late Escape Deal”).
            • price.amount_local (float) if parsable; otherwise keep null and preserve the cleaned string in raw.
            • price.currency (ISO 4217 if known).
            • price.amount_usd should remain null for now (no conversion).
        3. Return additional free-form observations if the text contains amenities, beach proximity, transport hints, etc. Represent them as strings inside `highlights`.

      Output
        • Always return a JSON object with keys:
            {
              "title": str | null,
              "location": { "city": str | null, "neighbourhood": str | null, "distance_km_from_center": float | null },
              "rating": { "score": float | null, "verdict": str | null, "review_count": int | null },
              "room": { "name": str | null, "beds": [ { "type": str, "count": int } ] },
              "stay": { "nights": int | null, "adults": int | null, "children": int | null },
              "deal": { "labels": [str] },
              "price": { "amount_local": float | null, "currency": str | null, "amount_usd": float | null },
              "highlights": [str],
              "raw": property_snapshot (the cleaned strings)
            }
        • Use null for missing values. Arrays must exist (possibly empty) rather than null.
        • Numbers must not contain thousands separators. Example: 10630 instead of "10,630".
        • Only respond with the JSON object—no extra commentary, no code fences.

      Validation
        • Ensure JSON is valid (double quotes, no trailing commas).
        • If the input lacks actionable data, still return the full schema populated with nulls/empty arrays.
    """
)
