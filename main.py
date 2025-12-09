import streamlit as st
import os
import glob
from pathlib import Path
import zipfile
import sys
from io import BytesIO
import shutil
import subprocess
user_input = st.text_input('Copy & paste a spotify link into here to download and play it.',key='enter')
user_input = user_input.split('?',1)[0]
web_page_open = True
# print(song)

download_dir = 'temp_downloads'
Path(download_dir).mkdir(exist_ok=True)



max_time = 3*60

def delete_contents():
    try:
        shutil.rmtree(download_dir)
        Path(download_dir).mkdir(exist_ok=True)
        
    except OSError as error:
        st.warning(f'Could not delete directory {download_dir}: {error}')
        
def run_on_first_load():
    st.cache_data.clear()
    delete_contents()


# 2. Check the session state for a flag
if 'first_run_complete' not in st.session_state:
    run_on_first_load()
    st.session_state['first_run_complete'] = True
        
# def cleanup_files():
#     now = time.time()
#     for path_file_path in Path(download_dir).glob('*'):
#         if os.stat(path_file_path).st_mtime < now - max_time:
#             try:
#                 os.remove(path_file_path)
#             except OSError as error:
#                 print(f"Error deleting old file {path_file_path}: {error}")

# cleanup_files()

downloaded=False

list_of_files=[]


# if user_input:

downloaded=False


@st.cache_data(show_spinner="Downloading song(s)...")

    
def download_music():
    Path(download_dir).mkdir(exist_ok=True)
    try:
        result = subprocess.run(
            ['spotdl', user_input, '--output', download_dir], 
            capture_output=True, # Capture stdout and stderr
            text=True,
            check=True # Raise an exception if the command fails
        )
        # result.stdout and result.stderr will contain spotdl's messages
    except subprocess.CalledProcessError as e:
        # Raise a clearer exception with the error output
        raise RuntimeError(f"SpotDL failed. Error: {e.stderr} Output: {e.stdout}")
    # st.info('Downloading song(s)..')
    # os.system(f'spotdl {user_input} --output {download_dir}')
    search_pattern = os.path.join(download_dir, '*mp3')
    files = glob.glob(search_pattern)
    st.space(8)
    st.success('Downloading complete!')
    # if not files:
    #     raise RuntimeError('No audio found after running SpotDL.')
    # return files
    # latest_file = max(list_of_files, key=os.path.getctime)
    # file_path = latest_file
    # return list_of_files
if user_input:
    try:
        list_of_files=download_music()
    except RuntimeError as error:
        st.error(str(error))
        # if 'enter' in st.session_state:
        #     st.session_state['enter']=''
        
if list_of_files:
    if not list_of_files:
            st.error('No audio files found. Check the console for specific errors.')
    else:
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer,'w',zipfile.ZIP_DEFLATED, False) as zip_file:
            for file_path in list_of_files:
                zip_file.write(file_path,Path(file_path).name)
        zip_buffer.seek(0)
        zip_file_name = f"spotify_downloads_{Path(list_of_files[0]).stem}.zip"
        
        # zip_data = zip_buffer.read()
        
        st.space(8)
        
        st.download_button(
            label='Download whole playlist (zip)',
            data=zip_buffer.read(),
            file_name=zip_file_name,
            mime='application/zip',
            key='download_all_zip',

        )
        st.subheader("Downloaded tracks:")
        
        for file_path in list_of_files:
            file_name=Path(file_path).name
            
            unique_key_download = f"download_{file_name}"
            # unique_key_audio = 
        

            with st.container(border=True):
                st.write(f"**Track**: {file_name}")

                try:
                    with open(file_path,'rb') as f:
                        audio_bytes = f.read()
                except FileNotFoundError:
                    st.error('Audio file not found.')
                    st.stop()

                st.download_button(
                    label='Download MP3',
                    data=audio_bytes,
                    file_name = file_name,
                    mime = 'audio/mp3',
                    # args=(file_path,)
                    )
                st.audio(data=audio_bytes, format='audio/mp3')
