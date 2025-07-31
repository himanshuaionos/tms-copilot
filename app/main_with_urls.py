# # app/main.py
# import streamlit as st
# from pathlib import Path
# import time
# from typing import List, Dict
# import os, sys
# from urllib.parse import urlencode
# from pinecone import Pinecone, ServerlessSpec
# from PIL import Image
# import requests
# import json

# #################
# # Please comment this line while working on local machine
# # import sys
# # sys.modules["sqlite3"] = __import__("pysqlite3")
# ####################

# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
# from utils.config import config

# # Set page config as the first Streamlit command
# st.set_page_config(
#     page_title=config.APP_TITLE,
#     layout="wide",
# )

# ## Adding customised avatar for the bot
# assistant_avatar = Image.open("app/icon_tms.png")

# ## Load source URL mapping
# def load_source_url_mapping():
#     """Load source URL mapping from JSON file."""
#     try:
#         with open("source_url_mapping.json", "r") as f:
#             mapping_data = json.load(f)
#             url_map = {}
#             display_name_map = {}
            
#             for item in mapping_data.get("url_mapping", []):
#                 file_name = item["file_name"]
#                 url_map[file_name] = item["source_url"]
#                 if "display_name" in item:
#                     display_name_map[file_name] = item["display_name"]
            
#             return {"urls": url_map, "display_names": display_name_map}
#     except Exception as e:
#         print(f"Error loading source URL mapping: {e}")
#         return {"urls": {}, "display_names": {}}

# # Initialize source URL mapping
# source_url_mapping = load_source_url_mapping()

# def check_environment():
#     """Check if all required environment variables are set."""
#     missing_vars = []
    
#     if not config.OPENAI_API_KEY:
#         missing_vars.append("OPENAI_API_KEY")
#     if not config.PINECONE_API_KEY:
#         missing_vars.append("PINECONE_API_KEY")
#     if not config.PINECONE_ENVIRONMENT:
#         missing_vars.append("PINECONE_ENVIRONMENT")
    
#     if missing_vars:
#         error_msg = f"Missing required environment variables: {', '.join(missing_vars)}\n"
#         error_msg += "Please ensure these variables are set in your .env file or environment."
#         raise ValueError(error_msg)

# def display_sources(sources: List[Dict]):
#     """Display unique source URLs with display names after response message."""
#     if not sources:
#         return
    
#     # Track unique sources to avoid duplicates
#     unique_sources = {}
    
#     # Extract and deduplicate sources
#     for source in sources:
#         metadata = source.get('metadata', {})
#         source_name = metadata.get('source', 'Source')
        
#         # Skip if we've already processed this source
#         if source_name in unique_sources:
#             continue
            
#         # Try to find URL and display name in the mapping first, then fallback
#         url = ""
#         display_name = source_name
        
#         # Check if source exists in our mapping
#         if source_name in source_url_mapping["urls"]:
#             url = source_url_mapping["urls"][source_name]
#             # Use display name if available, otherwise use source name
#             if source_name in source_url_mapping["display_names"]:
#                 display_name = source_url_mapping["display_names"][source_name]
#         else:
#             url = metadata.get('url', '')
        
#         # Only store if it has a URL
#         if url:
#             unique_sources[source_name] = {
#                 "url": url,
#                 "display_name": display_name
#             }
    
#     # Display unique sources as simple links
#     if unique_sources:
#         st.markdown("***")
#         st.markdown("**Sources:**")
#         sources_markdown = ""
#         for i, (_, source_info) in enumerate(unique_sources.items()):
#             if i > 0:
#                 sources_markdown += " | "
#             sources_markdown += f"[{source_info['display_name']}]({source_info['url']})"
#         st.markdown(sources_markdown)

# # Initialize session state at the very top to avoid KeyError
# if "chat_history" not in st.session_state:
#     st.session_state.chat_history = []
# if "current_sources" not in st.session_state:
#     st.session_state.current_sources = []
# if "context_window" not in st.session_state:
#     st.session_state.context_window = 5
# if "max_history" not in st.session_state:
#     st.session_state.max_history = 10
# if "show_sources" not in st.session_state:
#     st.session_state.show_sources = True
# if "conversation_id" not in st.session_state:
#     st.session_state.conversation_id = None

