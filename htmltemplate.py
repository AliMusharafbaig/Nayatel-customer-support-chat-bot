# htmltemplate.py

css = '''
<style>
body {
    background-color: #1e1e1e;
    color: #e0e0e0;
}
header {
    background-color: #1e1e1e;
    color: #e0e0e0;
}
.chat-message {
    padding: 1.5rem; 
    border-radius: 0.5rem; 
    margin-bottom: 1rem; 
    display: flex;
}
.chat-message.user {
    background-color: #333;
}
.chat-message.bot {
    background-color: #444;
}
.chat-message .avatar {
  width: 25%;
}
.chat-message .avatar img {
  max-width: 100px;
  max-height: 100px;
  border-radius: 50%;
  object-fit: cover;
}
.chat-message .message {
  width: 75%;
  padding: 0 1.5rem;
  color: #fff;
}
.sidebar .block-container {
    background-color: #1e1e1e;
}
.sidebar .sidebar-content {
    background-color: #1e1e1e;
    color: #e0e0e0;
}
.sidebar .block-container h2 {
    color: #e0e0e0;
}
.sidebar .block-container .stTextInput input {
    background-color: #333;
    color: #e0e0e0;
}
.sidebar .block-container .stButton button {
    background-color: #333;
    color: #e0e0e0;
}
</style>
'''

faq_css = '''
<style>
.faq-button {
    display: block;
    width: 100%;
    padding: 10px;
    margin-bottom: 5px;
    background-color: #444;
    color: #fff;
    border: none;
    text-align: left;
    font-size: 1rem;
    border-radius: 5px;
}
.faq-button:hover {
    background-color: #555;
}
</style>
'''

bot_template = '''
<div class="chat-message bot">
    <div class="avatar">
        <img src="data:image/png;base64,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">
    </div>
    <div class="message">{{MSG}}</div>
</div>
'''

faq_template = '''
<div class="faq-button" onclick="document.getElementById('{faq_id}').click()">
    {faq}
</div>
'''
