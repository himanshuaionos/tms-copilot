# app/main.py
import streamlit as st
from pathlib import Path
from datetime import datetime
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
<<<<<<< HEAD
assistant_avatar = Image.open("app/icon_tms.png") 
=======
assistant_avatar = None #Image.open("app/icon_tms.png") 
>>>>>>> 04769348975d273406f55105f939376498ccebf0

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
    """Display sources with proper formatting and links."""
    if not sources:
        return
    
    with st.expander("📚 Source References", expanded=False):
        for i, source in enumerate(sources, 1):
            metadata = source.get('metadata', {})
            url = metadata.get('url', '')
            
            st.markdown(f"### Reference {i}")
            if url:
                st.markdown(f"[🔗 {metadata.get('source', 'Source')}]({url})")
            else:
                st.markdown(f"**{metadata.get('source', 'Source')}**")
            
            # Show preview text
            preview_text = source['text'][:300] + "..." if len(source['text']) > 300 else source['text']
            st.caption(preview_text)
            st.divider()

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
<<<<<<< HEAD
=======
if "show_feedback" not in st.session_state:
    st.session_state.show_feedback = False
if "feedback_submitted" not in st.session_state:
    st.session_state.feedback_submitted = False
if "feedback_positive" not in st.session_state:
    st.session_state.feedback_positive = False
if "feedback_negative" not in st.session_state:
    st.session_state.feedback_negative = False
>>>>>>> 04769348975d273406f55105f939376498ccebf0

st.title(config.APP_TITLE)
st.markdown("Please don’t use any personal data. Note that responses are provided by a chatbot powered by Artificial Intelligence technology and not reviewed by humans. Therefore, the responses to your questions may not be accurate.")

<<<<<<< HEAD
# st.markdown("""
# Get answers to all your TMS Cytric related queries.
# """)

st.markdown("Please don’t use any personal data. Note that responses are provided by a chatbot powered by Artificial Intelligence technology and not reviewed by humans. Therefore, the responses to your questions may not be accurate.")
=======
def on_yes_click():
    st.session_state.feedback_positive = True
    st.session_state.feedback_negative = False
    
def on_no_click():
    st.session_state.feedback_positive = False
    st.session_state.feedback_negative = True


def save_feedback(feedback_data):
    """Save feedback data to both JSON file and PostgreSQL database with user info."""
    # Add timestamp to feedback
    feedback_data["timestamp"] = datetime.now().isoformat()
    
    # Add user information
    feedback_data["user_id"] = 1
    feedback_data["username"] = 'divyesh'
    feedback_data["user_full_name"] = 'Divyesh Chhabra'
    
    # 1. Save to JSON file (keeping this for backward compatibility)
    feedback_file = config.BASE_DIR / "feedback_data.json"
    
    # Load existing feedback if file exists
    if feedback_file.exists():
        with open(feedback_file, "r") as f:
            try:
                existing_data = json.load(f)
            except json.JSONDecodeError:
                existing_data = []
    else:
        existing_data = []
    
    # Append new feedback and save
    existing_data.append(feedback_data)
    with open(feedback_file, "w") as f:
        json.dump(existing_data, f, indent=2)
    
    print("✅ Feedback saved to JSON file successfully.")
    
    # 2. Save to SQLite database
    try:
        print("Attempting to save feedback to PostgreSQL database...")
        # Prepare data for insertion
        print("Preparing feedback payload for database insertion...")
        feedback_payload = {
            "user_id": feedback_data.get("user_id"),
            "username": feedback_data.get("username", ""),
            "user_full_name": feedback_data.get("user_full_name", ""),
            "feedback_type": feedback_data.get("feedback_type", ""),
            "conversation_id": feedback_data.get("conversation_id", None),
            "time_saved": feedback_data.get("time_saved", ""),
            "rating": feedback_data.get("rating", 0),
            "recommend": feedback_data.get("recommend", ""),
            "liked_aspects": json.dumps(feedback_data.get("liked_aspects", [])),
            "other_liked": feedback_data.get("other_liked", ""),
            "improvement_suggestions": feedback_data.get("improvement_suggestions", ""),
            "issues": json.dumps(feedback_data.get("issues", [])),
            "other_feedback": feedback_data.get("other_feedback", "")
        }
        
        # Log the payload for debugging
        print("Payload being sent to API:", json.dumps(feedback_payload, indent=2))
        api_url = "http://localhost:8000/chat/feedback"
        response = requests.post(api_url, json=feedback_payload)
        if response.ok:
            print("✅ Feedback saved to SQLite database successfully.")
        else:
            print(f"❌ Failed to save feedback to SQLite database: {response.status_code} {response.text}")
        
    except Exception as e:
        print(f"❌ Database error: {str(e)}")
        print(f"Error type: {type(e).__name__}")

        import traceback
        traceback.print_exc()
        print("Feedback saved to JSON file only.")
