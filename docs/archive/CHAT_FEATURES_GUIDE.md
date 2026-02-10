# 💬 Chat Features Guide

## ✅ New Features Added

The Streamlit UI now supports **multiple chat sessions**, **follow-up questions**, and **better conversation management**!

---

## 🎯 Features

### 1. **Multiple Chat Sessions** 📁
- Create unlimited chat sessions
- Each chat has its own conversation history
- Switch between chats seamlessly
- All chats persist during your session

### 2. **New Chat Button** ➕
- Located in the top-right corner
- Creates a fresh chat session instantly
- Automatically switches to the new chat

### 3. **Chat Sidebar** 💬
- Located on the left side
- Shows all your chat sessions
- **Newest chats appear at the top** ⭐
- Click any chat to switch to it
- Delete chats you don't need (🗑️ button)

### 4. **Latest Messages on Top** 🔝
- Messages now display in reverse order
- Most recent message appears at the top
- Easier to see latest responses
- No more scrolling to the bottom!

### 5. **Follow-up Questions** 🔄
- Ask follow-up questions naturally
- System tracks last 5 messages for context
- Works across the same chat session
- Badge shows when context is available

---

## 🎨 UI Layout

```
┌─────────────────────────────────────────────────────┐
│  🤖 Agriculture AI Assistant        [➕ New Chat]   │
├─────────────────────────────────────────────────────┤
│  Sidebar:                                           │
│  ┌──────────────────┐                               │
│  │ 💬 Chat Sessions │                               │
│  ├──────────────────┤                               │
│  │ 📍 Chat 3        │ ← Current (blue)              │
│  │ "Find Roundup"   │                               │
│  │ (5 msgs)     [🗑️]│                               │
│  ├──────────────────┤                               │
│  │ 💬 Chat 2        │ ← Other chats (gray)          │
│  │ "Weather in..."  │                               │
│  │ (3 msgs)     [🗑️]│                               │
│  ├──────────────────┤                               │
│  │ 💬 Chat 1        │                               │
│  │ "Soil data..."   │                               │
│  │ (2 msgs)     [🗑️]│                               │
│  └──────────────────┘                               │
│                                                     │
│  [Example questions...]                             │
│  [Input area...]                                    │
│                                                     │
│  💬 Conversation            [🗑️ Clear Chat]         │
│  ┌─────────────────────────────────────┐           │
│  │ 🤖 AgAdvisor (LATEST - on top!)    │           │
│  │ [Most recent response]              │           │
│  └─────────────────────────────────────┘           │
│  ┌─────────────────────────────────────┐           │
│  │ 👤 You:                              │           │
│  │ [Most recent question]               │           │
│  └─────────────────────────────────────┘           │
│  ┌─────────────────────────────────────┐           │
│  │ 🤖 AgAdvisor (older)                │           │
│  │ [Previous response]                  │           │
│  └─────────────────────────────────────┘           │
│  ...                                                │
└─────────────────────────────────────────────────────┘
```

---

## 🚀 How to Use

### Starting a New Chat:
1. Click **"➕ New Chat"** button (top-right)
2. New empty chat opens automatically
3. Start asking questions!

### Switching Between Chats:
1. Open sidebar (left side)
2. Click any chat to switch to it
3. Blue highlight (📍) shows current chat

### Deleting Chats:
1. Open sidebar
2. Find the chat you want to delete
3. Click **🗑️** button next to it
4. Note: Cannot delete the current chat if it's the only one

### Clearing Current Chat:
1. Click **"🗑️ Clear Chat"** button (next to conversation title)
2. Clears all messages in current chat
3. Chat session remains (empty)

### Follow-up Questions:
1. Ask an initial question
2. Get a response
3. Ask a related follow-up question
4. System automatically uses previous context
5. Look for context indicator in metadata

---

## 💡 Examples

### Example 1: Multiple Topics in Different Chats

**Chat 1: Weather Questions**
```
You: What's the weather in London?
Bot: The weather in London is...

You: How about Paris?
Bot: The weather in Paris is...
```

**Chat 2: CDMS Labels** (Click "➕ New Chat")
```
You: Find Roundup label
Bot: I found 3 labels for Roundup...

You: What about Sevin?
Bot: I found labels for Sevin...
```

**Chat 3: Agriculture Advice** (Click "➕ New Chat")
```
You: How to control aphids?
Bot: Based on research, you can...

You: What about organic methods?
Bot: For organic control...
```

### Example 2: Follow-up Questions (Same Chat)

```
You: What's the weather in New York?
Bot: New York is currently 20°C with clear skies...

You: How about tomorrow?  ← Follow-up
Bot: [Uses context: knows you're asking about New York weather]

You: Is it going to rain?  ← Another follow-up
Bot: [Still knows we're talking about New York]
```

---

## 🔍 Chat Management

### Sidebar Features:

