import logging
import os
from datetime import datetime
from io import BytesIO

from spleeter.separator import Separator
from s3_manager import S3Manager

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants for configuration
STEM_OPTIONS = {2: 'spleeter:2stems', 4: 'spleeter:4stems', 5: 'spleeter:5stems'}
BUCKET_NAME = 'stem-sep-app'


class AudioSeparator:
    def __init__(self, stem_count: int):
        if stem_count not in STEM_OPTIONS:
            raise ValueError(f'Invalid stem count. Please choose from {list(STEM_OPTIONS.keys())}')
        self.model_configuration = STEM_OPTIONS[stem_count]
        self.separator = Separator(self.model_configuration)
        self.s3_manager = S3Manager()

    def separate(self, s3_file_name: str):
        try:
            # Download the audio file from S3
            audio_file = self.s3_manager.download_from_s3(s3_file_name, BUCKET_NAME)
            if not audio_file:
                raise Exception('Failed to download the audio file from S3.')

            # Save the audio file to a temporary location
            temp_audio_file_path = f"/tmp/{s3_file_name}"
            with open(temp_audio_file_path, 'wb') as temp_file:
                temp_file.write(audio_file.getbuffer())

            # Perform separation
            output_dir = '/tmp/output'
            self.separator.separate_to_file(temp_audio_file_path, output_dir)

            # Collect separated files
            audio_data = {}
            for root, _, files in os.walk(output_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    with open(file_path, 'rb') as f:
                        file_data = BytesIO(f.read())
                        audio_data[file] = file_data

            # Upload separated audio files to S3
            s3_file_names = []
            for file_name, file_data in audio_data.items():
                s3_separated_file_name = f"{file_name}_{datetime.now().strftime('%Y%m%d-%H%M%S')}.mp3"
                self.s3_manager.upload_to_s3(file_data, s3_separated_file_name, BUCKET_NAME)
                s3_file_names.append(s3_separated_file_name)

            return s3_file_names
        except Exception as e:
            logger.error(f'An error occurred during separation: {e}')
            return 'An error occurred during the separation process.'
