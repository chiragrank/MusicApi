import os
from pymongo import MongoClient
import pandas as pd

def extract_features(index, music_file):
    """
    Create a dictionary for each song to store title, url and genre
    """
    music = {}
    music["title"] = music_file.iloc[index]["title"]
    music["url"] = [music_file.iloc[index]["sample_30sec"]]
    music["genre"] = str(music_file.iloc[index]["g_num"])
    return music


def create_database(path, env_var):
    """
    Create a collection with music url, genre  and title for each song.
    """
    uri = os.environ.get(env_var)
    connection = MongoClient(uri)
    db = connection.music_exp
    music_file = pd.read_csv(path)
    total_songs = music_file.shape[0]
    if "music_data" in db.collection_names():
        db.music_data.drop()
    for i in range(total_songs):
        music = extract_features(i, music_file)
        db.music_data.insert_one(music)
    connection.close()
