def format_single_product_data(data):
    product = data.get('product', {})
    
    print("\n" + "=" * 100)
    print("SHOPIFY PRODUCT DETAILS")
    print("=" * 100)
    
    print(f"\n📦 BASIC INFORMATION:")
    print(f"   Title:        {product.get('title', 'N/A')}")
    print(f"   ID:           {product.get('id', 'N/A')}")
    print(f"   Handle:       {product.get('handle', 'N/A')}")
    print(f"   Vendor:       {product.get('vendor', 'N/A')}")
    print(f"   Product Type: {product.get('product_type', 'N/A')}")
    print(f"   Status:       {product.get('status', 'N/A')}")
    print(f"   Created:      {product.get('created_at', 'N/A')}")
    print(f"   Updated:      {product.get('updated_at', 'N/A')}")
    print(f"   Published:    {product.get('published_at', 'N/A')}")
    
    print(f"\n📝 DESCRIPTION:")
    body_html = product.get('body_html', 'N/A')
    if body_html and body_html != 'N/A':
        clean_desc = body_html.replace('<p>', '').replace('</p>', '').replace('\n', ' ').strip()
        if len(clean_desc) > 300:
            print(f"   {clean_desc[:300]}...")
        else:
            print(f"   {clean_desc}")
    else:
        print(f"   N/A")
    
    print(f"\n🏷️  TAGS:")
    tags = product.get('tags', '')
    print(f"   {tags if tags else 'No tags'}")
    
    options = product.get('options', [])
    if options:
        print(f"\n⚙️  OPTIONS:")
        for option in options:
            values = ', '.join(option.get('values', []))
            print(f"   {option.get('name', 'N/A')}: {values}")
    
    variants = product.get('variants', [])
    if variants:
        print(f"\n🎨 VARIANTS ({len(variants)} total):")
        print(f"   {'SKU':<18} {'Title':<20} {'Price':<12} {'Inventory':<12} {'Weight':<10} {'ID'}")
        print(f"   {'-' * 95}")
        for variant in variants:
            sku = variant.get('sku', 'N/A')
            title = variant.get('title', 'N/A')
            price = variant.get('price', 'N/A')
            inventory = variant.get('inventory_quantity', 'N/A')
            weight = f"{variant.get('weight', 'N/A')}{variant.get('weight_unit', '')}"
            var_id = variant.get('id', 'N/A')
            print(f"   {sku:<18} {title:<20} ${price:<11} {str(inventory):<12} {weight:<10} {var_id}")
    
    images = product.get('images', [])
    if images:
        print(f"\n🖼️  IMAGES ({len(images)} total):")
        for img_idx, image in enumerate(images, 1):
            img_id = image.get('id', 'N/A')
            position = image.get('position', 'N/A')
            width = image.get('width', 'N/A')
            height = image.get('height', 'N/A')
            src = image.get('src', 'N/A')
            variant_ids = image.get('variant_ids', [])
            variant_count = len(variant_ids)
            print(f"   [{img_idx}] ID: {img_id} | Position: {position} | Size: {width}x{height} | Linked Variants: {variant_count}")
            print(f"       URL: {src}")
    
    print(f"\n{'=' * 100}\n")

def format_product_data(data):
    products = data.get('products', [])
    
    print("=" * 100)
    print(f"SHOPIFY PRODUCTS SEARCH RESULTS")
    print("=" * 100)
    print(f"\nTotal Products Found: {len(products)}\n")
    
    for idx, product in enumerate(products, 1):
        print(f"\n{'─' * 100}")
        print(f"PRODUCT #{idx}")
        print(f"{'─' * 100}")
        
        print(f"\n📦 BASIC INFORMATION:")
        print(f"   Title:        {product.get('title', 'N/A')}")
        print(f"   ID:           {product.get('id', 'N/A')}")
        print(f"   Vendor:       {product.get('vendor', 'N/A')}")
        print(f"   Product Type: {product.get('product_type', 'N/A')}")
        print(f"   Status:       {product.get('status', 'N/A')}")
        print(f"   Created:      {product.get('created_at', 'N/A')}")
        print(f"   Updated:      {product.get('updated_at', 'N/A')}")
        
        print(f"\n📝 DESCRIPTION:")
        body_html = product.get('body_html', 'N/A')
        if body_html and body_html != 'N/A':
            print(f"   {body_html[:200]}{'...' if len(body_html) > 200 else ''}")
        else:
            print(f"   N/A")
        
        print(f"\n🏷️  TAGS:")
        tags = product.get('tags', '')
        print(f"   {tags if tags else 'No tags'}")
        
        options = product.get('options', [])
        if options:
            print(f"\n⚙️  OPTIONS:")
            for option in options:
                values = ', '.join(option.get('values', []))
                print(f"   {option.get('name', 'N/A')}: {values}")
        
        variants = product.get('variants', [])
        if variants:
            print(f"\n🎨 VARIANTS ({len(variants)} total):")
            print(f"   {'SKU':<15} {'Title':<25} {'Price':<10} {'Inventory':<10} {'ID'}")
            print(f"   {'-' * 80}")
            for variant in variants:
                sku = variant.get('sku', 'N/A')
                title = variant.get('title', 'N/A')
                price = variant.get('price', 'N/A')
                inventory = variant.get('inventory_quantity', 'N/A')
                var_id = variant.get('id', 'N/A')
                print(f"   {sku:<15} {title:<25} ${price:<9} {inventory:<10} {var_id}")
        
        images = product.get('images', [])
        if images:
            print(f"\n🖼️  IMAGES ({len(images)} total):")
            for img_idx, image in enumerate(images, 1):
                img_id = image.get('id', 'N/A')
                position = image.get('position', 'N/A')
                width = image.get('width', 'N/A')
                height = image.get('height', 'N/A')
                src = image.get('src', 'N/A')
                variant_count = len(image.get('variant_ids', []))
                print(f"   [{img_idx}] ID: {img_id} | Position: {position} | Size: {width}x{height} | Variants: {variant_count}")
                print(f"       URL: {src}")
    
    print(f"\n{'=' * 100}\n")