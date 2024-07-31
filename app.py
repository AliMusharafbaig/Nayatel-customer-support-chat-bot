import streamlit as st
from dotenv import load_dotenv
import os
from PyPDF2 import PdfReader
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.llms import HuggingFaceHub
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
from htmltemplate import css, bot_template, faq_css, faq_template
import concurrent.futures
from transformers import AutoTokenizer
import re

# Set page configuration
st.set_page_config(page_title="Nayatel AI Bot", page_icon=":books:", layout="wide")

# Load environment variables
load_dotenv()

# Ensure the Hugging Face Hub token is set
huggingface_api_token = os.getenv('HUGGINGFACEHUB_API_TOKEN')
if not huggingface_api_token:
    st.error("HUGGINGFACEHUB_API_TOKEN environment variable is missing.")
    st.stop()

os.environ["HUGGINGFACEHUB_API_TOKEN"] = huggingface_api_token

# Predefined PDF path
PDF_PATH = "nayatelinformation.pdf"

# Function to extract text from a single page
def extract_text_from_page(page_info):
    page, pdf_name, page_number = page_info
    try:
        page_text = page.extract_text()
        return page_text if page_text else ""
    except Exception:
        return ""

# Function to get raw text from the predefined PDF
def get_pdf_text(pdf_path):
    with open(pdf_path, 'rb') as file:
        reader = PdfReader(file)
        page_infos = [(page, pdf_path, i + 1) for i, page in enumerate(reader.pages)]
        with concurrent.futures.ThreadPoolExecutor() as executor:
            results = executor.map(extract_text_from_page, page_infos)
    return "".join(results)

# Function to split text into chunks
def get_text_chunks(raw_text, chunk_size=1000):
    tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")
    tokens = tokenizer(raw_text, return_tensors="pt").input_ids[0]
    chunks = [tokens[i:i + chunk_size] for i in range(0, len(tokens), chunk_size)]
    chunks = [chunk for chunk in chunks if len(chunk) < 16000]
    return [tokenizer.decode(chunk) for chunk in chunks]

# Function to create a vector store
def get_vectorstore(text_chunks):
    embeddings = HuggingFaceEmbeddings()
    return FAISS.from_texts(texts=text_chunks, embedding=embeddings)

# Function to create a conversation chain
def get_conversation_chain(vectorstore):
    llm = HuggingFaceHub(repo_id="mistralai/Mistral-Nemo-Instruct-2407",
                         model_kwargs={"temperature": 0.5, "max_length": 512},
                         huggingfacehub_api_token=huggingface_api_token)
    memory = ConversationBufferMemory(memory_key='chat_history', return_messages=True)
    return ConversationalRetrievalChain.from_llm(llm=llm, retriever=vectorstore.as_retriever(), memory=memory)

# Pre-process the PDF and initialize the conversation chain
with st.spinner("Setting up the bot..."):
    raw_text = get_pdf_text(PDF_PATH)
    text_chunks = get_text_chunks(raw_text)
    vectorstore = get_vectorstore(text_chunks)
    st.session_state.conversation = get_conversation_chain(vectorstore)
    st.success("Vector store (FAISS index) created successfully!")

# Function to handle user input
def handle_userinput(user_question):
    if st.session_state.conversation:
        # Determine if the question is a greeting or general support query
        greetings = re.compile(r'\b(hi|hello|hey|good morning|good evening|good afternoon|thank you|thanks)\b', re.IGNORECASE)
        general_support_queries = re.compile(r'\b(i need help|i\'m in trouble|support|help me|assistance)\b', re.IGNORECASE)
        nayatel_related = re.compile(r'\b(nayatel|internet|fiber|broadband|connectivity|modem|router|PPPoE|Ethernet|FTTH|troubleshoot|support)\b', re.IGNORECASE)
        irrelevant = re.compile(r'\b(actor|celebrity|movie|programming|python|code)\b', re.IGNORECASE)

        llm = HuggingFaceHub(repo_id="mistralai/Mistral-Nemo-Instruct-2407",
                             model_kwargs={"temperature": 0.5, "max_length": 512},
                             huggingfacehub_api_token=huggingface_api_token)

        if greetings.search(user_question):
            llm_response = llm({'question': user_question})
            st.write(bot_template.replace("{{MSG}}", llm_response['content']), unsafe_allow_html=True)
            return
        elif general_support_queries.search(user_question):
            llm_response = llm({'question': user_question})
            st.write(bot_template.replace("{{MSG}}", llm_response['content']), unsafe_allow_html=True)
            return
        elif irrelevant.search(user_question):
            st.write(bot_template.replace("{{MSG}}", "Sorry, I can only answer questions related to Nayatel services and telecommunications. Please make sure your question is related to those topics."), unsafe_allow_html=True)
            return
        elif not nayatel_related.search(user_question):
            st.write(bot_template.replace("{{MSG}}", "I'm here to answer questions related to Nayatel services and telecommunications. Please ask a relevant question."), unsafe_allow_html=True)
            return

        # Display user message
        st.write(f'<div class="user-message">{user_question}</div>', unsafe_allow_html=True)

        # Process and display bot response
        response = st.session_state.conversation({'question': user_question})
        st.session_state.chat_history = response['chat_history']

        relevant_answer_found = False
        for i, message in enumerate(st.session_state.chat_history):
            if i % 2 != 0:
                answer = message.content.split("Helpful Answer: ")[-1] if "Helpful Answer: " in message.content else message.content
                if len(answer.split()) > 5:  # Ensure answer is meaningful
                    st.write(bot_template.replace("{{MSG}}", answer), unsafe_allow_html=True)
                    relevant_answer_found = True
                    break

        if not relevant_answer_found:
            # Use LLM for a comprehensive answer if the PDF content is insufficient
            llm_response = llm({'question': user_question})
            st.write(bot_template.replace("{{MSG}}", llm_response['content']), unsafe_allow_html=True)
    else:
        st.error("Conversation chain is not initialized. Please process the documents first.")

# Function to display FAQs and handle their selection
def display_faqs():
    faqs = [
        "What is Nayatel fiber internet?",
        "What are the benefits of FTTH over traditional broadband?",
        "What equipment is needed for fiber internet connection?",
        "How do I know which internet plan is right for me?",
        "What is FTTH?",
        "Do you offer technical support over the phone or online chat?",
        "Can I bundle internet with other services like cable TV or phone?",
        "How can I pay my bill online?"
    ]
    st.sidebar.markdown(faq_css, unsafe_allow_html=True)
    st.sidebar.markdown("<h2>FAQS</h2>", unsafe_allow_html=True)
    for faq in faqs:
        if st.sidebar.button(faq):
            st.session_state.user_question = faq

def main():
    st.write(css, unsafe_allow_html=True)

    if "conversation" not in st.session_state:
        st.session_state.conversation = None
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = None
    st.session_state.bot_avatar_url = "data:image/png;base64,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"  #nayatel image logo
    st.header("Nayatel Customer Support")

    # Display FAQs in the sidebar
    display_faqs()

    # User question input
    user_question = st.text_input("Ask a question regarding Nayatel services or technology:")
    if user_question or st.session_state.get("user_question"):
        if not user_question:
            user_question = st.session_state.get("user_question")
        handle_userinput(user_question)

if __name__ == '__main__':
    main()
