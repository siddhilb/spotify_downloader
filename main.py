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
        
# def run_on_first_load():
#     st.cache_data.clear()
#     delete_contents()

# if 'first_run_complete' not in st.session_state:
#     run_on_first_load()
#     st.session_state['first_run_complete'] = True
        
# # def cleanup_files():
# #     now = time.time()
# #     for path_file_path in Path(download_dir).glob('*'):
# #         if os.stat(path_file_path).st_mtime < now - max_time:
# #             try:
# #                 os.remove(path_file_path)
# #             except OSError as error:
# #                 print(f"Error deleting old file {path_file_path}: {error}")

# # cleanup_files()

downloaded=False

list_of_files=[]


# if user_input:

downloaded=False

st.cache_data.clear()

@st.cache_data(show_spinner="Downloading song(s)...")

    
def download_music():
    delete_contents()
    Path(download_dir).mkdir(exist_ok=True)
    try:
        result = subprocess.run(
            ['spotdl', user_input, '--output', download_dir,'--bitrate', '192k'], 
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
    files = [
    str(p.resolve()) 
    for p in Path(download_dir).rglob('*.mp3')
    if p.is_file()
]
    st.space(8)
    if not files:
        files = [
                str(p.resolve())
                for p in Path(download_dir).rglob('*.MP3')
                if p.is_file()
            ]  
    if not files:
        raise RuntimeError('No audio found after running SpotDL.')
    else:
        st.success('Downloading complete!')
    return files
    #latest_file = max(list_of_files, key=os.path.getctime)
    #file_path = latest_file
    # return list_of_files
if user_input:
    try:
        # Capture both the list of files and the log
        list_of_files, spotdl_log = download_music()
        
        st.session_state['spotdl_debug_log'] = spotdl_log # Save log to session state
        
        st.space(8)
        st.success('Downloading complete! Files ready below.')
        
    except RuntimeError as error:
        # Catch the error from the function
        error_message = str(error)
        st.error(f"Download Error: {error_message.split('SpotDL log:')[0].strip()}")
        st.session_state['spotdl_debug_log'] = error_message # Save the full error log
        list_of_files = [] # Ensure files list is empty

# --- Display the Log for Debugging ---
if 'spotdl_debug_log' in st.session_state and st.session_state['spotdl_debug_log']:
    with st.expander("SpotDL Detailed Log (CLICK HERE TO DEBUG)", expanded=True):
        # Display the log content
        st.code(st.session_state['spotdl_debug_log'], language='log')
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
