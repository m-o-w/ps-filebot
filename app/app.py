import os
from llama_index import GPTVectorStoreIndex, SimpleDirectoryReader
import streamlit as st
from config import upload_directory
import random

# Load index from session if found
global_index = None
iterator = random.randint(1, 99)
print("Iterator: ",iterator)

if "index" in st.session_state: # check if the index variable exists in the session state object
    global_index = st.session_state.index.as_query_engine() # create a query engine from the index
    
if not os.path.exists(upload_directory):
    os.makedirs(upload_directory)
    

# ------------------------------------Code for setting API Key-------------------------------------
def button_click(user_api_key):
    if len(user_api_key) < 30:
        st.sidebar.error("Please enter valid API Key")
        return
    st.sidebar.write("Setting Key",user_api_key)
    os.environ["OPENAI_API_KEY"] = user_api_key
    st.experimental_rerun()

if os.environ.get("OPENAI_API_KEY") is None:
    # Get API Key
    user_api_key = st.sidebar.text_input("Your API Key Here")
    st.sidebar.warning("Get your OpenAI API key from [here](https://platform.openai.com/account/api-keys).\n")
    button = st.sidebar.button("Load Key")
    if button:
        button_click(user_api_key)
else:
    st.sidebar.success("API Key Loaded")
    reload_button = st.sidebar.button("Reload Key")
    if reload_button:
        os.environ.pop("OPENAI_API_KEY")
        st.experimental_rerun()
        

# FileManagement Save file
def save_uploaded_file(uploaded_file):
    print("save_uploaded_file Called: ",iterator)
    with open(os.path.join(upload_directory, uploaded_file.name), "wb") as file:
        file.write(uploaded_file.getbuffer())
        print("file.write Called: ",iterator)

# FileManagement Delete file
def delete_file(file_path):
    print("delete_file Called: ",iterator)
    if os.path.exists(file_path):
        os.remove(file_path)
        st.experimental_rerun()
    else:
        st.sidebar.error("File not found")

# Rebuild vector index        
def rebuild_index(from_directory):
    print("rebuild_index Called: ",iterator)
    global global_index
    document = SimpleDirectoryReader(from_directory).load_data()
    index_temp = GPTVectorStoreIndex(api_key=os.environ.get("OPENAI_API_KEY"))     ###### Temp
    st.session_state.index = GPTVectorStoreIndex.from_documents(document)
    global_index = st.session_state.index.as_query_engine()
    
# Read file dir and index files
def index_files():
    print("index_files Called: ",iterator)
    # Check if no files uploaded
    files = os.listdir(upload_directory)
    if len(files) == 0:
        st.sidebar.error("Please upload files")
        return None
        
    # Create index and persist
    if files is not None:
        rebuild_index(upload_directory)
        st.sidebar.write("Rebuild Index")
        
# Generate response from index
def answer_question(question):
    print("answer_question Called: ",iterator)                        
    response = global_index.query(question+"?")
    st.info(response)

# File upload section
uploaded_file = st.sidebar.file_uploader("Upload files")
if uploaded_file:
    save_uploaded_file(uploaded_file)
    del uploaded_file
        
# Display uploaded files and provide delete option
st.sidebar.header("Uploaded Files")
files = os.listdir(upload_directory)
for file_name in files:
    file_path = os.path.join(upload_directory, file_name)
    delete_button = st.sidebar.button(f"Delete: {file_name}")
    if delete_button:
        delete_file(file_path)
        
def main():
    print("main Called: ",iterator)
            
    #Start StreamLit
    st.title("File AI Bot")
    form = st.form("Input box", clear_on_submit=True)
    question = form.text_input("Send message", placeholder="Your question here")
    submit_button = form.form_submit_button("Send")
    
    # Someone have asked a question
    if question:
        print("question Called: ",iterator)
        if os.environ.get("OPENAI_API_KEY") is None:
            st.error("Please set your API key in the side-bar")
            return
        files = os.listdir(upload_directory)
        if len(files) == 0:
            st.sidebar.error("Please upload files")
            return
        if "index" not in st.session_state: # check if the index variable exists in the session state object
            index_files()
            st.sidebar.success("Index rebuild complete")
        if "index" in st.session_state: # check if the index variable exists in the session state object
            answer_question(question) 
        

if __name__ == "__main__":
    print("__name__ Called: ",iterator)
    main()


