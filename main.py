import logging
import os
import time
import zipfile
from datetime import datetime
from io import BytesIO
import threading
import concurrent.futures

import streamlit as st

from audio_separator import AudioSeparator
from s3_manager import S3Manager

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants for configuration
STEM_OPTIONS = {2: 'spleeter:2stems', 4: 'spleeter:4stems', 5: 'spleeter:5stems'}
BUCKET_NAME = 'stem-sep-app'
ZIP_FILE = 'separated_audio'

# Set page title and favicon
st.set_page_config(page_title='Audio Separator', page_icon=':musical_note:')


def save_uploaded_file(uploaded_file) -> str:
    s3_manager = S3Manager()
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    s3_file_name = f"{uploaded_file.name}_{timestamp}"

    # Upload the file directly to S3
    file_data = BytesIO(uploaded_file.getvalue())
    logger.info(f"Uploading {s3_file_name} to S3...")
    if s3_manager.upload_to_s3(file_data, s3_file_name, BUCKET_NAME):
        return s3_file_name
    else:
        raise Exception('Failed to upload file to S3')


def process_audio(stem_choice: int, s3_file_name: str):
    # Create an instance of AudioSeparator with the user's choice
    audio_separator = AudioSeparator(stem_count=stem_choice)
    # Perform the audio separation
    return audio_separator.separate(s3_file_name)


def create_zip_and_upload(s3_file_names: list):
    s3_manager = S3Manager()
    zip_buffer = BytesIO()

    with zipfile.ZipFile(zip_buffer, 'a', zipfile.ZIP_DEFLATED) as zip_file:
        for s3_file_name in s3_file_names:
            file_data = s3_manager.download_from_s3(s3_file_name, BUCKET_NAME)
            if file_data:
                zip_file.writestr(s3_file_name, file_data.read())

    zip_buffer.seek(0)
    zip_s3_file_name = f"{ZIP_FILE}_{datetime.now().strftime('%Y%m%d-%H%M%S')}.zip"
    s3_manager.upload_to_s3(zip_buffer, zip_s3_file_name, BUCKET_NAME)
    return zip_s3_file_name


def main():
    st.title('Audio Separator')
    st.markdown(
        """
        Welcome to the Audio Separator. Please follow the instructions below to separate your audio file 
        into stems.
        """
    )

    with st.sidebar:
        st.header('Instructions')
        st.write('1. Select the number of stems using the slider.')
        st.write('2. Upload your audio file (supports MP3 format).')
        st.write('3. Click "Process" to separate the audio.')
        st.write('4. Download the separated audio.')

        stem_choice = st.selectbox(
            'Select the number of stems',
            list(STEM_OPTIONS.keys())
        )

    uploaded_file = st.file_uploader('Upload your audio file', type=['mp3'])
    if uploaded_file is not None:
        if st.button('Preview Uploaded Audio'):
            st.audio(uploaded_file)

    if uploaded_file and st.button('Process Audio'):
        with st.spinner('Processing audio...'):
            s3_file_name = save_uploaded_file(uploaded_file)
            result = []

            def process():
                separated_files = process_audio(stem_choice, s3_file_name)
                result.append(separated_files)

            processing_thread = threading.Thread(target=process)
            processing_thread.start()
            processing_thread.join()

            separated_files = result[0]

            if isinstance(separated_files, str):
                st.error(separated_files)
            else:
                st.success('Processing complete!')

                # Provide audio previews for each separated stem
                st.spinner('Generating audio previews...')
                s3_manager = S3Manager()
                futures = {}
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    for s3_file_name in separated_files:
                        futures[executor.submit(s3_manager.download_from_s3, s3_file_name, BUCKET_NAME)] = s3_file_name

                for future in concurrent.futures.as_completed(futures):
                    file_data = future.result()
                    s3_file_name = futures[future]
                    if file_data:
                        stem_name = os.path.splitext(os.path.basename(s3_file_name))[0]  # Extract stem name from filename
                        stem_name = stem_name.split('.')[0].split('_')[0]  # Get the first part before underscore
                        st.subheader(f'{stem_name.capitalize()} Preview')  # Display stem name
                        st.audio(file_data)

                # Create a zip file
                with st.spinner('Creating zip file...'):
                    zip_s3_file_name = create_zip_and_upload(separated_files)
                    st.success('Zip file created successfully!')

                # Provide a download button for the zip file
                st.write('Preparing download...')
                time.sleep(1)  # Wait for a second to ensure the download link is generated
                st.markdown(
                    f"[Download Separated Audio](https://{BUCKET_NAME}.s3.amazonaws.com/{zip_s3_file_name})")


if __name__ == '__main__':
    main()
