
import streamlit as st
from chat_bot import chatbot
from langchain_core.messages import HumanMessage, AIMessage
import uuid


def generate_thread_id():
    return str(uuid.uuid4())


def add_thread(thread_id):
    if thread_id not in st.session_state['chat_threads']:
        st.session_state['chat_threads'].append(thread_id)


def reset_chat():
    thread_id = generate_thread_id()
    st.session_state['thread_id'] = thread_id
    add_thread(thread_id)
    st.session_state['message_history'] = []


def load_conversation_history(thread_id):
    state = chatbot.get_state(
        config={'configurable': {'thread_id': thread_id}}
    )
    return state.values.get('messages', [])


# Initialize session state
if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []

if 'thread_id' not in st.session_state:
    st.session_state['thread_id'] = generate_thread_id()

if 'chat_threads' not in st.session_state:
    st.session_state['chat_threads'] = []
if 'thread_titles' not in st.session_state:
    st.session_state['thread_titles'] = {}

add_thread(st.session_state['thread_id'])


# Sidebar
st.sidebar.title("Chatbot")

if st.sidebar.button("New Chat"):
    reset_chat()
    st.rerun()

st.sidebar.header("My Conversations")

for thread_id in st.session_state['chat_threads']:

    title = st.session_state['thread_titles'].get(thread_id)
    if not title:
        continue  # Skip threads without titles


    if st.sidebar.button(title, key=f"thread_{thread_id}"):
        st.session_state['thread_id'] = thread_id

        try:
            messages = load_conversation_history(thread_id)
            temp_messages = []

            for msg in messages:
                if isinstance(msg, HumanMessage):
                    role = 'user'
                elif isinstance(msg, AIMessage):
                    role = 'assistant'
                else:
                    continue

                temp_messages.append({
                    'role': role,
                    'content': msg.content
                })

            st.session_state['message_history'] = temp_messages

        except Exception as e:
            st.error(f"Could not load conversation: {e}")
            st.session_state['message_history'] = []

        st.rerun()


# Main chat area
st.title("Chatbot")

for message in st.session_state['message_history']:
    with st.chat_message(message['role']):
        st.write(message['content'])


# Process input only after the user submits a message
user_input = st.chat_input("Type here")

if user_input and user_input.strip():
    thread_id = st.session_state['thread_id']

    if thread_id not in st.session_state['thread_titles']:
        title = user_input.strip().replace("\n", " ")

        if len(title) > 30:
            title = title[:27] + "..."

        st.session_state['thread_titles'][thread_id] = title

    config = {
        'configurable': {
            'thread_id': st.session_state['thread_id']
        }
    }

    # Display user message
    st.session_state['message_history'].append({
        'role': 'user',
        'content': user_input
    })

    with st.chat_message('user'):
        st.write(user_input)

    # Generate and display assistant response
    with st.chat_message('assistant'):
        try:
            ai_message = st.write_stream(
                chunk.content
                for chunk, metadata in chatbot.stream(
                    {'messages': [HumanMessage(content=user_input)]},
                    config=config,
                    stream_mode='messages'
                )
                if isinstance(chunk.content, str) and chunk.content
            )

            st.session_state['message_history'].append({
                'role': 'assistant',
                'content': ai_message or ''
            })

        except Exception as e:
            st.error(f"Error generating response: {e}")
