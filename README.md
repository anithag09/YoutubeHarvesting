# YouTube Data Harvesting and Warehousing

This project is designed to extract data from YouTube using the YouTube Data API, store it in a MySQL database, and display it using Streamlit. The application supports various functionalities such as fetching channel information, video details, comments, and generating insights based on the data.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Usage](#usage)
- [Functionalities](#functionalities)
- [FAQ Queries](#faq-queries)
- [Code Overview](#code-overview)
- [Closing the Database Connection](#closing-the-database-connection)
- [Contact](#contact)

## Prerequisites
- Python 3.x
- MySQL Server
- Google API Key for YouTube Data API

## Installation
1. Clone the repository:
    ```bash
    git clone <repository_url>
    ```
2. Install the required Python packages:
    ```bash
    pip install -r requirements.txt
    ```
3. Set up MySQL and create a database named `Youtube`.
4. Replace the `api_key`, `host`, `user`, `passwd`, and `database` variables in the script with your own credentials.

## Usage
1. Run the Streamlit application:
    ```bash
    streamlit run app.py
    ```
2. Enter a YouTube channel ID in the provided text field and use the buttons to upload data to SQL or view channel info.

## Functionalities
### Channel Information
- Fetch and store channel information including channel name, ID, subscription count, view count, description, and playlist ID.

### Video Information
- Fetch and store video details including video ID, name, thumbnail, published date, duration, caption status, view count, like count, favorite count, and comment count.

### Comments Information
- Fetch and store comments on videos including comment ID, video ID, author name, comment text, and published date.

### FAQ Queries
- Generate insights based on the data such as:
  1. Names of all videos and their corresponding channels.
  2. Channels with the most number of videos.
  3. Top 10 most viewed videos.
  4. Number of comments on each video.
  5. Videos with the highest number of likes.
  6. Total number of likes for each video.
  7. Total number of views for each channel.
  8. Channels that published videos in the year 2022.
  9. Average duration of videos in each channel.
  10. Videos with the highest number of comments.

## Code Overview
### Database Connection
The `connect_database` function establishes a connection to the MySQL database.

### Fetching Data
- `get_channel_info`: Fetches details of a YouTube channel.
- `get_video_list`: Retrieves the list of video IDs for a channel.
- `get_video_info`: Fetches details of videos.
- `get_comment_info`: Fetches comments for videos.

### Inserting Data
- `insert_channel_data`: Inserts channel information into the `Channels` table.
- `insert_video_data`: Inserts video information into the `Videos` table.
- `insert_comments_data`: Inserts comments information into the `Comments` table.

### Utility Functions
- `convert_datetime`: Converts YouTube date format to MySQL date format.
- `convert_duration`: Converts YouTube duration format to a readable format.

### Fetch Existing Channel IDs
- `get_existing_channel_ids`: Fetches existing channel IDs from the database to prevent duplicate entries.

### Joining Data
- `join_data`: Joins data from `Channels`, `Videos`, and `Comments` tables for a specific channel ID.

### Streamlit Interface
- The application provides a user interface to input channel IDs, upload data to SQL, and view channel information.
- FAQ section to execute predefined queries and display results.

## Closing the Database Connection
Ensure to close the database connection after completing operations:
```python
myconnection.close()
