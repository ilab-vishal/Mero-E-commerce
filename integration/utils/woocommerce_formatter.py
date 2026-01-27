def clean_description(desc: str) -> str:
    """Strip HTML tags and whitespace from description."""
    if not desc:
        return ""
    return desc.replace("<p>", "").replace("</p>", "").replace("\n", " ").strip()


def format_merged_product(product):
    if not product:
        print("❌ No product to format")
        return

    print("\n" + "=" * 100)
    print("WOOCOMMERCE PRODUCT (MERGED)")
    print("=" * 100)

    # Basic Info
    print(f"\n📦 BASIC INFORMATION:")
    print(f"   Name:   {product.get('name', 'N/A')}")
    print(f"   ID:     {product.get('id', 'N/A')}")
    print(f"   Slug:   {product.get('slug', 'N/A')}")
    print(f"   Type:   {product.get('type', 'N/A')}")
    print(f"   Status: {product.get('status', 'N/A')}")

    # Description
    desc = clean_description(product.get('description'))
    if desc:
        print(f"\n📝 DESCRIPTION:")
        print(f"   {desc[:200]}{'...' if len(desc) > 200 else ''}")

    # Attributes
    attributes = product.get('attributes', {})
    if attributes:
        print(f"\n⚙️  ATTRIBUTES:")
        for name, options in attributes.items():
            print(f"   {name.title()}: {', '.join(options) if isinstance(options, list) else options}")

    # Categories
    categories = product.get('categories', [])
    if categories:
        print(f"\n📁 CATEGORIES: {', '.join(categories)}")

    # Variants
    variants = product.get('variants', [])
    if variants:
        print(f"\n🎨 VARIANTS ({len(variants)} total):")
        print(f"   {'ID':<8} {'Attributes':<30} {'Price':<10} {'Stock':<8} {'Status':<10}")
        print(f"   {'-' * 80}")
        for v in variants:
            attrs = v.get('attributes', {})
            attr_str = " | ".join([f"{k}:{val}" for k, val in attrs.items()]) or "N/A"
            print(
                f"   {str(v.get('id', 'N/A')):<8} "
                f"{attr_str:<30} "
                f"{str(v.get('price', 'N/A')):<10} "
                f"{str(v.get('stock_quantity', 'N/A')):<8} "
                f"{str(v.get('stock_status', 'N/A')):<10}"
            )

    print("\n" + "=" * 100 + "\n")
