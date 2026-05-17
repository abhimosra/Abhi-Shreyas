import json
from config.settings import CATALOG_PATH

_catalog = None


def _load_catalog() -> dict:
    global _catalog
    if _catalog is None:
        with open(CATALOG_PATH) as f:
            _catalog = json.load(f)
    return _catalog


def search_products(query: str, category: str | None = None) -> str:
    catalog = _load_catalog()
    query_lower = query.lower()
    results = []
    for product in catalog["products"]:
        if category and product["category"] != category:
            continue
        searchable = f"{product['name']} {product['description']} {product['materials']} {product['category']}".lower()
        if any(term in searchable for term in query_lower.split()):
            results.append({
                "sku": product["sku"],
                "name": product["name"],
                "price_usd": product["price_usd"],
                "materials": product["materials"],
                "description": product["description"],
                "in_stock": product["in_stock"],
                "sizes_available": product.get("sizes_available") or product.get("lengths_available"),
            })
    if not results:
        return json.dumps({"found": False, "message": "No products matched that search. Try broader terms."})
    return json.dumps({"found": True, "count": len(results), "products": results})


def get_product_by_sku(sku: str) -> str:
    catalog = _load_catalog()
    for product in catalog["products"]:
        if product["sku"].upper() == sku.upper():
            return json.dumps({"found": True, "product": product})
    return json.dumps({"found": False, "message": f"No product found with SKU '{sku}'."})


def get_shipping_info(destination_type: str = "domestic_standard") -> str:
    catalog = _load_catalog()
    shipping = catalog["shipping"]
    threshold = shipping["free_shipping_threshold_usd"]
    if destination_type not in shipping:
        return json.dumps({"error": f"Unknown destination type '{destination_type}'. Use: domestic_standard, domestic_express, or international."})
    option = shipping[destination_type]
    return json.dumps({
        "option": destination_type,
        "carrier": option["carrier"],
        "cost_usd": option["cost_usd"],
        "estimated_days": option["estimated_days"],
        "note": option.get("note"),
        "free_shipping_on_orders_over_usd": threshold,
    })


def get_store_policies() -> str:
    catalog = _load_catalog()
    return json.dumps(catalog["policies"])


def get_price_range(category: str | None = None) -> str:
    catalog = _load_catalog()
    products = catalog["products"]
    if category:
        products = [p for p in products if p["category"] == category]
    if not products:
        return json.dumps({"found": False, "message": f"No products found in category '{category}'."})
    prices = [p["price_usd"] for p in products]
    return json.dumps({
        "category": category or "all",
        "min_usd": min(prices),
        "max_usd": max(prices),
        "count": len(products),
    })


# Maps tool names from Claude's tool_use blocks to the actual functions
TOOL_FUNCTIONS = {
    "search_products": search_products,
    "get_product_by_sku": get_product_by_sku,
    "get_shipping_info": get_shipping_info,
    "get_store_policies": get_store_policies,
    "get_price_range": get_price_range,
}


def execute_tool(tool_name: str, tool_input: dict) -> str:
    func = TOOL_FUNCTIONS.get(tool_name)
    if not func:
        return json.dumps({"error": f"Unknown tool: {tool_name}"})
    return func(**tool_input)
