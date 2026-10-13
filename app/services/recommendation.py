import json
import re
from typing import Any

from app.config import settings


class RecommendationService:
    def __init__(self):
        self.client = None

        if settings.gemini_api_key.strip():
            try:
                from google import genai

                self.client = genai.Client(
                    api_key=settings.gemini_api_key
                )
            except Exception:
                self.client = None

    def generate(
        self, request_data: dict[str, Any]
    ) -> tuple[dict[str, Any], str]:
        if self.client is not None:
            try:
                result = self._generate_with_gemini(request_data)
                result = self._validate_result(
                    result, request_data
                )
                return result, "gemini"
            except Exception:
                # Continue with a local fallback if AI is unavailable.
                pass

        return self._fallback(request_data), "fallback"

    def _generate_with_gemini(
        self, data: dict[str, Any]
    ) -> dict[str, Any]:
        prompt = f"""
You are PocketSmart AI, a practical budget planning assistant.

Create a realistic recommendation plan using Indian rupees (INR).
Return ONLY a valid JSON object. Do not use Markdown fences.

User requirements:
{json.dumps(data, ensure_ascii=False)}

Use exactly this JSON structure:
{{
  "title": "Short plan title",
  "summary": "A helpful summary",
  "items": [
    {{
      "name": "Item name",
      "category": "Category",
      "quantity": 1,
      "unit_price": 1000,
      "total_price": 1000,
      "reason": "Why this item is suitable",
      "search_query": "Search terms for finding this item"
    }}
  ],
  "tips": ["Practical budget tip"],
  "budget": {data["budget"]},
  "total_estimated": 1000,
  "remaining_budget": 0
}}

Requirements:
- Choose appropriate items for the selected plan type.
- Use plausible estimated prices, not claimed live prices.
- Each quantity must be a positive integer.
- Each item's total_price must equal quantity multiplied by unit_price.
- The sum of item total_price values must not exceed the budget.
- total_estimated must equal the sum of item total_price values.
- remaining_budget must equal budget minus total_estimated.
- Include at least three useful items when the budget permits.
- Use Indian context and simple, clear English.
- Do not claim that items are currently in stock.
- For jewelry, make respectful, occasion-appropriate suggestions.
"""

        response = self.client.models.generate_content(
            model=settings.gemini_model,
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "temperature": 0.3,
            },
        )

        text = (response.text or "").strip()

        # Also tolerate accidental JSON code fences.
        text = re.sub(
            r"^```(?:json)?\s*|\s*```$",
            "",
            text,
            flags=re.IGNORECASE,
        )

        return json.loads(text)

    def _validate_result(
        self,
        result: dict[str, Any],
        data: dict[str, Any],
    ) -> dict[str, Any]:
        budget = int(data["budget"])

        if not isinstance(result, dict):
            raise ValueError("Invalid AI response.")

        items = result.get("items")

        if not isinstance(items, list):
            raise ValueError("Missing recommendation items.")

        if len(items) > 50:
            raise ValueError("Too many recommendation items.")

        clean_items = []
        total = 0

        for item in items:
            if not isinstance(item, dict):
                continue

            name = str(item.get("name", "Recommended item"))[:150]
            category = str(item.get("category", "General"))[:80]
            reason = str(item.get("reason", ""))[:500]
            search_query = str(item.get("search_query", name))[:200]

            try:
                quantity = int(item.get("quantity", 1))
                unit_price = int(item.get("unit_price", 0))
            except (ValueError, TypeError):
                continue

            if quantity < 1 or quantity > 10000 or unit_price < 0:
                continue

            line_total = quantity * unit_price

            if line_total > budget or total + line_total > budget:
                continue

            total += line_total

            clean_items.append({
                "name": name,
                "category": category,
                "quantity": quantity,
                "unit_price": unit_price,
                "total_price": line_total,
                "reason": reason,
                "search_query": search_query,
            })

        if not clean_items:
            raise ValueError("AI did not provide usable items.")

        tips = result.get("tips", [])

        if not isinstance(tips, list):
            tips = []

        return {
            "title": str(result.get("title", "Your Budget Plan"))[:200],
            "summary": str(result.get("summary", ""))[:1000],
            "items": clean_items,
            "tips": [str(tip)[:300] for tip in tips[:10]],
            "budget": budget,
            "total_estimated": total,
            "remaining_budget": budget - total,
        }

    def _fallback(
        self, data: dict[str, Any]
    ) -> dict[str, Any]:
        plan_type = data["plan_type"]
        budget = int(data["budget"])

        if plan_type == "home":
            title = "Home Essentials Budget Plan"
            candidates = [
                ("LED bulbs", "Lighting", 150, 2,
                 "Useful for energy-efficient lighting"),
                ("Ceiling fan", "Electrical", 1800, 1,
                 "A practical cooling option"),
                ("Storage shelf", "Furniture", 1200, 1,
                 "Helps organize household items"),
                ("Dining table", "Furniture", 4500, 1,
                 "A shared dining space"),
                ("Study lamp", "Lighting", 700, 1,
                 "Helpful for reading and studying"),
                ("Curtains", "Home decor", 600, 2,
                 "Adds privacy and shade"),
            ]
        elif plan_type == "party":
            people = int(data.get("people", 10))
            candidates = [
                ("Food allowance per guest", "Food",
                 180, people,
                 "An estimated food allowance for each guest"),
                ("Drinks per guest", "Refreshments",
                 40, people,
                 "Budget for non-alcoholic refreshments"),
                ("Decorations", "Decor",
                 700, 1,
                 "Simple party decorations"),
                ("Disposable plates and cups", "Supplies",
                 10, people,
                 "Basic serving supplies"),
                ("Cake", "Dessert",
                 800, 1,
                 "A dessert for the celebration"),
            ]
            title = "Party Budget Plan"
        else:
            title = "Jewelry Occasion Plan"
            candidates = [
                ("Simple earrings", "Earrings", 350, 1,
                 "A versatile accessory"),
                ("Pendant necklace", "Necklace", 650, 1,
                 "Pairs well with many outfits"),
                ("Bangle set", "Bangles", 300, 1,
                 "A traditional accessory option"),
                ("Minimal bracelet", "Bracelet", 250, 1,
                 "A simple everyday option"),
                ("Statement necklace", "Necklace", 1200, 1,
                 "An option for a special occasion"),
            ]

        items = []
        total = 0

        for name, category, unit_price, quantity, reason in candidates:
            line_total = unit_price * quantity

            if total + line_total > budget:
                continue

            total += line_total

            items.append({
                "name": name,
                "category": category,
                "quantity": quantity,
                "unit_price": unit_price,
                "total_price": line_total,
                "reason": reason,
                "search_query": name,
            })

        if not items:
            items.append({
                "name": "Save this budget for a suitable option",
                "category": "Budget planning",
                "quantity": 1,
                "unit_price": budget,
                "total_price": budget,
                "reason": (
                    "Compare available options before purchasing."
                ),
                "search_query": "budget-friendly options",
            })
            total = budget

        style = data.get("style", "").strip()
        occasion = data.get("occasion", "").strip()

        summary = (
            f"This is a sample {plan_type} plan for a budget of "
            f"₹{budget:,}. Estimated costs are illustrative, "
            "not live retailer prices."
        )

        if style:
            summary += f" Preferred style: {style}."
        if occasion:
            summary += f" Occasion: {occasion}."

        return {
            "title": title,
            "summary": summary,
            "items": items,
            "tips": [
                "Compare prices from different sellers before buying.",
                "Keep some money aside for unexpected costs.",
                "Check product quality, delivery charges and return policies.",
            ],
            "budget": budget,
            "total_estimated": total,
            "remaining_budget": budget - total,
        }