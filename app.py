import os
from flask import Flask,jsonify,request, session
from bson.objectid import ObjectId
from bson import json_util
import json
from pymongo import MongoClient
import numpy as np
from pyAudioAnalysis import audioTrainTest as att
from flask_cors import CORS

app = Flask(__name__)
uri = os.environ.get('MONGODB_URI')
app.config['DEBUG'] = True
app.config['SECRET_KEY'] = "this is a music app"
CORS(app)


def predict_music(user):
    """
    predicts the music based on the user choice
    :parameter
    user: (dic) Contains the user response for the songs
    :return
    selected_music: (int) Index of the recommended music based on user response using SVM
    """
    connection = MongoClient(uri)
    db = connection.get_default_database()

    pos_feature = []
    for p_index in user['pos_music']:
        p_music = db.music_data.find_one({"_id": ObjectId(p_index)})
        pos_feature.append(np.asarray(p_music['stFeatures']))
    neg_feature = []
    for n_index in user['neg_music']:
        n_music = db.music_data.find_one({"_id": ObjectId(n_index)})
        neg_feature.append(np.asarray(n_music['stFeatures']))

    features = [(np.hstack(pos_feature)).T, (np.hstack(neg_feature)).T]
    model = att.trainSVM_RBF(features, 0.1)
    selected_music = user["av_music"][0]
    selected_value = 0
    for i in user["av_music"]:
        s_music = db.music_data.find_one({"_id": ObjectId(i)})
        feature = np.asarray(s_music['stFeatures'])
        predict = [0, 0]
        for j in range(feature.shape[1]):
            predict[int(model.predict(feature[:, j].reshape(1, -1)))] += 1
        if (predict[0] / (predict[0] + predict[1])) > selected_value:
            selected_value = (predict[0] / (predict[0] + predict[1]))
            selected_music = i
    connection.close()
    return selected_music


@app.route('/getMusic', methods=["Post"])
def update_music():
    """
    provides url of recommended music based on user response
    """
    connection = MongoClient(uri)
    db = connection.get_default_database() 
    user_id = request.get_json()
    user = db.user_data.find_one({"_id": ObjectId(user_id["u_id"])})
    client_data = {}
    if len(user["av_music"]) > 0:
        if len(user['pos_music']) == 0 or len(user['neg_music']) == 0:
            music_index = np.random.choice(user["av_music"])
        else:
            music_index = predict_music(user)
        session["m_id"] = music_index
        db.user_data.update({"_id": ObjectId(user_id["u_id"])}, {'$pull': {'av_music': session["m_id"]}})
        suggestion_music = db.music_data.find_one({"_id": ObjectId(music_index)})
        client_data["m_url"] = suggestion_music["url"]
        client_data["m_id"] = music_index
    else:
        client_data["m_url"] = "None"
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
    user["av_music"] = [str(m["_id"]) for m in music]
    user["pos_music"] = []
    user["neg_music"] = []
    user["abs_music"] = []
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
    user = db.user_data.find_one({"_id": ObjectId(user_choice['u_id'])})
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
