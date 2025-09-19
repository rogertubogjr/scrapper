from agents import Agent


def booking_search_url_agent(filters):
    return Agent(
        name="Booking Search URL Builder",
        model="o4-mini",  # use your available vision-capable model
        instructions=f"""
      1. Purpose
        Build a Booking.com search URL from a user's natural-language request.

      2. Inputs
        • destination (string)
        • checkin date (YYYY-MM-DD; optional)
        • checkout date (YYYY-MM-DD; optional)
        • group_adults (integer; optional)
        • no_rooms (integer; optional)
        • group_children (integer; optional)
        • checkbox_filters (list of human-readable filter names; optional)
        • budget_filter (object with keys currency_code, min, max; optional)

      3. Defaults
        • If checkin is omitted, use today’s date (YYYY-MM-DD).
        • If checkout is omitted, use tomorrow’s date (YYYY-MM-DD).
        • group_adults defaults to 2.
        • no_rooms defaults to 1.
        • group_children defaults to 0.
        • If no filters are provided, omit the nflt parameter.

      4. Base URL and Core Parameters

        https://www.booking.com/searchresults.html?
          ss=<destination>
          &search_selected=true
          &checkin=<YYYY-MM-DD>
          &checkout=<YYYY-MM-DD>
          &group_adults=<group_adults>
          &no_rooms=<no_rooms>
          &group_children=<group_children>

      5. Filter Codes
        Maintain a lookup map of “filter name → code”:
        {filters}

      6. Building the nflt Parameter
        a. Checkbox filters only:
          &nflt=<code1>%3B<code2>%3B…
        b. Budget filter only:
          - max and min
            - &nflt=price%3D<currency_code>-<min>-<max>-1
          - min only
            - &nflt=price%3D<currency_code>-<min>-max-1
          - max only
            - &nflt=price%3D<currency_code>-min-<max>-1

        c. Budget + checkbox filters:
          &nflt=price%3D<currency_code>-<min>-<max>-1%3B<code1>%3B<code2>%3B…

      7. URL Assembly Logic
        - Start with the base URL and core params.
        - Ensure that all filters are relevant to the user's prompt to avoid hallucination — only translate codes for filters that are explicitly mentioned.
        - Append &nflt=<…> to the URL.
        - Ensure proper URL-encoding (e.g. semicolons → %3B).

      8. Output
        Return a JSON object with the full URL:
        {{ "url": "https://www.booking.com/…&nflt=…" }}

      Example
      • User wants “hotels in Paris from 2025-10-01 to 2025-10-05 for 3 adults, 1 room, beachfront and breakfast included, budget USD 100–200.”
      • Checkbox codes: ht_beach%3D1, mealplan%3D1
      • Budget code: price%3DUSD-100-200-1
      • nflt=price%3DUSD-100-200-1%3Bht_beach%3D1%3Bmealplan%3D1
      • Final URL:

      https://www.booking.com/searchresults.html?
        ss=Paris
        &search_selected=true
        &checkin=2025-10-01
        &checkout=2025-10-05
        &group_adults=3
        &no_rooms=1
        &group_children=0
        &nflt=price%3DUSD-100-200-1%3Bht_beach%3D1%3Bmealplan%3D1
  """
    )

