"""
Agentic Chatbot Graph Definition.
Handles memory, tool execution, and LLM interaction using LangGraph.
"""

# Standard library imports
from typing import Annotated, Any, Dict, List, Optional, TypedDict

# Third-party imports
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
)
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.graph import START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition

# Local imports
from base.elasticsearch_service import es_service
from base.llm_service import llm_service
from config import OPENAI_CHAT_MODEL, LLM_TEMPERATURE


# --- Shared Formatter (DRY) ---

def _format_variant(variant: Dict, currency: str = "NPR") -> str:
    """Format a single variant for display."""
    attrs = variant.get("attributes", {})
    attr_str = ", ".join(f"{k}: {v}" for k, v in attrs.items()) or "Standard"
    return (
        f"  - {attr_str} | "
        f"Price: {variant.get('price')} {currency} | "
        f"Stock: {variant.get('stock')} | "
        f"SKU: {variant.get('sku', 'N/A')}"
    )


def _format_product(product: Dict, variants_key: str = "variants", include_desc: bool = True) -> str:
    """Format a product with its variants for LLM context."""
    currency = product.get("currency", "NPR")
    variants = product.get(variants_key, product.get("variants", []))
    variants_block = "\n".join(_format_variant(v, currency) for v in variants)
    
    lines = [
        f"Product: {product.get('name')}",
        f"Product ID: {product.get('product_id')}",
        f"Price Range: {product.get('price_min')} - {product.get('price_max')} {currency}",
        f"Total Inventory: {product.get('total_inventory')}",
        f"Image: {product.get('primary_image')}",
    ]
    if include_desc:
        desc = product.get("description", "") or ""
        lines.append(f"Description: {desc[:300]}..." if len(desc) > 300 else f"Description: {desc}")
    lines.extend([f"Variants:\n{variants_block}", "---"])
    return "\n".join(lines)


# --- Domain Tools ---

@tool
def search_products(query: str) -> str:
    """
    Search for e-commerce products using hybrid retrieval (Keyword + Vector).
    
    Use this for general product questions like:
    - "Show me running shoes"
    - "Do you have winter jackets?"
    - "What laptops do you sell?"
    
    Args:
        query: Natural language search query
    """
    query_vector = llm_service.generate_embedding(query)
    results = es_service.hybrid_search(query=query, query_vector=query_vector, size=5)
    
    if not results:
        return "No matching products found."
    
    return "\n".join(_format_product(p) for p in results)


@tool
def search_by_variant(
    query: str,
    variant_filters: str = None,
    min_price: float = None,
    max_price: float = None,
    in_stock_only: bool = True
) -> str:
    """
    Search products with specific variant attribute filters.
    
    Use this when the user asks for SPECIFIC variant attributes like:
    - Color: "red shoes", "blue shirt", "black jacket"
    - Size: "size L", "size 42", "medium hoodie"
    - Material: "cotton shirt", "leather bag", "silk scarf"
    - Storage: "64GB iPhone", "256GB laptop"
    - Flavor: "vanilla ice cream", "chocolate cake"
    - Power: "100W charger", "500W blender"
    - Any other attribute!
    
    Args:
        query: Product search term (e.g., "shirt", "shoes", "phone")
        variant_filters: Comma-separated attribute filters like "color:red,size:L,material:cotton"
        min_price: Minimum price filter
        max_price: Maximum price filter
        in_stock_only: Only return in-stock variants (default: True)
    
    Examples:
        - query="shirt", variant_filters="color:red,size:L"
        - query="iPhone", variant_filters="storage:128GB,color:black"
        - query="coffee", variant_filters="roast:dark,weight:500g"
    """
    # Parse variant_filters string into dict
    attributes = {}
    if variant_filters:
        for pair in variant_filters.split(","):
            pair = pair.strip()
            if ":" in pair:
                key, value = pair.split(":", 1)
                attributes[key.strip().lower()] = value.strip()
    
    # If no filters, fall back to hybrid search
    if not attributes and min_price is None and max_price is None:
        query_vector = llm_service.generate_embedding(query)
        results = es_service.hybrid_search(query=query, query_vector=query_vector, size=5)
        if not results:
            return "No matching products found."
        return "\n".join(_format_product(p) for p in results)
    
    # Search with variant filters
    results = es_service.search_by_variant_attributes(
        attributes=attributes,
        price_min=min_price,
        price_max=max_price,
        in_stock_only=in_stock_only,
        size=5
    )
    
    if not results:
        filter_str = ", ".join(f"{k}={v}" for k, v in attributes.items())
        return f"No products found with filters: {filter_str}"
    
    # Show only matching variants
    formatted = []
    for product in results:
        product["variants"] = product.get("_matching_variants", product.get("variants", []))
        formatted.append(_format_product(product, include_desc=False))
    
    return "\n".join(formatted)