# st.title(config.APP_TITLE)

# # st.markdown("""
# # Get answers to all your TMS Cytric related queries.
# # """)

# st.markdown("Please don’t use any personal data. Note that responses are provided by a chatbot powered by Artificial Intelligence technology and not reviewed by humans. Therefore, the responses to your questions may not be accurate.")


# # Floating "New Conversation" Button at bottom-right
# # st.markdown("""
# #     <style>
# #     .new-convo-button {
# #         position: fixed;
# #         bottom: 20px;
# #         right: 30px;
# #         z-index: 9999;
# #     }
# #     </style>
# #     <div class="new-convo-button">
# #         <form action="" method="post">
# #             <button type="submit">🔄 New Conversation</button>
# #         </form>
# #     </div>
# # """, unsafe_allow_html=True)

# # Clear session state on button click (handle post request)
# if st.session_state.get("reset_chat", False):
#     st.session_state.chat_history = []
#     st.session_state.current_sources = []
#     st.session_state.conversation_id = None  # Reset conversation_id for new session
#     st.session_state.reset_chat = False
#     st.rerun()

# # Use JS to detect button submit and set Streamlit state
# st.markdown("""
#     <script>
#     const form = document.querySelector('.new-convo-button form');
#     form.addEventListener('submit', async function(event) {
#         event.preventDefault();
#         await fetch('', { method: 'POST' });
#         window.parent.postMessage({type: 'streamlit:setComponentValue', value: true}, '*');
#     });
#     </script>
# """, unsafe_allow_html=True)


# # Chat interface
# for message in st.session_state.chat_history:
#     with st.chat_message(
#         name=message["role"],
#         avatar=assistant_avatar if message["role"] == "assistant" else None
#     ):
#         st.write(message["content"])

# # We don't need the separate sources display section anymore
# # since we're showing sources directly after each assistant message


# # User input
# user_input = st.chat_input("Ask me anything about TMS Cytric...")

# # Update the query processing in the main chat interface
# if user_input:
#     # Add user message to chat history
#     st.session_state.chat_history.append({
#         "role": "user",
#         "content": user_input
#     })
    
#     # Display user message
#     with st.chat_message("user"):
#         st.write(user_input)
    
#     # Create a placeholder for the streaming response
#     with st.chat_message(
#         "assistant",
#         avatar=assistant_avatar
#         ):
#         response_placeholder = st.empty()
        
#         try:
#             # Prepare payload for API
#             payload = {
#                 "message": user_input,
#                 "chat_history": st.session_state.chat_history[-st.session_state.max_history:],
#                 "context_window": st.session_state.context_window,
#                 "max_history": st.session_state.max_history,
#                 "include_sources": True,
#                 "conversation_id": st.session_state.conversation_id
#             }
#             # Log the payload for debugging
#             #print("Payload being sent to API:", json.dumps(payload, indent=2))
#             api_url = "http://13.233.150.156:8505/chat/stream"
#             response = requests.post(api_url, json=payload, stream=True, timeout=120)
            
#             full_response = ""
#             # Stream the response as it arrives
#             for chunk in response.iter_content(chunk_size=None, decode_unicode=True):
#                 if chunk:
#                     full_response += chunk
#                     response_placeholder.markdown(full_response)
#             # After streaming the response and updating chat history, fetch and display sources if enabled
#             # print(full_response)
#             st.session_state.chat_history.append({
#                 "role": "assistant",
#                 "content": full_response
#             })
#             # Update conversation_id from API response header if present
#             if "conversation_id" in response.headers:
#                 st.session_state.conversation_id = int(response.headers["conversation_id"])
#             else:
#                 pass
#                         # Fetch and display sources if enabled
#             if st.session_state.show_sources and st.session_state.conversation_id:
#                 try:
#                     conv_url = f"http://13.233.150.156:8505/conversation/{st.session_state.conversation_id}"
#                     conv_resp = requests.get(conv_url, timeout=30)
#                     if conv_resp.ok:
#                         conv_data = conv_resp.json()
#                         # Get the last assistant message with sources
#                         for msg in reversed(conv_data["messages"]):
#                             if msg["role"] == "assistant" and msg.get("sources"):
#                                 display_sources(msg["sources"])
#                                 break
#                     # Silently continue if sources can't be fetched
#                 except Exception as e:
#                     print(f"Error fetching sources: {e}")
#         except Exception as e:
#             st.error(f"An error occurred during query processing: {str(e)}")
#             st.error("Full error details:")
#             st.exception(e)

