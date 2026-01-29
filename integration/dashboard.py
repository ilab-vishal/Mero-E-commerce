import streamlit as st
import requests
import os
from dotenv import load_dotenv
import time

# Load configuration
load_dotenv()

# --- Page Config ---
st.set_page_config(
    page_title="Mero Integration Hub",
    page_icon="🚀",
    layout="wide",
)

# --- Constants ---
API_BASE_URL = os.getenv("API_URL", "http://app:8000")

# --- UI Header ---
st.title("Mero Integration Hub")
st.markdown("---")

# --- Sidebar Selection ---
st.sidebar.header("Platform selection")
platform = st.sidebar.selectbox(
    "Choose Integration Platform",
    ["Shopify", "WooCommerce"],
    index=0
)

# Set some variables based on selection
platform_key = platform.lower()
api_prefix = f"/api/{platform_key}"

# --- Main Dashboard ---
col1, col2 = st.columns([1, 1])

with col1:
    st.header(f"{platform} Connection")
    
    with st.form("connection_form"):
        store_url = st.text_input(
            "Store URL", 
            placeholder="your-store.myshopify.com" if platform_key == "shopify" else "https://your-wordpress-site.com"
        )
        
        client_id_label = "API Client ID" if platform_key == "shopify" else "Consumer Key (ck_...)"
        client_id = st.text_input(client_id_label, placeholder="Enter Key or ID")
        
        token_label = "Admin API Access Token" if platform_key == "shopify" else "Consumer Secret (cs_...)"
        access_token = st.text_input(token_label, type="password", placeholder="••••••••••••••••")
        
        test_submitted = st.form_submit_button("Validate Connection")
        
        if test_submitted:
            if not store_url or not access_token:
                st.error("Please provide both Store URL and Access Token/Secret.")
            else:
                with st.spinner(f"Connecting to {platform}..."):
                    try:
                        # Prepare payload based on platform
                        payload = {
                            "platform": platform_key,
                            "store_url": store_url,
                        }
                        
                        if platform_key == "shopify":
                            payload["client_id"] = client_id
                            payload["access_token"] = access_token
                        else:
                            payload["consumer_key"] = client_id
                            payload["consumer_secret"] = access_token
                        
                        response = requests.post(
                            f"{API_BASE_URL}{api_prefix}/connect",
                            json=payload,
                            timeout=30
                        )
                        
                        if response.status_code == 200:
                            data = response.json()
                            st.success(f"✅ {data.get('message', 'Connected successfully!')}")
                            if data.get("details"):
                                st.info(data["details"])
                        else:
                            error_data = response.json()
                            st.error(f"❌ Connection Failed: {error_data.get('detail', 'Unknown error')}")
                            
                    except Exception as e:
                        st.error(f"🌐 Network Error: Could not reach backend API ({e})")

with col2:
    st.header("Operations")
    
    st.subheader("Bulk Synchronization")
    st.write("Trigger a full re-sync of your product catalog to Elasticsearch.")
    
    if st.button("Start Bulk Sync", key="sync_btn"):
        if not store_url or not access_token:
            st.warning("⚠️ Please fill in connection settings before starting sync.")
        else:
            with st.spinner("Initiating background synchronization..."):
                try:
                    payload = {
                        "platform": platform_key,
                        "store_url": store_url,
                    }
                    
                    if platform_key == "shopify":
                        payload["client_id"] = client_id
                        payload["access_token"] = access_token
                    else:
                        payload["consumer_key"] = client_id
                        payload["consumer_secret"] = access_token

                    response = requests.post(
                        f"{API_BASE_URL}{api_prefix}/sync",
                        json=payload,
                        timeout=30
                    )
                    
                    if response.status_code in [200, 202]:
                        data = response.json()
                        st.success(f"🚀 Sync Accepted! {data.get('message', '')}")
                        st.toast("Sync operation started in background.")
                    else:
                        error_data = response.json()
                        st.error(f"❌ Sync Start Failed: {error_data.get('detail', 'Internal server error')}")
                        
                except Exception as e:
                    st.error(f"❌ Failed to reach backend: {e}")

    st.markdown("---")
    st.subheader("📊 System Health")
    
    # Check Health in real-time
    try:
        health_response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if health_response.status_code == 200:
            st.success("API: Online 🟢")
        else:
            st.error("API: Issues 🟡")
    except:
        st.error("API: Offline 🔴")

# --- Activity Log ---
st.markdown("---")
st.subheader("🕒 Activity Feed")
if 'activity_logs' not in st.session_state:
    st.session_state.activity_logs = []

# (In a real app, logs would be pulled from a service, but here we just show session events)
if st.session_state.activity_logs:
    for log in reversed(st.session_state.activity_logs):
        st.text(log)
else:
    st.write("Ready for tasks.")

# --- Footer ---
st.markdown(
    """
    <div style='text-align: center; color: grey; margin-top: 50px;'>
        Mero Integration Platform &copy; 2026 | Professional Software Integration
    </div>
    """, 
    unsafe_allow_html=True
)