#### Chat Display:
- **📍 Blue badge** - Current chat (you're in this one)
- **💬 Gray badge** - Other chats (click to switch)
- **Preview text** - First question from the chat
- **Message count** - "(X msgs)"
- **Delete button** - 🗑️ (only for non-current chats)

#### Sorting:
- Newest chats **always at the top**
- Based on creation time
- No manual sorting needed

#### Chat Naming:
- Auto-named: "Chat 1", "Chat 2", etc.
- Sequential numbering
- Future: Custom names (not implemented yet)

---

## 🎯 Latest Messages on Top

### Why This Change?

**Old Behavior:**
- Latest message at bottom
- Need to scroll down to see new responses
- Older messages pushed up

**New Behavior:**
- Latest message at **top** ⭐
- No scrolling needed
- Immediately see newest content
- Better for mobile/small screens

### Visual Flow:

```
┌─────────────────────────────────┐
│ 💬 Conversation   [🗑️ Clear]    │
├─────────────────────────────────┤
│                                 │
│ 🤖 AgAdvisor: [NEWEST - TOP]   │  ← Just added!
│ [Latest response here]          │
│                                 │
│ 👤 You: [Recent question]       │
│                                 │
│ 🤖 AgAdvisor: [Older]           │
│ [Previous response]             │
│                                 │
│ 👤 You: [Older question]        │
│                                 │
│ ... (older messages below)      │
│                                 │
└─────────────────────────────────┘
```

---

## 🔄 Follow-up Question Context

### How It Works:

1. **System tracks last 5 messages** in current chat
2. **Passes context to LLM** for better understanding
3. **Badge indicator** shows when context is used
4. **Works automatically** - no special syntax needed

### What Gets Tracked:

```python
# Last 5 messages before current question
Context = [
    {role: "user", content: "What's the weather in London?"},
    {role: "assistant", content: "London is 15°C..."},
    {role: "user", content: "How about tomorrow?"},  ← Understands this refers to London
    {role: "assistant", content: "Tomorrow will be..."},
    {role: "user", content: "Will it rain?"}  ← Still knows it's about London
]
```

### Context Indicator:

When a response uses context, you'll see in debug mode:
- `has_context: true`
- `context_messages: 5`

---

## 🎨 Visual Indicators

### Chat Status:
- **📍 Blue button** - Current chat
- **💬 Gray button** - Other chats
- **🗑️ Button** - Delete (only for non-current)

### Message Order:
- **Top** = Newest
- **Bottom** = Oldest

### Message Types:
- **👤 Blue box** - Your messages
- **🤖 Gray box** - Bot responses

### Badges:
- **🔧 Green** - Tool used
- **📊 Blue** - Confidence score
- **🔑 Orange** - Keywords
- **📚 Purple** - Citations (if available)

---

## 🐛 Troubleshooting

### Chat Not Switching?
- Make sure you clicked the chat button
- Check for blue highlight (📍)
- Try refreshing the page

### Delete Button Not Working?
- Can't delete current chat
- Switch to another chat first
- Need at least one chat to remain

### Follow-ups Not Working?
- Make sure you're in the same chat
- Context limited to last 5 messages
- Try being more specific

### Messages Not Appearing?
- Check you're in the right chat
- Look in sidebar for all chats
- Try clearing browser cache

---

## 🚀 Running the Updated UI

```bash
# Activate environment
conda activate agentic

# Run Streamlit
streamlit run src/streamlit_app_conversational.py
```

The app will open at `http://localhost:8501`

---

## ✅ What Changed in the Code

### Session State:
```python
# Before:
st.session_state.conversation_history = []

# After:
st.session_state.chats = {
    'chat_1': {
        'name': 'Chat 1',
        'messages': [],
        'created_at': timestamp
    }
}
st.session_state.current_chat_id = 'chat_1'
```

### Message Storage:
```python
# Before:
st.session_state.conversation_history.append(message)

# After:
current_chat = st.session_state.chats[st.session_state.current_chat_id]
current_chat['messages'].append(message)
```

### Message Display:
```python
# Before:
for message in messages:
    display(message)

# After:
for message in reversed(messages):  # Latest first!
    display(message)
```

---

## 🎯 Key Benefits

### Before:
- ❌ Single conversation only
- ❌ Can't separate topics
- ❌ Oldest messages at top
- ❌ Must clear all to start fresh

### After:
- ✅ Multiple chat sessions
- ✅ Separate topics easily
- ✅ **Latest messages at top** ⭐
- ✅ Create new chats anytime
- ✅ Switch between chats
- ✅ Delete unwanted chats
- ✅ Follow-up question context

---

## 📊 Session Management

### Data Structure:
```json
{
  "chats": {
    "chat_1": {
      "name": "Chat 1",
      "messages": [...],
      "created_at": 1234567890.123
    },
    "chat_2": {
      "name": "Chat 2",
      "messages": [...],
      "created_at": 1234567891.456
    }
  },
  "current_chat_id": "chat_2",
  "chat_counter": 2
}
```

### Message Structure:
```json
{
  "role": "user" or "assistant",
  "content": "Message text",
  "timestamp": 1234567890.123,
  "metadata": {
    "tool": "cdms_label",
    "confidence": 0.95,
    "has_context": true,
    "context_messages": 5,
    ...
  }
}
```

---

## 🎉 Summary

### New Features:
- ✅ Multiple chat sessions
- ✅ New chat button
- ✅ Chat sidebar with management
- ✅ **Latest messages on top** ⭐
- ✅ Chat deletion
- ✅ Follow-up question support
- ✅ Context tracking (last 5 messages)
- ✅ Visual indicators

### User Benefits:
- 📁 Organize conversations by topic
- 🔄 Ask follow-up questions naturally
- 🔝 See latest responses immediately
- 🗑️ Clean up unwanted chats
- 💬 Switch contexts easily

**Everything works out of the box!** Just run the UI and try it! 🚀

---

**Test it now:**
```bash
streamlit run src/streamlit_app_conversational.py
```

1. Click "➕ New Chat" → See new chat created
2. Ask a question → Get response
3. Check sidebar → See all chats listed (newest first)
4. Check conversation → Latest message is on top!
5. Ask follow-up → Context preserved!

🎉 **All features working!**


