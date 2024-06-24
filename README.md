# Summarize.py

**Summarize.py** is a Python script designed to extract and summarize content from YouTube subtitles, making it easier to create engaging YouTube Shorts.

## Features

- **Subtitles Data Preparation**: Splits and processes subtitle data for further analysis.
- **YouTube Shorts Clipping**: Selects approximately one minute of continuous, narrative-rich content from longer videos for YouTube Shorts.

## Getting Started

### Prerequisites

Make sure all the necessary Python packages are installed. Refer to the `requirements.txt` file for the list of required packages.

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/MichaelChenGithub/ContentClippingTool-for-YT-shorts.git
   cd ContentClippingTool-for-YT-shorts
   ```
2. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

### Usage

Run the `summarize.py` script:
```bash
python summarize.py
```

### Adjustable Parameters

- **summarizing_system_prompt**: Adjust this parameter based on your summarization needs. Examples include:
  - "Extract 2 minutes of video."
  - "Extract 3 segments of one-minute videos."

- **split_for_yt_clipping Parameters**:
  - **max_length**: Set this according to the maximum number of tokens that the large language model can handle.
  - **overlap**: Indicates the number of overlapping sentences when splitting long articles. Increasing this value ensures better content extraction for YouTube Shorts but will also increase the number of API calls to the language model and the script's execution time.
