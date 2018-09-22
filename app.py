import os
from flask import Flask,jsonify,request, session
from bson.objectid import ObjectId
from bson import json_util
import json
from pymongo import MongoClient
import numpy as np
from flask_cors import CORS

app = Flask(__name__)
uri = os.environ.get('MONDODB_URI')
app.config['DEBUG'] = True
app.config['SECRET_KEY'] = "this is a music app"
CORS(app)


@app.route('/getMusic', methods=["Post"])
def update_music():
    """
    Randomly Samples the music from the sampled genre and updates the database collection
    """
    connection = MongoClient(uri)
    db = connection.get_default_database()
    user_choice = request.get_json()  
    genre = np.random.choice(125)
    genre_music = list(db.music_data.find({"genre": str(genre)}))
    music_index = np.random.choice(len(genre_music))
    client_data = {}
    client_data["m_url"] = genre_music[music_index]["url"]
    client_data["m_id"] = str(genre_music[music_index]["_id"])
    db.user_data.update({"_id": ObjectId(user_choice["u_id"])}, {'$push': {'seq_music': client_data["m_id"]}})
    connection.close()
    return jsonify(client_data)


@app.route('/', methods=['GET'])
def create_store():
    """
    Creates a new user in the database
    """
    connection = MongoClient(uri)
    db = connection.get_default_database()
    music = db.music_data.find({})
    user = {}
    user["pos_music"] = []
    user["neg_music"] = []
    user["feedback"] = []
    user["seq_music"] = []
    user["av_music"] = [str(m["_id"]) for m in music]
    user_id = db.user_data.insert_one(user)
    user["u_id"] = str(user_id.inserted_id)
    del user["_id"]
    connection.close()
    return jsonify(user)


@app.route("/sendChoice", methods=["Post"])
def update_user():
    """
    Updates the user choice in the database
    """
    connection = MongoClient(uri)
    db = connection.get_default_database()
    user_choice = request.get_json()
    if user_choice["choice"] == "1":
        db.user_data.update({"_id": ObjectId(user_choice["u_id"])}, {'$push': {'pos_music': user_choice["m_id"]}})
    elif user_choice["choice"] == "-1":
        db.user_data.update({"_id": ObjectId(user_choice["u_id"])}, {'$push': {'neg_music': user_choice["m_id"]}})
    elif user_choice["choice"] == "0":
        db.user_data.update({"_id": ObjectId(user_choice["u_id"])}, {'$push': {'abs_music': user_choice["m_id"]}})
    user = db.user_data.find_one({"_id":ObjectId(user_choice['u_id'])})
    connection.close()
    return json.dumps(user, indent=4, default=json_util.default)


@app.route("/feedback", methods=["Post"])
def update_feedback():
    """
    Stores the user feedback in the database
    """
    connection = MongoClient(uri)
    db = connection.get_default_database()
    user_choice = request.get_json()
    db.user_data.update({"_id": ObjectId(user_choice["u_id"])}, {'$push': {'feedback': user_choice["comment"]}})
    user = db.user_data.find_one({"_id": ObjectId(user_choice['u_id'])})
    connection.close()
    return json.dumps(user, indent=4, default=json_util.default)


if __name__ == '__main__':
    app.secret_key = "this is a music app"
    app.run()