# app/main.py
import streamlit as st
from pathlib import Path
import time
from typing import List, Dict
import os, sys
from urllib.parse import urlencode
from pinecone import Pinecone, ServerlessSpec
from PIL import Image
import requests
import json

#################
# Please comment this line while working on local machine
# import sys
# sys.modules["sqlite3"] = __import__("pysqlite3")
####################

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.config import config

# Set page config as the first Streamlit command
st.set_page_config(
    page_title=config.APP_TITLE,
    layout="wide",
)

## Adding customised avatar for the bot
assistant_avatar = Image.open("app/icon_tms.png")

## Load source URL mapping
def load_source_url_mapping():
    """Load source URL mapping from JSON file."""
    try:
        with open("source_url_mapping.json", "r") as f:
            mapping_data = json.load(f)
            url_map = {}
            display_name_map = {}
            
            for item in mapping_data.get("url_mapping", []):
                file_name = item["file_name"]
                url_map[file_name] = item["source_url"]
                if "display_name" in item:
                    display_name_map[file_name] = item["display_name"]
            
            return {"urls": url_map, "display_names": display_name_map}
    except Exception as e:
        print(f"Error loading source URL mapping: {e}")
        return {"urls": {}, "display_names": {}}

# Initialize source URL mapping
source_url_mapping = load_source_url_mapping()

def check_environment():
    """Check if all required environment variables are set."""
    missing_vars = []
    
    if not config.OPENAI_API_KEY:
        missing_vars.append("OPENAI_API_KEY")
    if not config.PINECONE_API_KEY:
        missing_vars.append("PINECONE_API_KEY")
    if not config.PINECONE_ENVIRONMENT:
        missing_vars.append("PINECONE_ENVIRONMENT")
    
    if missing_vars:
        error_msg = f"Missing required environment variables: {', '.join(missing_vars)}\n"
        error_msg += "Please ensure these variables are set in your .env file or environment."
        raise ValueError(error_msg)

def display_sources(sources: List[Dict]):
    """Display unique source URLs with display names after response message."""
    if not sources:
        return
    
    # Track unique sources to avoid duplicates
    unique_sources = {}
    
    # Extract and deduplicate sources
    for source in sources:
        metadata = source.get('metadata', {})
        source_name = metadata.get('source', 'Source')
        
        # Skip if we've already processed this source
        if source_name in unique_sources:
            continue
            
        # Try to find URL and display name in the mapping first, then fallback
        url = ""
        display_name = source_name
        
        # Check if source exists in our mapping
        if source_name in source_url_mapping["urls"]:
            url = source_url_mapping["urls"][source_name]
            # Use display name if available, otherwise use source name
            if source_name in source_url_mapping["display_names"]:
                display_name = source_url_mapping["display_names"][source_name]
        else:
            url = metadata.get('url', '')
        
        # Only store if it has a URL
        if url:
            unique_sources[source_name] = {
                "url": url,
                "display_name": display_name
            }
    
    # Display unique sources as simple links
    if unique_sources:
        st.markdown("***")
        st.markdown("**Sources:**")
        sources_markdown = ""
        for i, (_, source_info) in enumerate(unique_sources.items()):
            if i > 0:
                sources_markdown += " | "
            sources_markdown += f"[{source_info['display_name']}]({source_info['url']})"
        st.markdown(sources_markdown)

# Initialize session state at the very top to avoid KeyError
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "current_sources" not in st.session_state:
    st.session_state.current_sources = []
if "context_window" not in st.session_state:
    st.session_state.context_window = 5
if "max_history" not in st.session_state:
    st.session_state.max_history = 10
if "show_sources" not in st.session_state:
    st.session_state.show_sources = True
if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = None

st.title(config.APP_TITLE)

# st.markdown("""
# Get answers to all your TMS Cytric related queries.
# """)

st.markdown("Please don’t use any personal data. Note that responses are provided by a chatbot powered by Artificial Intelligence technology and not reviewed by humans. Therefore, the responses to your questions may not be accurate.")


