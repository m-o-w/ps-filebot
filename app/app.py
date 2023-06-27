import os
from llama_index import GPTVectorStoreIndex, SimpleDirectoryReader
import streamlit as st
from config import upload_directory, container_connection_string, inbound_container, index_container
import random
from azure.storage.blob import BlobServiceClient
from llama_index import StorageContext, load_index_from_storage
import openai


# Load index from session if found
global_index = None
iterator = random.randint(1, 99)
print("Iterator: ",iterator)

# Create method to load index from blob storage
def load_index():
    print("load_index Called: ",iterator)
    delete_files_in_directory(index_container)
    blob_service_client = BlobServiceClient.from_connection_string(container_connection_string)
    container_client = blob_service_client.get_container_client(index_container)
    blob_list = container_client.list_blobs(prefix=index_container+"\\")
    for blob in blob_list:
        # Get a blob client for each blob
        blob_client = container_client.get_blob_client(blob.name)
        # Download each blob to local folder
        #with open(os.path.join(local_folder, blob.name), "wb") as file:
        with open(blob.name, "wb") as file:
            file.write(blob_client.download_blob().readall())
    
    storage_context = StorageContext.from_defaults(persist_dir="index")
    index = load_index_from_storage(storage_context)
    st.session_state.index = index
    st.sidebar.success(f"Document Count: {len(index.docstore.docs)}")
    print("load_index from blob: ",iterator)

if "index" in st.session_state: # check if the index variable exists in the session state object
    global_index = st.session_state.index # create a query engine from the index
    
if not os.path.exists(upload_directory):
    os.makedirs(upload_directory)

if not os.path.exists("index"):
    os.makedirs("index")

def delete_files_in_directory(directory):
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        if os.path.isfile(file_path):
            os.remove(file_path)
            print(f"Deleted file: {file_path}")
    
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
    reload_button = st.sidebar.button("Delete Key")
    if reload_button:
        os.environ.pop("OPENAI_API_KEY")
        st.experimental_rerun()
        

# FileManagement Save file
def save_uploaded_file(uploaded_file):
    blob_service_client = BlobServiceClient.from_connection_string(container_connection_string)
    blob_client = blob_service_client.get_blob_client(container=inbound_container, blob=uploaded_file.name)
    blob_client.upload_blob(uploaded_file)
    return
    
# FileManagement Delete file
def delete_file(file_path):
    print("delete_file Called: ",iterator)
    if os.path.exists(file_path):
        os.remove(file_path)
        if "index" in st.session_state:
            st.session_state.pop('index')
        st.experimental_rerun()
    else:
        st.sidebar.error("File not found")

# Rebuild vector index        
def rebuild_index(from_directory):
    print("rebuild_index Called: ",iterator)
    global global_index
    document = SimpleDirectoryReader(from_directory).load_data()
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
    query_engine=global_index.as_query_engine(openai_api_key=os.environ["OPENAI_API_KEY"])
    response = query_engine.query(question+"?")
    st.info(response)

# File upload section
uploaded_file = st.sidebar.file_uploader("Upload files to Blob")
print("uploaded_file: ",uploaded_file)
if uploaded_file:
    save_uploaded_file(uploaded_file)
    del uploaded_file

# Create reload button on sidebar
reload_button = st.sidebar.button("Reload Index")
if reload_button:
    load_index()
        
def main():
    print("main Called: ",iterator)
            
    #Start StreamLit
    st.title("PS File AI Bot (V13)")
    form = st.form("Input box", clear_on_submit=True)
    question = form.text_input("Send message", placeholder="Your question here")
    submit_button = form.form_submit_button("Send")
    
    # Someone have asked a question
    if question:
        print("question Called: ",iterator)
        if os.environ.get("OPENAI_API_KEY") is None:
            st.error("Please set your API key in the side-bar")
            return
        else:
            openai.api_key = os.environ.get("OPENAI_API_KEY")
        
        if "index" not in st.session_state: # check if the index variable exists in the session state object
            st.sidebar.success("Loading Index")
            load_index()
        if "index" not in st.session_state: # check if the index variable exists in the session state object
            st.sidebar.error("Index not found")
            return
        if "index" in st.session_state: # check if the index variable exists in the session state object
            answer_question(question) 
        
if __name__ == "__main__":
    print("__name__ Called: ",iterator)
    main()
