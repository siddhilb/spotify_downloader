import streamlit as st
import os
import glob
from pathlib import Path
import zipfile
from io import BytesIO
import shutil
import subprocess

# --- Configuration & Utility Functions ---

download_dir = 'temp_downloads'

def delete_contents():
    """Deletes and recreates the temp_downloads folder."""
    try:
        # Use shutil.rmtree for a directory and its contents
        shutil.rmtree(download_dir)
    except Exception:
        # Ignore errors if the directory doesn't exist yet
        pass
    Path(download_dir).mkdir(exist_ok=True)

# --- Core Download Function (Cached and Robust) ---

@st.cache_data(show_spinner="Running SpotDL and downloading...")
def download_music():
    # 1. Clean the directory before downloading
    delete_contents()
    
    # Initialize log
    spotdl_log = ""

    try:
        # Use subprocess to execute the command and capture all output
        # check=False ensures we capture the log even on non-zero exit code
        result = subprocess.run(
            ['spotdl', st.session_state['enter'], '--output', download_dir, '--bitrate', '128k'], 
            capture_output=True,
            text=True,
            check=False 
        )
        
        # Capture the full output log
        spotdl_log += f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}\nExit Code: {result.returncode}"
        
        # Raise the error explicitly if the exit code is not 0
        if result.returncode != 0:
            raise RuntimeError(f"SpotDL failed with exit code {result.returncode}.")
            
    except Exception as e:
        # Catch errors like FileNotFoundError for spotdl executable
        raise RuntimeError(f"Failed to execute SpotDL command: {e}")
    
    # 2. Robust file search (Path.rglob is best practice)
    download_path = Path(download_dir)    
    files = [
        str(p.resolve()) 
        for p in download_path.rglob('*.mp3')
        if p.is_file()
    ]
    
    # 3. Final check for files
    if not files:
        # If no files found, raise the error and include the full log
        raise RuntimeError(f"No audio files were found after SpotDL completed. Final Log:\n{spotdl_log}")
        
    return files, spotdl_log # Return both the files and the log string

# --- UI and Session Initialization ---

user_input = st.text_input('Copy & paste a spotify link into here to download and play it.',key='enter')
user_input = user_input.split('?',1)[0]
# Clear cache on every rerun to force the first download attempt
st.cache_data.clear() 

# --- Main Script Flow ---

list_of_files = [] 

if user_input:
    try:
        # Capture both the list of files and the log
        list_of_files, spotdl_log = download_music()
        
        st.session_state['spotdl_debug_log'] = spotdl_log # Save log to session state
        
        # Display success message outside the cached function
        st.space(1)
        st.success('Downloading complete! Files ready below.')
        
    except RuntimeError as error:
        # Catch the error, display the brief message, and save the full log
        error_message = str(error)
        
        # Extract the user-friendly error message part
        if "Final Log:" in error_message:
            st.error(f"Download Error: {error_message.split('Final Log:')[0].strip()}")
            st.session_state['spotdl_debug_log'] = error_message.split("Final Log:")[1]
        else:
            st.error(f"Download Error: {error_message}")
            st.session_state['spotdl_debug_log'] = error_message
            
        list_of_files = [] 

# --- Display Debug Log ---
if 'spotdl_debug_log' in st.session_state:
    with st.expander("SpotDL Detailed Log (CLICK HERE TO DEBUG)", expanded=True):
        st.code(st.session_state['spotdl_debug_log'], language='log')

# --- Display Downloads and Audio Players ---

if list_of_files:
    
    # --- ZIP File Creation ---
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer,'w',zipfile.ZIP_DEFLATED, False) as zip_file:
        for file_path_str in list_of_files:
            # Use Path to get the base filename for the zip entry
            zip_file.write(file_path_str, Path(file_path_str).name) 
    zip_buffer.seek(0)
    zip_file_name = f"spotify_downloads_{Path(list_of_files[0]).stem}.zip"
    
    st.space(1)
    
    st.download_button(
        label='Download whole playlist (zip)',
        data=zip_buffer.read(),
        file_name=zip_file_name,
        mime='application/zip',
        key='download_all_zip',
    )
    
    st.subheader("Downloaded tracks:")
    
    # --- Individual Track Display ---
    for file_path_str in list_of_files:
        # CRUCIAL: Convert to Path object and resolve for reliable reading
        file_path = Path(file_path_str)
        file_name = file_path.name

        with st.container(border=True):
            st.write(f"**Track**: {file_name}")

            try:
                # Use the resolved path for opening the file
                with open(file_path.resolve(),'rb') as f: 
                    audio_bytes = f.read()
            except FileNotFoundError:
                st.error(f'Audio file not found or permission denied for {file_name}.')
                continue 
            except Exception as e:
                st.error(f"An unexpected error occurred while reading {file_name}: {e}")
                continue

            col1, col2 = st.columns([1, 4])
            
            with col1:
                st.download_button(
                    label='Download MP3',
                    data=audio_bytes,
                    file_name = file_name,
                    mime = 'audio/mp3',
                    key=f'download_{file_name}',
                )
            with col2:
                st.audio(data=audio_bytes, format='audio/mp3')