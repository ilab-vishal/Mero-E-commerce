import streamlit as st
import requests
import json

# Page Configuration
st.set_page_config(
    page_title="WooCommerce Bridge",
    page_icon="🔌",
    layout="centered"
)

# Custom Styling
st.markdown("""
    <style>
    .main {
        background-color: #f8fafc;
    }
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        height: 3em;
        background-color: #2563eb;
        color: white;
        font-weight: bold;
    }
    .stTextInput>div>div>input {
        border-radius: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# App Content
st.title("🔌 WooCommerce Connector")
st.subheader("Verification System")
st.write("Enter your store credentials below to verify connectivity.")

with st.container(border=True):
    store_url = st.text_input("Store Base URL", placeholder="e.g. localhost/woocommerce_store")
    
    col1, col2 = st.columns(2)
    with col1:
        consumer_key = st.text_input("Consumer Key", type="default", placeholder="ck_xxxxxxxx...")
    with col2:
        consumer_secret = st.text_input("Consumer Secret", type="password", placeholder="cs_xxxxxxxx...")

    st.divider()

    if st.button("Verify Connection", key="verify_btn"):
        if not store_url or not consumer_key or not consumer_secret:
            st.error("⚠️ All fields are required for validation.")
            st.session_state.connected = False
        else:
            with st.spinner("Establishing Bridge..."):
                try:
                    response = requests.post(
                        "http://localhost:8050/api/woocommerce/connect",
                        json={
                            "store_url": store_url,
                            "consumer_key": consumer_key,
                            "consumer_secret": consumer_secret
                        },
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        result_data = response.json()
                        st.session_state.connected = True
                        st.session_state.total_store_products = result_data.get("total_store_products", 0)
                        st.session_state.creds = {
                            "store_url": store_url,
                            "consumer_key": consumer_key,
                            "consumer_secret": consumer_secret
                        }
                        st.success("✅ Success: Bridge Established!")
                    else:
                        st.session_state.connected = False
                        st.error(f"❌ Connection Rejected: {response.json().get('detail', 'Unknown Error')}")
                except Exception as e:
                    st.session_state.connected = False
                    st.error(f"❌ Network Error: Could not reach backend API ({e})")

# Bulk Sync Section
if st.session_state.get("connected"):
    st.divider()
    st.subheader("📦 Inventory Synchronization")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Products in Store", st.session_state.get("total_store_products", 0))
    with col2:
        st.info("Ready to synchronize with Elasticsearch")

    if st.button("🚀 Start Bulk Sync"):
        with st.spinner("Syncing products from store to Elasticsearch..."):
            try:
                sync_response = requests.post(
                    "http://localhost:8050/api/woocommerce/bulk-sync",
                    json=st.session_state.creds,
                    timeout=300 # Longer timeout for bulk sync
                )
                
                if sync_response.status_code == 200:
                    result = sync_response.json()
                    st.success(f"✅ Sync Completed in {result['duration_seconds']}s")
                    st.balloons()
                    
                    # Update count locally if possible or just show result
                    res_col1, res_col2, res_col3 = st.columns(3)
                    res_col1.metric("Fetched", result['total_fetched'])
                    res_col2.metric("Indexed", result['indexed_count'])
                    res_col3.metric("Failed", result['failed_count'])
                    
                    if result['failed_count'] > 0:
                        with st.expander("Show Failures"):
                            st.json(result['failures'])
                else:
                    st.error(f"❌ Sync Failed: {sync_response.json().get('detail', 'Unknown Error')}")
            except Exception as e:
                st.error(f"❌ Sync Error: {e}")

st.caption("Professional E-commerce Integration System | Modular v2")
