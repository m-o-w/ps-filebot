import os
from llama_index import GPTVectorStoreIndex, SimpleDirectoryReader
import streamlit as st
from config import upload_directory, container_connection_string, inbound_container, index_container, archive_container
import random
from azure.storage.blob import BlobServiceClient
from llama_index import StorageContext, load_index_from_storage
import openai


# Load index from session if found
global_index = None
iterator = random.randint(1, 99)
print("Iterator: ",iterator)
if os.environ.get("OPENAI_API_KEY") is not None:
    openai.api_key = os.environ.get("OPENAI_API_KEY")
    

def copy_index_to_blob(index_container, container_connection_string):
    print("copy_index_to_blob Called: ",iterator)
    blob_service_client = BlobServiceClient.from_connection_string(container_connection_string)
    # Get the source and destination container client
    target_container_client = blob_service_client.get_container_client(index_container)
    # Define the connection string and blob names
    folder_path = index_container
    for file_name in os.listdir(folder_path):
        print(file_name)
        blob_client = target_container_client.get_blob_client(index_container+"/"+file_name)
        with open(os.path.join(folder_path, file_name), "rb") as data:
            blob_client.upload_blob(data, overwrite=True)
            print("Uploaded to Azure Blob storage as blob:\n\t" + file_name)
    
def archive_inbound_files():
    print("archive_inbound_files Called: ",iterator)
    # list all files in local inbound folder
    inbound_files = os.listdir(inbound_container)
    print(f"###############  Inbound files: {inbound_files}")
    # archive each file
    for filename in inbound_files:
        archive_blob(filename, container_connection_string, inbound_container, archive_container)
        
     
def archive_blob(filename, container_connection_string, source_container, archive_container):
    # Define the connection string and blob names
    print("archive_blob Called: ",iterator)
    blob_connection_string = container_connection_string
    source_container_name = source_container
    destination_container_name = archive_container
    
    print(f"###############  Archiving blob: {filename}")
    print(f"###############  Connection string: {blob_connection_string}")
    print(f"###############  Source container: {source_container_name}")
    print(f"###############  Destination container: {destination_container_name}")
    
    # Move blob to archive container and delete source blob
    blob_service_client = BlobServiceClient.from_connection_string(blob_connection_string)
    # Get the source and destination container client
    source_container_client = blob_service_client.get_container_client(source_container_name)
    destination_container_client = blob_service_client.get_container_client(destination_container_name)
    # Get the source blob client
    source_blob_client = source_container_client.get_blob_client(filename)
    destination_blob_client = destination_container_client.get_blob_client(filename)
    destination_blob_client.start_copy_from_url(source_blob_client.url)
    # Delete the source blob
    source_blob_client.delete_blob()

# Get all filers from blob storage 'inbound' container
def get_files_from_blob_storage():
    print("get_files_from_blob_storage Called: ",iterator)
    blob_service_client = BlobServiceClient.from_connection_string(container_connection_string)
    container_client = blob_service_client.get_container_client(inbound_container)
    blob_list = container_client.list_blobs()
    for blob in blob_list:
        # Get a blob client for each blob
        blob_client = container_client.get_blob_client(blob.name)
        # Download each blob to local folder
        with open(os.path.join(inbound_container, blob.name), "wb") as file:
        #with open(blob.name, "wb") as file:
            file.write(blob_client.download_blob().readall())


def merge_file_with_index(index, inbound_dir_name):
    print("merge_file_with_index Called: ",iterator)
    loader = SimpleDirectoryReader(inbound_dir_name, recursive=True, exclude_hidden=True)
    new_documents = loader.load_data()
    for docs in new_documents:
        index.update_ref_doc(docs)
    print(f"Documents count loaded: {len(new_documents)}")
    print(f"###############  Index updated. Docs count in index: {index.docstore.docs}")
    return index

# Create method to load index from blob storage
def load_index():
    print("load_index Called: ",iterator)
    if os.environ.get("OPENAI_API_KEY") is None:
        st.error("Please set your API key in the side-bar")
        return
    delete_files_in_directory(index_container)
    blob_service_client = BlobServiceClient.from_connection_string(container_connection_string)
    container_client = blob_service_client.get_container_client(index_container)
    blob_list = container_client.list_blobs(prefix=index_container+"\\")
    for blob in blob_list:
        print("Getting: ",blob.name)
        # Get a blob client for each blob
        blob_client = container_client.get_blob_client(blob.name)
        # Download each blob to local folder
        #with open(os.path.join(local_folder, blob.name), "wb") as file:
        with open(blob.name, "wb") as file:
            file.write(blob_client.download_blob().readall())      
    
    storage_context = StorageContext.from_defaults(persist_dir="index")
    index = load_index_from_storage(storage_context)
    
    get_files_from_blob_storage()
    index = merge_file_with_index(index, inbound_container)
    index.storage_context.persist(persist_dir=index_container)
    copy_index_to_blob(index_container, container_connection_string)
    archive_inbound_files()
    delete_files_in_directory(inbound_container)
    
    st.session_state.index = index
    st.sidebar.success(f"Document Count: {len(index.docstore.docs)}")
    print("load_index from blob: ",iterator)

if "index" in st.session_state: # check if the index variable exists in the session state object
    global_index = st.session_state.index # create a query engine from the index
    
if not os.path.exists(upload_directory):
    os.makedirs(upload_directory)
    
if not os.path.exists(inbound_container):
    os.makedirs(inbound_container)

if not os.path.exists(index_container):
    os.makedirs(index_container)

def delete_files_in_directory(directory):
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        if os.path.isfile(file_path):
            os.remove(file_path)
            print(f"Deleted file: {file_path}")
    
# ------------------------------------Code for setting API Key-------------------------------------
def load_api_key(user_api_key):
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
        load_api_key(user_api_key)
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
    openai.api_key = os.environ.get("OPENAI_API_KEY")
    print("answer_question Called: ",iterator)
    query_engine=global_index.as_query_engine(openai_api_key=os.environ["OPENAI_API_KEY"])
    response = query_engine.query(question+"?")
    st.info(question)
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
    st.set_page_config(page_title="PS File Hunter")
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
