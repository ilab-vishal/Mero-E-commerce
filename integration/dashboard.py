import os
import time

import requests
import streamlit as st
from dotenv import load_dotenv

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

# --- Session Persistence ---
if "chat_session_id" not in st.session_state:
    import uuid
    st.session_state.chat_session_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = []

# --- Sidebar Navigation ---
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Configuration", "AI Assistant"])

# --- Memory Inspector (Debug Tool) ---
st.sidebar.markdown("---")
with st.sidebar.expander("🛠️ Debug: Session Memory", expanded=False):
    st.caption(f"ID: `{st.session_state.chat_session_id}`")
    from chatbot.memory import memory_store
    history = memory_store.get_history(st.session_state.chat_session_id)
    if history:
        st.json(history)
        if st.button("Clear History", key="clear_mem"):
            memory_store.clear(st.session_state.chat_session_id)
            st.session_state.messages = []
            st.rerun()
    else:
        st.info("No history found in Redis for this session.")

if page == "Configuration":
    # --- Configuration Page ---
    st.sidebar.header("Platform selection")
    platform = st.sidebar.selectbox(
        "Choose Integration Platform",
        ["Shopify", "WooCommerce"],
        index=0
    )
    platform_key = platform.lower()
    api_prefix = f"/api/{platform_key}"

    st.title("Integration Configuration")
    
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
                            # Prepare payload
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
                st.error("Please fill in the connection details and validate the connection first.")
            else:
                with st.spinner(f"Initiating bulk sync for {platform}..."):
                    try:
                        # Prepare payload
                        payload = {
                            "store_url": store_url,
                        }
                        
                        endpoint = ""
                        if platform_key == "shopify":
                            # Shopify Sync Payload
                            payload["platform"] = "shopify"  # Required by pydantic model in integration.py
                            payload["client_id"] = client_id
                            payload["access_token"] = access_token
                            endpoint = f"{API_BASE_URL}/api/shopify/sync"
                        else:
                            # WooCommerce Sync Payload
                            payload["consumer_key"] = client_id
                            payload["consumer_secret"] = access_token
                            # WooCommerce endpoint usually expects these in the body or query, 
                            # verifying routers/bulk_sync.py: BulkSyncRequest model takes store_url, consumer_key, consumer_secret
                            endpoint = f"{API_BASE_URL}/api/woocommerce/sync"
                        
                        response = requests.post(endpoint, json=payload, timeout=10)
                        
                        if response.status_code == 200:
                            data = response.json()
                            st.success(f"✅ {data.get('message', 'Sync started successfully!')}")
                        else:
                            error_msg = response.text
                            try:
                                error_json = response.json()
                                error_msg = error_json.get('detail', error_msg)
                            except:
                                pass
                            st.error(f"❌ Sync Request Failed: {error_msg}")
                            
                    except Exception as e:
                        st.error(f"🌐 Comm Error: {str(e)}")
            
        st.markdown("---")
        st.subheader("📊 System Health")
        
        try:
            health_response = requests.get(f"{API_BASE_URL}/health", timeout=5)
            if health_response.status_code == 200:
                st.success("API: Online 🟢")
            else:
                st.error("API: Issues 🟡")
        except:
            st.error("API: Offline 🔴")

elif page == "AI Assistant":
    # --- Chatbot Page ---
    st.title("🛍️ Inventory AI Assistant")
    st.markdown("Ask questions about your products, prices, and inventory.")

    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # React to user input
    if prompt := st.chat_input("What would you like to know?"):
        # Display user message in chat message container
        st.chat_message("user").markdown(prompt)
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display assistant response in chat message container
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            
            with st.spinner("Agent is thinking..."):
                try:
                    # New Professional Standard: Send ONLY Session ID + Query
                    # The backend handles the history via Redis.
                    response = requests.post(
                        f"{API_BASE_URL}/chat",
                        json={
                            "query": prompt,
                            "session_id": st.session_state.chat_session_id
                        },
                        timeout=60
                    )
                    
                    if response.status_code == 200:
                        full_response = response.json().get("answer", "No response from agent.")
                    else:
                        full_response = f"Error: {response.text}"
                        
                except Exception as e:
                    full_response = f"Connection error: {e}"
            
            message_placeholder.markdown(full_response)
            
        # Add assistant message to chat history
        st.session_state.messages.append({"role": "assistant", "content": full_response})

# --- Footer ---
st.markdown("---")
st.markdown(
    f"""
    <div style='text-align: center; color: grey;'>
        Mero Integration Platform &copy; 2026 | Session: {st.session_state.get('chat_session_id', 'N/A')[:8]}...
    </div>
    """, 
    unsafe_allow_html=True
)
