# Audio Separator

This is an application that separates audio files into stems using the Spleeter library. It's built with Python and Streamlit.

![Screenshot of the application](Screenshot.png)

## Features

- Select the number of stems (2, 4, or 5)
- Upload your audio file (supports MP3 format)
- Separate the audio into stems
- Download the separated audio

## Installation

1. **Clone this repository**:

    ```bash
    git clone https://github.com/bantoinese83/Audio_Stem_Seperation.git
    cd Audio_Stem_Seperation
    ```

2. **Create a new virtual environment**:

    ```bash
    conda create -n audio_stem_sep python=3.8
    conda activate audio_stem_sep
    ```

3. **Install the required packages**:

    ```bash
    pip install -r requirements.txt
    ```

4. **Configure AWS S3**:

   Create a `.env` file in the root of your project and add the following configuration:

    ```plaintext
    # AWS
    AWS_ACCESS_KEY_ID=YOUR_AWS_ACCESS_KEY_ID
    AWS_SECRET_ACCESS_KEY=YOUR_AWS_SECRET_ACCESS_KEY
    AWS_REGION=us-east-1

    # S3
    STEM_SEP_S3_BUCKET=stem-sep-app
    ```

   Replace `YOUR_AWS_ACCESS_KEY_ID` and `YOUR_AWS_SECRET_ACCESS_KEY` with your actual AWS credentials.

5. **Run the Streamlit app**:

    ```bash
    streamlit run main.py
    ```
