import streamlit as st
import requests
from datetime import datetime, timedelta
import os

# Retrieve API key from environment variable (replace "AIzaSyBrzgzfBoSm6vpamvNXqVh5wTbvae-CXqQ" if needed)
API_KEY = os.getenv("AIzaSyBrzgzfBoSm6vpamvNXqVh5wTbvae-CXqQ", "AIzaSyBrzgzfBoSm6vpamvNXqVh5wTbvae-CXqQ")

YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
YOUTUBE_VIDEO_URL = "https://www.googleapis.com/youtube/v3/videos"
YOUTUBE_CHANNEL_URL = "https://www.googleapis.com/youtube/v3/channels"

st.title("YouTube Viral Topics Tool")

# User inputs
days = st.number_input("Enter Days to Search (1-30):", min_value=1, max_value=30, value=5)
results_per_keyword = st.number_input("Results per Keyword:", min_value=1, max_value=10, value=5)

# Category selection
selected_categories = st.multiselect(
    "Select keyword categories:",
    options=["Relationship/Infidelity", "Stoicism"],
    default=["Relationship/Infidelity"]
)

# Predefined lists of keywords
relationship_keywords = [
    "Affair Relationship Stories", "Reddit Update", "Reddit Relationship Advice", "Reddit Relationship", 
    "Reddit Cheating", "AITA Update", "Open Marriage", "Open Relationship", "X BF Caught", 
    "Stories Cheat", "X GF Reddit", "AskReddit Surviving Infidelity", "GurlCan Reddit", 
    "Cheating Story Actually Happened", "Cheating Story Real", "True Cheating Story", 
    "Reddit Cheating Story", "R/Surviving Infidelity", "Surviving Infidelity", 
    "Reddit Marriage", "Wife Cheated I Can't Forgive", "Reddit AP", "Exposed Wife", 
    "Cheat Exposed"
]

stoicism_keywords = [
    "Stoicism", "Stoic Philosophy", "Marcus Aurelius", "Seneca", "Epictetus",
    "Meditations", "Stoic Wisdom", "Stoic Mindset", "Ancient Stoicism", "Modern Stoicism"
]

# Combine keywords based on selected categories
keywords = []
if "Relationship/Infidelity" in selected_categories:
    keywords.extend(relationship_keywords)
if "Stoicism" in selected_categories:
    keywords.extend(stoicism_keywords)

if st.button("Fetch Data"):
    try:
        # Calculate the publishedAfter date parameter based on user input
        start_date = (datetime.utcnow() - timedelta(days=int(days))).isoformat("T") + "Z"
        all_results = []

        for keyword in keywords:
            st.write(f"Searching for keyword: **{keyword}**")
            search_params = {
                "part": "snippet",
                "q": keyword,
                "type": "video",
                "order": "viewCount",
                "publishedAfter": start_date,
                "maxResults": results_per_keyword,
                "key": API_KEY,
            }
            response = requests.get(YOUTUBE_SEARCH_URL, params=search_params)
            search_data = response.json()

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

            # Fetch video statistics
            stats_params = {
                "part": "statistics",
                "id": ",".join(video_ids),
                "key": API_KEY,
            }
            stats_response = requests.get(YOUTUBE_VIDEO_URL, params=stats_params)
            stats_data = stats_response.json()

            if "items" not in stats_data or not stats_data["items"]:
                st.warning(f"Failed to fetch video statistics for keyword: {keyword}")
                continue

            # Fetch channel statistics
            channel_params = {
                "part": "statistics",
                "id": ",".join(channel_ids),
                "key": API_KEY,
            }
            channel_response = requests.get(YOUTUBE_CHANNEL_URL, params=channel_params)
            channel_data = channel_response.json()

            if "items" not in channel_data or not channel_data["items"]:
                st.warning(f"Failed to fetch channel statistics for keyword: {keyword}")
                continue

            # Map IDs to statistics
            video_stats = {item.get("id"): item.get("statistics", {}) for item in stats_data["items"]}
            channel_stats = {item.get("id"): item.get("statistics", {}) for item in channel_data["items"]}

            # Combine video and channel data
            for vid, info in video_info_map.items():
                stats = video_stats.get(vid, {})
                channel_id = info.get("ChannelID")
                channel_stat = channel_stats.get(channel_id, {})

                views = int(stats.get("viewCount", 0))
                subs = int(channel_stat.get("subscriberCount", 0))

                # Apply filter only for Relationship/Infidelity keywords:
                # For stoicism keywords you might not need this filter. Adjust as necessary.
                if "Relationship/Infidelity" in selected_categories and subs >= 3000:
                    continue

                combined_result = {
                    "Title": info["Title"],
                    "Description": info["Description"],
                    "URL": info["URL"],
                    "Views": views,
                    "Subscribers": subs
                }
                all_results.append(combined_result)

        if all_results:
            st.success(f"Found {len(all_results)} results across selected keywords!")
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
            st.warning("No results found based on the selected criteria.")

    except Exception as e:
        st.error(f"An error occurred: {e}")
