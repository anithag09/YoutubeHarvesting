import googleapiclient.discovery
from googleapiclient.errors import HttpError
import pymysql
from datetime import datetime
from datetime import timedelta
import re
import streamlit as st
import pandas as pd

# YouTube API Key
api_key = "*********"

# Initialize YouTube API client
youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=api_key)

# Establish SQL connection
def connect_database():
    try:
        myconnection = pymysql.connect(host='127.0.0.1', user='root', passwd='*****', database='Youtube')
        return myconnection
    except Exception as e:
        st.error(f"An error occurred while connecting to the database: {e}")
        exit(1)

myconnection = connect_database()
cursor = myconnection.cursor()

# Get Channel Details
def get_channel_info(channel_id):
    try:
        channel_data = youtube.channels().list(
            id=channel_id,
            part='snippet,statistics,contentDetails'
        ).execute()

        channel_information = dict(
            channel_name=channel_data['items'][0]['snippet']['title'],
            channel_id=channel_data['items'][0]['id'],
            subscription_count=channel_data['items'][0]['statistics']['subscriberCount'],
            channel_views=channel_data['items'][0]['statistics']['viewCount'],
            channel_description=channel_data['items'][0]['snippet']['description'],
            playlist_id=channel_data['items'][0]['contentDetails']['relatedPlaylists']['uploads']
        )

        return channel_information
    except Exception as e:
        st.error(f"An error occurred while fetching channel information: {e}")
        return []

# Insert channel data into MySQL
def insert_channel_data(channel_info):
    try:
        # Create Channel table if not exists
        cursor.execute('''CREATE TABLE IF NOT EXISTS Channels (
            channel_name VARCHAR(250),
            channel_id VARCHAR(250) PRIMARY KEY,
            subscription_count INT,
            channel_views INT,
            channel_description TEXT,
            playlist_id VARCHAR(250),
            INDEX (channel_id)
        )''')

        # Insert channel details into the table
        query1 = '''
        INSERT INTO Channels (channel_id, channel_name, subscription_count, channel_views, channel_description, playlist_id)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
        channel_name = VALUES(channel_name),
        subscription_count = VALUES(subscription_count),
        channel_views = VALUES(channel_views),
        channel_description = VALUES(channel_description),
        playlist_id = VALUES(playlist_id)
        '''
        cursor.execute(query1, (
            channel_info['channel_id'],
            channel_info['channel_name'],
            channel_info['subscription_count'],
            channel_info['channel_views'],
            channel_info['channel_description'],
            channel_info['playlist_id']
        ))

        myconnection.commit()
        st.success(f"Channel {channel_info['channel_name']} data is inserted to SQL successfully")

    except Exception as e:
        st.error(f"An error occurred while inserting channel data: {e}")

# Get Video ids
def get_video_list(channel_id):
    try:
        video_ids = []
        next_page_token = None

        channel_data = youtube.channels().list(
            id=channel_id,
            part='snippet,statistics,contentDetails'
        ).execute()

        playlist_id = channel_data['items'][0]['contentDetails']['relatedPlaylists']['uploads']

        while True:
            video_data = youtube.playlistItems().list(
                playlistId=playlist_id,
                part='snippet,contentDetails',
                maxResults=50,
                pageToken=next_page_token
            ).execute()

            for i in range(len(video_data['items'])):
                video_ids.append(video_data['items'][i]['contentDetails']['videoId'])
            next_page_token = video_data.get('nextPageToken')

            if next_page_token is None:
                break

        return video_ids
    except Exception as e:
        st.error(f"An error occurred while fetching video list: {e}")
        return []