>>>>>>> 04769348975d273406f55105f939376498ccebf0


# Add handlers for submit buttons
def on_submit_positive():
    time_saved = st.session_state.time_saved
    rating = st.session_state.rating
    recommend = st.session_state.recommend
    liked_aspects = st.session_state.liked_aspects if "liked_aspects" in st.session_state else []
    other_liked = st.session_state.other_liked if "other_liked" in st.session_state else ""
    improvement_suggestions = st.session_state.improvement_suggestions if "improvement_suggestions" in st.session_state else ""
    
    feedback_data = {
        "feedback_type": "positive",
        "conversation_id": st.session_state.conversation_id,
        "time_saved": time_saved,
        "rating": rating,
        "recommend": recommend,
        "liked_aspects": liked_aspects,
        "other_liked": other_liked,
        "improvement_suggestions": improvement_suggestions
    }
    
    # Save feedback with response
    save_feedback(feedback_data)
    
    st.session_state.feedback_submitted = True

def on_submit_negative():
    issues = st.session_state.issues if "issues" in st.session_state else []
    other_feedback = st.session_state.other_feedback if "other_feedback" in st.session_state else ""
    rating = st.session_state.rating
    recommend = st.session_state.recommend
    improvement = st.session_state.improvement if "improvement" in st.session_state else ""
    
    feedback_data = {
        "feedback_type": "negative",
        "conversation_id": st.session_state.conversation_id,
        "issues": issues,
        "other_feedback": other_feedback,
        "rating": rating,
        "recommend": recommend,
        "improvement_suggestions": improvement
    }
    
    # Save feedback with response
    save_feedback(feedback_data)
    
    st.session_state.feedback_submitted = True


# # Floating "New Conversation" Button at bottom-right
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
    st.session_state.show_feedback = False
    st.session_state.feedback_submitted = True
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

# Display sources if enabled
if st.session_state.show_sources and st.session_state.current_sources:
    with st.expander("Source Documents", expanded=False):
        for i, source in enumerate(st.session_state.current_sources):
            st.markdown(f"**Source {i+1}**")
            st.write(source["text"])
            if "metadata" in source and "url" in source["metadata"]:
                st.markdown(f"[Link to source]({source['metadata']['url']})")
            st.divider()


# User input
user_input = st.chat_input("Ask me anything about TMS Cytric...")

# Update the query processing in the main chat interface
if user_input:
    st.session_state.show_feedback = False

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
<<<<<<< HEAD
            #print("Payload being sent to API:", json.dumps(payload, indent=2))
            api_url = "http://172.31.3.215:8505/chat/stream"
=======
            print("Payload being sent to API:", json.dumps(payload, indent=2))
            api_url = "http://localhost:8000/chat/stream"
>>>>>>> 04769348975d273406f55105f939376498ccebf0
            response = requests.post(api_url, json=payload, stream=True, timeout=120)
            
            full_response = ""
            # Stream the response as it arrives
            for chunk in response.iter_content(chunk_size=None, decode_unicode=True):
                if chunk:
                    full_response += chunk
                    response_placeholder.markdown(full_response)
<<<<<<< HEAD
            # After streaming the response and updating chat history, fetch and display sources if enabled
            # print(full_response)
=======

            # After streaming the response and updating chat history, fetch and display sources if enabled            
>>>>>>> 04769348975d273406f55105f939376498ccebf0
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": full_response
            })
<<<<<<< HEAD
=======

