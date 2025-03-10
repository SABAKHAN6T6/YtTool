import streamlit as st
import requests
from datetime import datetime, timedelta
import os

# Retrieve API key from environment variable (replace "YOUR_API_KEY_HERE" if needed)
API_KEY = os.getenv("AIzaSyBrzgzfBoSm6vpamvNXqVh5wTbvae-CXqQ", "AIzaSyBrzgzfBoSm6vpamvNXqVh5wTbvae-CXqQ")

YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
YOUTUBE_VIDEO_URL = "https://www.googleapis.com/youtube/v3/videos"
YOUTUBE_CHANNEL_URL = "https://www.googleapis.com/youtube/v3/channels"

st.title("YouTube Viral Topics Tool")

# User inputs
days = st.number_input("Enter Days to Search (1-30):", min_value=1, max_value=30, value=5)
results_per_keyword = st.number_input("Results per Keyword:", min_value=1, max_value=10, value=5)

# Predefined list of keywords
keywords = [
    "Affair Relationship Stories", "Reddit Update", "Reddit Relationship Advice", "Reddit Relationship", 
    "Reddit Cheating", "AITA Update", "Open Marriage", "Open Relationship", "X BF Caught", 
    "Stories Cheat", "X GF Reddit", "AskReddit Surviving Infidelity", "GurlCan Reddit", 
    "Cheating Story Actually Happened", "Cheating Story Real", "True Cheating Story", 
    "Reddit Cheating Story", "R/Surviving Infidelity", "Surviving Infidelity", 
    "Reddit Marriage", "Wife Cheated I Can't Forgive", "Reddit AP", "Exposed Wife", 
    "Cheat Exposed"
]

# Caching API responses to improve performance
@st.cache_data(show_spinner=False)
def fetch_data_for_keyword(keyword, published_after, max_results):
    search_params = {
        "part": "snippet",
        "q": keyword,
        "type": "video",
        "order": "viewCount",
        "publishedAfter": published_after,
        "maxResults": max_results,
        "key": API_KEY,
    }
    response = requests.get(YOUTUBE_SEARCH_URL, params=search_params)
    return response.json()

@st.cache_data(show_spinner=False)
def fetch_video_stats(video_ids):
    stats_params = {
        "part": "statistics",
        "id": ",".join(video_ids),
        "key": API_KEY,
    }
    response = requests.get(YOUTUBE_VIDEO_URL, params=stats_params)
    return response.json()

@st.cache_data(show_spinner=False)
def fetch_channel_stats(channel_ids):
    channel_params = {
        "part": "statistics",
        "id": ",".join(channel_ids),
        "key": API_KEY,
    }
    response = requests.get(YOUTUBE_CHANNEL_URL, params=channel_params)
    return response.json()

if st.button("Fetch Data"):
    try:
        # Calculate the publishedAfter date parameter based on user input
        start_date = (datetime.utcnow() - timedelta(days=int(days))).isoformat("T") + "Z"
        all_results = []

        for keyword in keywords:
            st.write(f"Searching for keyword: **{keyword}**")
            search_data = fetch_data_for_keyword(keyword, start_date, results_per_keyword)

            if "items" not in search_data or not search_data["items"]:
                st.warning(f"No videos found for keyword: {keyword}")
                continue

            videos = search_data["items"]
            video_ids = []
            channel_ids = []
            video_info_map = {}  # Maps video IDs to basic info

            for video in videos:
                video_id = video.get("id", {}).get("videoId")
                channel_id = video.get("snippet", {}).get("channelId")
                if video_id and channel_id:
                    video_ids.append(video_id)
                    channel_ids.append(channel_id)
                    video_info_map[video_id] = {
                        "Title": video["snippet"].get("title", "N/A"),
                        "Description": video["snippet"].get("description", "")[:200],
                        "URL": f"https://www.youtube.com/watch?v={video_id}",
                        "ChannelID": channel_id
                    }

            if not video_ids or not channel_ids:
                st.warning(f"Skipping keyword: {keyword} due to missing video or channel data.")
                continue

            stats_data = fetch_video_stats(video_ids)
            if "items" not in stats_data or not stats_data["items"]:
                st.warning(f"Failed to fetch video statistics for keyword: {keyword}")
                continue

            channel_data = fetch_channel_stats(channel_ids)
            if "items" not in channel_data or not channel_data["items"]:
                st.warning(f"Failed to fetch channel statistics for keyword: {keyword}")
                continue

            # Create dictionaries mapping IDs to statistics
            video_stats = {item.get("id"): item.get("statistics", {}) for item in stats_data["items"]}
            channel_stats = {item.get("id"): item.get("statistics", {}) for item in channel_data["items"]}

            # Combine video and channel data
            for vid, info in video_info_map.items():
                stats = video_stats.get(vid, {})
                channel_id = info.get("ChannelID")
                channel_stat = channel_stats.get(channel_id, {})

                views = int(stats.get("viewCount", 0))
                subs = int(channel_stat.get("subscriberCount", 0))

                # Filter channels with fewer than 3,000 subscribers
                if subs < 3000:
                    combined_result = {
                        "Title": info["Title"],
                        "Description": info["Description"],
                        "URL": info["URL"],
                        "Views": views,
                        "Subscribers": subs
                    }
                    all_results.append(combined_result)

        if all_results:
            st.success(f"Found {len(all_results)} results across all keywords!")
            for result in all_results:
                st.markdown(
                    f"**Title:** {result['Title']}  \n"
                    f"**Description:** {result['Description']}  \n"
                    f"**URL:** [Watch Video]({result['URL']})  \n"
                    f"**Views:** {result['Views']}  \n"
                    f"**Subscribers:** {result['Subscribers']}"
                )
                st.write("---")
        else:
            st.warning("No results found for channels with fewer than 3,000 subscribers.")

    except Exception as e:
        st.error(f"An error occurred: {e}")
