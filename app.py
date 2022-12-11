import os
import cv2
from glob import glob
import numpy as np
from flask import Flask, render_template, request, redirect, flash, url_for
from werkzeug.utils import secure_filename
import tensorflow as tf
from os.path import join, dirname, realpath

UPLOAD_FOLDER = 'static/uploads/'

# initialize the application
app = Flask(__name__)
app.debug = 1
app.secret_key = "secret key"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024



@app.route("/", methods=['GET'])
def index():
    """
    index: homepage
    render the homepage when a user visits the page
    """
    return render_template('index.html')

@app.route("/upload", methods=['GET', 'POST'])
def upload_video():
    """
    /upload: used to upload videos on the server
    returns a 200 http response when the video is upload
    returns a 400 http response when the video format isn't supported or when 
            size is greater than 10mb
    """
    if request.method == "POST":
        if 'video' not in request.files:
            flash('No video uploaded')
            return redirect(request.url)
        video = request.files['video']
        if video.filename == '':
            flash('No image selected for uploading')
            return redirect(request.url)
        else:
            filename = secure_filename(video.filename)
            video.save(os.path.join(app.config['UPLOAD_FOLDER'], "videos", filename))
            flash('Video successfully uploaded and displayed below')
    ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
    list_files = []
    for _, _, files in os.walk(os.path.join(ROOT_DIR, app.config['UPLOAD_FOLDER'])):
        list_files = files
    return render_template('uploads.html', videos=list_files)


# redirect to the html page with the specific video and contents
@app.route('/upload/<filename>')
def display_video(filename):
    print(filename)
    frame_video(filename)
    FRAMES = join(dirname(realpath(__file__)), f'{app.config["UPLOAD_FOLDER"]}frames/{filename}/')
    images = os.listdir(f"{FRAMES}")
    images = [ f"uploads/frames/{filename}/" + image for image in images]
    return render_template("uploaded_video.html", images=images, video=filename, code=True)


def frame_video(video_name):
    FRAMES = join(dirname(realpath(__file__)), f'{app.config["UPLOAD_FOLDER"]}frames/{video_name}/')
    RESIZED = join(dirname(realpath(__file__)), f'{app.config["UPLOAD_FOLDER"]}resized/{video_name}/')
    try:
        os.makedirs(FRAMES)
        os.makedirs(RESIZED)
    except:
        print("file already exist")
    existing_frames = os.listdir(FRAMES)
    existing_resized = os.listdir(RESIZED)
    if len(existing_frames) > 1:
        if len(existing_resized) > 1:
            return
        resize_video(video_name)
    def save_frame(video_path, gap):
        images_array = []
        name = video_path.split("\\")[0].split(".")[0]
        cap = cv2.VideoCapture(video_path)
        index = 0

        while True:
            ret, frame = cap.read()
            if ret == False:
                cap.release()
                break
            if frame is None:
                break
            else:
                if index == 0:
                    images_array.append(frame)
                    cv2.imwrite(f"{FRAMES}{index}.jpeg", frame)
                else:
                    if index % gap == 0:
                        images_array.append(frame)
                        cv2.imwrite(f"{FRAMES}{index}.jpeg", frame)
            index += 1
        return np.array(images_array)

    video_paths = glob("static/uploads/videos/*")
    for path in video_paths:
        array_of_images = save_frame(path, gap=10)
        resize_video(video_name)

def resize_video(video_name):
    FRAMES = join(dirname(realpath(__file__)), f'{app.config["UPLOAD_FOLDER"]}frames/{video_name}/')
    RESIZED = join(dirname(realpath(__file__)), f'{app.config["UPLOAD_FOLDER"]}resized/{video_name}/')  
    def resize_frames():
        frame_paths = glob(f"{FRAMES}*.jpeg")
        index = 0
        width, height = (299, 299)

        for frame in frame_paths:
            image = cv2.imread(frame)
            image_resized = cv2.resize(image, (299, 299))
            cv2.imwrite(f"{RESIZED}%i.jpeg"%index, image_resized)
            
            index += 1   
    resize_frames()


@app.route("/predict/<video_name>", methods=["POST","GET"])
def make_prediction(video_name):
    def fetch_frames():
        frame_paths = glob(f"static/resized/{video_name}/*.jpeg")
        query_frames_array = []

        for frame in frame_paths:
            image = cv2.imread(frame)
            query_frames_array.append(image)
        return np.array(query_frames_array)

    query_frames_array = fetch_frames()
    video_frame_classifier = tf.keras.models.load_model("incV3.h5")
    query_results = video_frame_classifier.predict(query_frames_array)
    decoded_query_results = tf.keras.applications.inception_v3.decode_predictions(query_results, top=5)

    def showResults(decoded_response):
        search_query_value = request.form["query"]
        print("search_query_value", search_query_value)
        for i in range(len(decoded_response)):
            class_tupple = decoded_response[i]
            _id, frame_class, frame_prob = class_tupple[0]
            image_index = i
            if search_query_value == "":
                pass
            elif search_query_value == frame_class:
                image_index = i
                break
        return i*10, frame_class
    image_index, frame_class = showResults(decoded_query_results)
    images = os.listdir(UPLOAD_FOLDER)
    images = [ f"frames/{video_name}" + image for image in images]
    videos = os.listdir(UPLOAD_FOLDER)
    videos = [ "uploads/videos/" + video for video in videos]
    print(image_index)
    return render_template("uploaded_video.html", index=image_index, class_name=frame_class, images=images, video=video_name)


if __name__ == "__main__":
    from wsgiref.simple_server import make_server
    with make_server("", 8000, app) as server:
        print("serving on port 8000...")
        server.serve_forever()
    
    