# Get video details
def get_video_info(video_ids):
    try:
        video_data = []
        for ids in video_ids:
            video_details = youtube.videos().list(
                id=ids,
                part='snippet,statistics,contentDetails'
            ).execute()

            for item in video_details['items']:
                details = dict(
                    channel_id=item['snippet']['channelId'],
                    video_name=item['snippet']['title'],
                    video_id=item['id'],
                    thumbnail=item['snippet']['thumbnails']['default']['url'],
                    published_at=item['snippet']['publishedAt'],
                    duration=item['contentDetails']['duration'],
                    caption_status=item['contentDetails'].get('caption', 'N/A'),
                    view_count=item['statistics'].get('viewCount', 0),
                    like_count=item['statistics'].get('likeCount', 0),
                    favorite_count=item['statistics'].get('favoriteCount', 0),
                    comment_count=item['statistics'].get('commentCount', 0)
                )
                video_data.append(details)
        return video_data
    except Exception as e:
        st.error(f"An error occurred while fetching video information: {e}")
        return []

# Convert YouTube date format to MySQL date format
def convert_datetime(youtube_datetime):
    return datetime.strptime(youtube_datetime, "%Y-%m-%dT%H:%M:%SZ").strftime("%Y-%m-%d %H:%M:%S")

# Convert YouTube time format to min and secs
def convert_duration(duration):
    pattern = re.compile(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?')
    match = pattern.match(duration)

    hours = int(match.group(1)) if match.group(1) else 0
    minutes = int(match.group(2)) if match.group(2) else 0
    seconds = int(match.group(3)) if match.group(3) else 0

    total_seconds = timedelta(hours=hours, minutes=minutes, seconds=seconds).total_seconds()
    readable_duration = f"{int(total_seconds // 60)} min {int(total_seconds % 60)} sec"
    
    return readable_duration

# Insert video data into MySQL
def insert_video_data(video_info_list):
    try:
        # Create Video table 
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS Videos (
            video_id VARCHAR(255) PRIMARY KEY,
            video_name VARCHAR(255),
            thumbnail TEXT,
            published_at DATETIME,
            duration VARCHAR(50),
            caption_status VARCHAR(50),
            view_count INT,
            like_count INT,
            favorite_count INT,
            comment_count INT,
            channel_id VARCHAR(255),
            FOREIGN KEY (channel_id) REFERENCES Channels(channel_id)
        )
        ''')

        # Insert video details into the table
        query2 = '''
        INSERT INTO Videos (video_id, video_name, thumbnail, published_at, duration, caption_status, view_count, like_count, favorite_count, comment_count, channel_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
        video_name = VALUES(video_name),
        thumbnail = VALUES(thumbnail),
        published_at = VALUES(published_at),
        duration = VALUES(duration),
        caption_status = VALUES(caption_status),
        view_count = VALUES(view_count),
        like_count = VALUES(like_count),
        favorite_count = VALUES(favorite_count),
        comment_count = VALUES(comment_count),
        channel_id = VALUES(channel_id)
        '''
        for video_info in video_info_list:
            cursor.execute(query2, (
                video_info['video_id'],
                video_info['video_name'],
                video_info['thumbnail'],
                convert_datetime(video_info['published_at']),
                convert_duration(video_info['duration']),
                video_info['caption_status'],
                video_info['view_count'],
                video_info.get('like_count', 0),
                video_info.get('favorite_count', 0),
                video_info.get('comment_count', 0),
                video_info['channel_id']
            ))

        myconnection.commit()
        st.success("Video data is inserted to SQL successfully")

    except Exception as e:
        st.error(f"An error occurred while inserting video data: {e}")

# Get video comments
def get_comment_info(video_ids):
    try:
        comment_info = []
        for ids in video_ids:
            try:
                video_comments = youtube.commentThreads().list(
                    videoId=ids,
                    part='snippet',
                    maxResults=20,
                    order='relevance',
                    textFormat='plainText'
                ).execute()

                for cmt in video_comments['items']:
                    comment = dict(
                        comment_id=cmt['id'],
                        video_id=cmt['snippet']['videoId'],
                        comment_author_name=cmt['snippet']['topLevelComment']['snippet']['authorDisplayName'],
                        comment_text=cmt['snippet']['topLevelComment']['snippet']['textOriginal'],
                        comment_published_date=cmt['snippet']['topLevelComment']['snippet']['publishedAt']
                    )
                    comment_info.append(comment)
            except HttpError as e:
                if e.resp.status == 403:
                    print(f"Comments are disabled for video ID: {ids}")
                else:
                    print(f"An error occurred: {e}")
        return comment_info
    except Exception as e:
        st.error(f"An error occurred while fetching comments: {e}")
        return []

# Insert comments data into MySQL
def insert_comments_data(comment_info_list):
    try:
        # Create Comments table if not exists
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS Comments (
            comment_id VARCHAR(255) PRIMARY KEY,
            video_id VARCHAR(255),
            comment_author_name VARCHAR(255),
            comment_text TEXT,
            comment_published_date DATETIME,
            FOREIGN KEY (video_id) REFERENCES Videos(video_id)
        )
        ''')

        # Insert comments details into the table
        query3 = '''
        INSERT INTO Comments (comment_id, video_id, comment_author_name, comment_text, comment_published_date)
        VALUES (%s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
        video_id = VALUES(video_id),
        comment_author_name = VALUES(comment_author_name),
        comment_text = VALUES(comment_text),
        comment_published_date = VALUES(comment_published_date)
        '''
        for comment_info in comment_info_list:
            cursor.execute('SELECT video_id FROM Videos WHERE video_id = %s', (comment_info['video_id'],))
            if cursor.fetchone():
                cursor.execute(query3, (
                    comment_info['comment_id'],
                    comment_info['video_id'],
                    comment_info['comment_author_name'],
                    comment_info['comment_text'],
                    convert_datetime(comment_info['comment_published_date'])
                ))

        myconnection.commit()
        st.success("Comments data is inserted to SQL successfully")

    except Exception as e:
        st.error(f"An error occurred while inserting comments data: {e}")

# Fetch existing channel IDs from the database
def get_existing_channel_ids():
    try:
        # Check if the table exists
        cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'Youtube' AND table_name = 'Channels'")
        if cursor.fetchone()[0] == 1:  
            cursor.execute("SELECT channel_id FROM Channels")
            result = cursor.fetchall()
            return [row[0] for row in result] 
        else:
            return []
    except Exception as e:
        st.error(f"An error occurred while fetching existing channel IDs: {e}")
        return []
    
# Function to get joined data from the database for a specific channel_id
def join_data(channel_id):
    try:
        query4 = '''
        SELECT
            Channels.channel_id,
            Channels.channel_name,
            Channels.subscription_count,
            Channels.channel_views,
            Channels.channel_description,
            Videos.video_id,
            Videos.video_name,
            Videos.thumbnail,
            Videos.published_at,
            Videos.duration,
            Videos.caption_status,
            Videos.view_count,
            Videos.like_count,
            Videos.favorite_count,
            Videos.comment_count,
            Comments.comment_id,
            Comments.comment_author_name,
            Comments.comment_text,
            Comments.comment_published_date
        FROM Channels
        LEFT JOIN Videos ON Channels.channel_id = Videos.channel_id
        LEFT JOIN Comments ON Videos.video_id = Comments.video_id
        WHERE Channels.channel_id = %s;
        '''
        cursor.execute(query4, channel_id)
        data = cursor.fetchall()
        return data
    except Exception as e:
        st.error(f"An error occurred while joining data: {e}")
        return []

# Streamlit code

tab1, tab2 = st.tabs(["Channel Information", "FAQ's"])

with st.sidebar:
    st.title(':green[Youtube Data Harvesting and Warehousing]')
    st.header(':blue[Tools Used]')
    st.caption(':grey[Python]')
    st.caption(':grey[MySQL]')
    st.caption(':grey[Streamlit]')

with tab1:
    # Create text field and button for channel id input
    channel_id = st.text_input("Enter Youtube channel id")
    def handle_upload():
        # Fetch channel information
        channel_info = get_channel_info(channel_id)
        if not channel_info:
            return

        # Insert data into MySQL
        insert_channel_data(channel_info)
        video_ids = get_video_list(channel_id)
        video_info_list = get_video_info(video_ids)
        insert_video_data(video_info_list)
        comment_info_list = get_comment_info(video_ids)
        insert_comments_data(comment_info_list)


    # Button to upload data to SQL
    if st.button(':violet[Upload to SQL]'):
        existing_channel_ids = get_existing_channel_ids()
        if not channel_id:
            st.warning("Please enter a YouTube channel ID")
        elif channel_id in existing_channel_ids:
            st.warning("Channel Information already exists in the database")
        else:
            handle_upload()
            st.success("Channel Information updated in the database")

    # Display joined data for the entered channel ID
    if st.button(':violet[View Channel Info]'):
        if channel_id:
            joined_data = join_data(channel_id)
            if joined_data:
                st.dataframe(pd.DataFrame(joined_data, columns=[
                    "channel_id", "channel_name", "subscription_count", "channel_views", "channel_description", 
                    "video_id", "video_name", "thumbnail", "published_at", 
                    "duration", "caption_status", "view_count", "like_count", "favorite_count", "comment_count",
                    "comment_id", "comment_author_name", "comment_text", "comment_published_date"
                ]))
            else:
                st.write("No data available for this channel.")
        else:
            st.warning("Please enter a YouTube channel ID")



with tab2:
    question = st.selectbox("Select your question", (
                                                "1. What are the names of all the videos and their corresponding channels?",
                                                "2. Which channels have the most number of videos, and how many videos do they have?",
                                                "3. What are the top 10 most viewed videos and their respective channels?",
                                                "4. How many comments were made on each video, and what are their corresponding video names?",
                                                "5. Which videos have the highest number of likes, and what are their corresponding channel names?",
                                                "6. What is the total number of likes for each video, and what are their corresponding video names?",
                                                "7. What is the total number of views for each channel, and what are their corresponding channel names?",
                                                "8. What are the names of all the channels that have published videos in the year 2022?",
                                                "9. What is the average duration of all videos in each channel, and what are their corresponding channel names?",
                                                "10. Which videos have the highest number of comments, and what are their corresponding channel names?"))

    if question == "1. What are the names of all the videos and their corresponding channels?":
        query1 = '''
                SELECT
                    Videos.video_name AS Name,
                    Channels.channel_name AS Channel
                FROM Videos
                INNER JOIN Channels ON Videos.channel_id = Channels.channel_id;
                '''
        cursor.execute(query1)
        ans1 = cursor.fetchall()
        st.dataframe(pd.DataFrame(ans1, columns=["Name", "Channel"]))

    elif question == "2. Which channels have the most number of videos, and how many videos do they have?":
        query2 = '''
                SELECT
                    Channels.channel_name AS Channel,
                    COUNT(Videos.video_id) AS Video_Count
                FROM Videos
                INNER JOIN Channels ON Videos.channel_id = Channels.channel_id
                GROUP BY Channels.channel_name
                ORDER BY Video_Count DESC;
                '''
        cursor.execute(query2)
        ans2 = cursor.fetchall()
        st.dataframe(pd.DataFrame(ans2, columns=["Channel", "Video_Count"]))

    elif question == "3. What are the top 10 most viewed videos and their respective channels?":
        query3 = '''
                SELECT
                    Channels.channel_name AS Channel,
                    Videos.video_name as Video,
                    Videos.view_count AS Views
                FROM Videos
                INNER JOIN Channels ON Videos.channel_id = Channels.channel_id
                ORDER BY Views DESC
                limit 10;
                '''
        cursor.execute(query3)
        ans3 = cursor.fetchall()
        st.dataframe(pd.DataFrame(ans3, columns=["Channel", "Video", "Views"]))

    elif question == "4. How many comments were made on each video, and what are their corresponding video names?":
        query4 = '''
                SELECT
                    Videos.video_name AS Name,
                    Comments.video_id as Video_id,
                    COUNT(Comments.comment_id) AS Count
                FROM Videos
                INNER JOIN Comments ON Videos.video_id = Comments.video_id
                GROUP BY Videos.video_id
                ORDER BY Count DESC;
                '''
        cursor.execute(query4)
        ans4 = cursor.fetchall()
        st.dataframe(pd.DataFrame(ans4, columns=["Name", "Video_id", "Count"]))        

    elif question == "5. Which videos have the highest number of likes, and what are their corresponding channel names?":
        query5 = '''
                SELECT
                    Channels.channel_name AS Channel,
                    Videos.video_name AS Video,
                    Videos.like_count AS Likes
                FROM Videos
                INNER JOIN Channels ON Videos.channel_id = Channels.channel_id
                ORDER BY Likes DESC
                LIMIT 5;
                '''
        cursor.execute(query5)
        ans5 = cursor.fetchall()
        st.dataframe(pd.DataFrame(ans5, columns=["Channel", "Video", "Likes"]))       

    elif question == "6. What is the total number of likes for each video, and what are their corresponding video names?":
        query6 = '''
                SELECT
                    Videos.video_name AS Video,
                    Videos.like_count AS Likes
                FROM Videos
                ORDER BY Likes DESC;
                '''
        cursor.execute(query6)
        ans6 = cursor.fetchall()
        st.dataframe(pd.DataFrame(ans6, columns=["Channel", "Like Count"]))            

    elif question == "7. What is the total number of views for each channel, and what are their corresponding channel names?":
        query7 = '''
                SELECT
                    Channels.channel_name AS Channel,
                    SUM(Videos.view_count) AS Views
                FROM Videos
                INNER JOIN Channels ON Videos.channel_id = Channels.channel_id
                GROUP BY Channel
                ORDER BY Views DESC;
                '''
        cursor.execute(query7)
        ans7 = cursor.fetchall()
        st.dataframe(pd.DataFrame(ans7, columns=["Channel", "Views"]))               

    elif question == "8. What are the names of all the channels that have published videos in the year 2022?":
        query8 = '''
                SELECT
                    Channels.channel_name AS Channel,
                    Videos.published_at AS Published_Date
                FROM Videos
                INNER JOIN Channels ON Videos.channel_id = Channels.channel_id
                WHERE EXTRACT(YEAR FROM published_at)="2022";
                '''
        cursor.execute(query8)
        ans8 = cursor.fetchall()
        st.dataframe(pd.DataFrame(ans8, columns=["Channel", "Published Date"]))        

    elif question == "9. What is the average duration of all videos in each channel, and what are their corresponding channel names?":
        query9 = '''
                SELECT
                    Channels.channel_name AS Channel,
                    Videos.duration AS Duration
                FROM Videos
                INNER JOIN Channels ON Videos.channel_id = Channels.channel_id;
                '''
        cursor.execute(query9)
        ans9 = cursor.fetchall()
        st.dataframe(pd.DataFrame(ans9, columns=["Channel", "Duration"]))       

    elif question == "10. Which videos have the highest number of comments, and what are their corresponding channel names?":
        query10 = '''
                SELECT
                    Channels.channel_name AS Channel,
                    Videos.comment_count as Comment_Count
                FROM Videos
                INNER JOIN Channels ON Videos.channel_id = Channels.channel_id
                ORDER BY Comment_Count DESC;
                '''
        cursor.execute(query10)
        ans10 = cursor.fetchall()
        st.dataframe(pd.DataFrame(ans10, columns=["Channel", "Comments Count"]))       

myconnection.close()