@tool
def get_variant_by_sku(sku: str) -> str:
    """
    Find a specific product variant by its SKU code.
    
    Use this when the user provides a specific SKU, product code, or item number.
    
    Args:
        sku: The unique SKU/product code (e.g., "ABC123", "NIKE-RED-42")
    """
    result = es_service.get_variant_by_sku(sku)
    
    if not result:
        return f"No product found with SKU: {sku}"
    
    matched = result.get("_matched_variant", {})
    result["variants"] = [matched] if matched else []
    return _format_product(result, include_desc=False)


# --- State Definition ---

class AgentState(TypedDict):
    """Tracking state for the agent workflow."""
    messages: Annotated[List[BaseMessage], add_messages]


# --- Graph Configuration ---

def _create_agent_graph():
    """Builds and compiles the LangGraph state machine."""
    tools = [search_products, search_by_variant, get_variant_by_sku]
    
    # Initialize LLM with tool binding using config values
    llm = ChatOpenAI(model=OPENAI_CHAT_MODEL, temperature=LLM_TEMPERATURE)
    llm_with_tools = llm.bind_tools(tools)

    def agent_node(state: AgentState):
        """Core agent logic: Invokes LLM with current history."""
        return {"messages": [llm_with_tools.invoke(state["messages"])]}

    # Define Graph
    workflow = StateGraph(AgentState)
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", ToolNode(tools))

    # Define Edges
    workflow.add_edge(START, "agent")
    workflow.add_conditional_edges("agent", tools_condition)
    workflow.add_edge("tools", "agent")

    return workflow.compile()


# Singleton graph instance
agent_graph = _create_agent_graph()


# --- Public Interface ---

def invoke_agent(user_query: str, history: List[Any] = None) -> str:
    """
    Run the agentic workflow.
    
    Args:
        user_query: The latest user input.
        history: List of message objects (role/content) for context.
    """
    if history is None:
        history = []

    # Store Knowledge Base (General Knowledge Perspective)
    store_policy = """
    STORE POLICIES:
    - **Shipping**: Free shipping on orders over NPR 5000. Standard delivery takes 2-4 business days.
    - **Returns**: 7-day return policy for unused items with tags.
    - **Payment**: We accept Esewa, Khalti, and Cash on Delivery (COD).
    - **Location**: We are located in Kathmandu, Nepal.
    """

    system_prompt = f"""You are an expert e-commerce sales assistant for a Nepali online store.
Your goal is to help customers find exactly what they need and provide accurate product information.

{store_policy}

AVAILABLE TOOLS:
1. **search_products**: Use for general product searches ("show me shoes", "what laptops do you have")
2. **search_by_variant**: Use when user specifies attributes like color, size, material, storage, etc.
   - Format filters as: "color:red,size:L,material:cotton"
3. **get_variant_by_sku**: Use when user provides a specific SKU/product code

GUIDELINES:
1. **Be Precise**: When showing variants, mention the EXACT price and stock for the requested attributes.
   - Example: "The Red shirt in Size L is NPR 1500 with 5 in stock."
2. **Check Availability**: Always tell the user if something is out of stock.
3. **Suggest Alternatives**: If the exact variant isn't available, suggest similar options.
4. **Be Helpful**: Answer questions about shipping, returns, and payment methods using store policies.
5. **Stay Concise**: Give clear, direct answers. Don't overwhelm with unnecessary details.

IMPORTANT:
- ALWAYS use tools for product information. Never make up prices or availability.
- If a user asks for a specific variant (color, size, etc.), use search_by_variant.
- If user just browses ("show me jackets"), use search_products.
- For SKU lookups, use get_variant_by_sku.
"""

    # Build Message History
    messages: List[BaseMessage] = [SystemMessage(content=system_prompt)]
    
    for msg in history:
        # Handle both dict access and attribute access (Pydantic vs Dict)
        if isinstance(msg, dict):
            role = msg.get("role")
            content = msg.get("content")
        else:
            role = getattr(msg, "role", None)
            content = getattr(msg, "content", None)
        
        if role == "user":
            messages.append(HumanMessage(content=content))
        elif role == "assistant":
            messages.append(AIMessage(content=content))
            
    # Append the latest query
    messages.append(HumanMessage(content=user_query))

    # Execute Graph
    result = agent_graph.invoke({"messages": messages})
    
    # Extract Final Response
    last_message = result["messages"][-1]
    return last_message.content
