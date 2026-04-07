"""
Mock tools for Travel Planning Agent.
Used for testing the ReAct loop without real API calls.
"""

MOCK_TOOLS = [
    {
        "name": "suggest_destinations",
        "description": "Suggest travel destinations based on budget, duration, month, and preferences",
    },
    {
        "name": "check_weather",
        "description": "Check weather conditions for a city in a specific month",
    },
    {
        "name": "search_flights",
        "description": "Search for flights between two cities within budget",
    },
    {
        "name": "search_hotels",
        "description": "Search for hotels in a location within budget per night",
    },
    {
        "name": "get_attractions",
        "description": "Get popular attractions in a city by category",
    },
    {
        "name": "calculate_total_cost",
        "description": "Calculate total trip cost and remaining budget",
    },
]

# Mock responses for each tool
MOCK_RESPONSES = {
    "suggest_destinations": {
        "status": "success",
        "destinations": [
            {"name": "Đà Nẵng", "estimated_cost": 6500000, "highlights": "Biển Mỹ Khê, Bà Nà Hills"},
            {"name": "Nha Trang", "estimated_cost": 7000000, "highlights": "Vinpearl, Đảo Yến"},
            {"name": "Đà Lạt", "estimated_cost": 5500000, "highlights": "Hồ Xuân Hương, Thác Prenn"},
        ],
        "recommendation": "Đà Nẵng - chi phí hợp lý, nhiều điểm tham quan",
    },
    "check_weather": {
        "status": "success",
        "weather": "Nắng nóng 28-36°C, có mưa rào chiều",
        "recommendation": "Cuối tháng 7 vẫn thuận lợi, nên mang theo ô/dù",
    },
    "search_flights": {
        "status": "success",
        "flights": [
            {"airline": "VietJet", "price": 2800000, "departure": "07:00"},
            {"airline": "Bamboo Airways", "price": 3500000, "departure": "09:30"},
        ],
        "best_option": {"airline": "VietJet", "price": 2800000, "departure": "07:00"},
    },
    "search_hotels": {
        "status": "success",
        "hotels": [
            {"name": "Sea Phoenix Hotel", "price": 1200000, "rating": 4.2, "distance_to_beach": "200m"},
            {"name": "Mường Thanh Luxury", "price": 1800000, "rating": 4.5, "distance_to_beach": "50m"},
        ],
        "best_option": {"name": "Sea Phoenix Hotel", "total_cost": 2400000, "rating": 4.2},
    },
    "get_attractions": {
        "status": "success",
        "attractions": [
            {"name": "Bà Nà Hills", "ticket_price": 750000, "duration": "1 ngày"},
            {"name": "Ngũ Hành Sơn", "ticket_price": 40000, "duration": "nửa ngày"},
            {"name": "Cầu Vàng", "ticket_price": 0, "duration": "2 giờ"},
            {"name": "Bãi biển Mỹ Khê", "ticket_price": 0, "duration": "tự do"},
        ],
        "estimated_total": 1500000,
    },
    "calculate_total_cost": {
        "status": "success",
        "total": 6700000,
        "remaining_budget": 3300000,
        "breakdown": {
            "flights": "41.8%",
            "hotels": "35.8%",
            "activities": "22.4%",
        },
    },
}


def get_mock_response(tool_name: str, args: str = "") -> str:
    """Get mock response for a tool call."""
    import json
    response = MOCK_RESPONSES.get(tool_name, {"status": "error", "message": f"Tool {tool_name} not found"})
    return json.dumps(response, ensure_ascii=False)