# Floating "New Conversation" Button at bottom-right
# st.markdown("""
#     <style>
#     .new-convo-button {
#         position: fixed;
#         bottom: 20px;
#         right: 30px;
#         z-index: 9999;
#     }
#     </style>
#     <div class="new-convo-button">
#         <form action="" method="post">
#             <button type="submit">🔄 New Conversation</button>
#         </form>
#     </div>
# """, unsafe_allow_html=True)

# Clear session state on button click (handle post request)
if st.session_state.get("reset_chat", False):
    st.session_state.chat_history = []
    st.session_state.current_sources = []
    st.session_state.conversation_id = None  # Reset conversation_id for new session
    st.session_state.reset_chat = False
    st.rerun()

# Use JS to detect button submit and set Streamlit state
st.markdown("""
    <script>
    const form = document.querySelector('.new-convo-button form');
    form.addEventListener('submit', async function(event) {
        event.preventDefault();
        await fetch('', { method: 'POST' });
        window.parent.postMessage({type: 'streamlit:setComponentValue', value: true}, '*');
    });
    </script>
""", unsafe_allow_html=True)


# Chat interface
for message in st.session_state.chat_history:
    with st.chat_message(
        name=message["role"],
        avatar=assistant_avatar if message["role"] == "assistant" else None
    ):
        st.write(message["content"])

# We don't need the separate sources display section anymore
# since we're showing sources directly after each assistant message


# User input
user_input = st.chat_input("Ask me anything about TMS Cytric...")

# Update the query processing in the main chat interface
if user_input:
    # Add user message to chat history
    st.session_state.chat_history.append({
        "role": "user",
        "content": user_input
    })
    
    # Display user message
    with st.chat_message("user"):
        st.write(user_input)
    
    # Create a placeholder for the streaming response
    with st.chat_message(
        "assistant",
        avatar=assistant_avatar
        ):
        response_placeholder = st.empty()
        
        try:
            # Prepare payload for API
            payload = {
                "message": user_input,
                "chat_history": st.session_state.chat_history[-st.session_state.max_history:],
                "context_window": st.session_state.context_window,
                "max_history": st.session_state.max_history,
                "include_sources": True,
                "conversation_id": st.session_state.conversation_id
            }
            # Log the payload for debugging
            #print("Payload being sent to API:", json.dumps(payload, indent=2))
            api_url = "http://13.233.150.156:8505/chat/stream"
            
            # Make the API call outside the spinner context
            response = requests.post(api_url, json=payload, stream=True, timeout=120)
            
            # Initialize response
            full_response = ""
            
            # Setup progress indicator
            with st.status("Thinking...", state="running") as status:
                # Process streaming response
                for chunk in response.iter_content(chunk_size=None, decode_unicode=True):
                    if chunk:
                        # On first chunk, update status
                        if not full_response:
                            # Update status instead of stopping it
                            status.update(label="Generating response...", state="running")
                        
                        # Update response
                        full_response += chunk
                        response_placeholder.markdown(full_response)
                
                # Complete the status when done
                status.update(label="Response complete", state="complete")
            
            # After streaming the response and updating chat history, fetch and display sources if enabled
            # print(full_response)
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": full_response
            })
            # Update conversation_id from API response header if present
            if "conversation_id" in response.headers:
                st.session_state.conversation_id = int(response.headers["conversation_id"])
            else:
                pass
                        # Fetch and display sources if enabled
            if st.session_state.show_sources and st.session_state.conversation_id:
                try:
                    conv_url = f"http://13.233.150.156:8505/conversation/{st.session_state.conversation_id}"
                    conv_resp = requests.get(conv_url, timeout=30)
                    if conv_resp.ok:
                        conv_data = conv_resp.json()
                        # Get the last assistant message with sources
                        for msg in reversed(conv_data["messages"]):
                            if msg["role"] == "assistant" and msg.get("sources"):
                                display_sources(msg["sources"])
                                break
                    # Silently continue if sources can't be fetched
                except Exception as e:
                    print(f"Error fetching sources: {e}")
        except Exception as e:
            st.error(f"An error occurred during query processing: {str(e)}")
            st.error("Full error details:")
            st.exception(e)