>>>>>>> 04769348975d273406f55105f939376498ccebf0
            # Update conversation_id from API response header if present
            if "conversation_id" in response.headers:
                st.session_state.conversation_id = int(response.headers["conversation_id"])
            else:
                pass
            # Fetch and display sources if enabled
            if st.session_state.show_sources and st.session_state.conversation_id:
                try:
<<<<<<< HEAD
                    conv_url = f"http://172.31.3.215:8505/conversation/{st.session_state.conversation_id}"
=======
                    conv_url = f"http://localhost:8000/conversation/{st.session_state.conversation_id}"
>>>>>>> 04769348975d273406f55105f939376498ccebf0
                    conv_resp = requests.get(conv_url, timeout=30)
                    if conv_resp.ok:
                        conv_data = conv_resp.json()
                        # Get the last assistant message with sources
                        for msg in reversed(conv_data["messages"]):
                            if msg["role"] == "assistant" and msg.get("sources"):
                                display_sources(msg["sources"])
                                break
                    else:
                        st.warning("Could not fetch sources for this response.")
                except Exception as e:
                    st.warning(f"Error fetching sources: {e}")
<<<<<<< HEAD
=======

            st.session_state.show_feedback = True
>>>>>>> 04769348975d273406f55105f939376498ccebf0
        except Exception as e:
            st.error(f"An error occurred during query processing: {str(e)}")
            st.error("Full error details:")
            st.exception(e)


# Display feedback section if needed
if st.session_state.show_feedback and not st.session_state.feedback_submitted:
    st.markdown("---")
    st.markdown("### Feedback")
    st.write("Did the AI Assistant help you resolve the customer's issue?")
    
    col1, col2 = st.columns(2)
    with col1:
        st.button("👍 Yes", key="yes_button", on_click=on_yes_click, use_container_width=True)
    with col2:
        st.button("👎 No", key="no_button", on_click=on_no_click, use_container_width=True)
    
    # Show positive feedback form
    if st.session_state.feedback_positive:
        st.write("### Thank you for your positive feedback!")
        
        st.selectbox(
            "How much time did this save you?",
            ["Less than 30 seconds", "30 seconds to 1 minute", "1-2 minutes", "More than 2 minutes"],
            index=0,
            key="time_saved"
        )
        
        st.slider("Rate the AI Assistant's response (1-10)", 1, 10, 7, key="rating")
        
        st.radio(
            "Would you recommend this AI Assistant to other friends?",
            ["Yes", "No"],
            index=0,
            key="recommend"
        )
        
        st.multiselect(
            "What specifically did you like about the response?",
            ["Completely correct response", "Correct response with minor omissions", "Other"],
            key="liked_aspects"
        )
        
        if "liked_aspects" in st.session_state and "Other" in st.session_state.liked_aspects:
            st.text_input("Please specify what else you liked:", key="other_liked")
        
        st.text_area("Any suggestions for improvement? (Optional)", key="improvement_suggestions")
        
        st.button("Submit Feedback", key="submit_positive", on_click=on_submit_positive)
        
        if st.session_state.feedback_submitted:
            st.success("Thank you for your feedback!")
    
    # Show negative feedback form
    if st.session_state.feedback_negative:
        st.write("### We're sorry the response didn't meet your needs.")
        
        # st.multiselect(
        #     "Please select your feedback type:",
        #     ["Missing information", "Incorrect information", "Response too complex",
        #     "Response not relevant to query", "System too slow", "Other"],
        #     key="issues"
        # )
        
        if "issues" in st.session_state and "Other" in st.session_state.issues:
            st.text_input("Please specify:", key="other_feedback")
        
        st.slider("Rate the AI Assistant's response (1-10)", 1, 10, 3, key="rating")
        
        st.radio(
            "Would you recommend this AI Assistant to other friends?",
            ["Yes", "No"],
            index=1,
            key="recommend"
        )

        st.multiselect(
            "Please select your feedback type:",
            ["Incorrect response", "Response is partially correct", "Response was incomplete",
            "Response is very verbose ", "Information provided is outdated", "Other"],
            key="issues"
        )
        
        st.text_area("What would have made this response more helpful? (Optional)", key="improvement")
        
        st.button("Submit Feedback", key="submit_negative", on_click=on_submit_negative)
        
        if st.session_state.feedback_submitted:
            st.success("Thank you for your feedback!")