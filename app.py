import os
import cv2
from flask import Flask, render_template, request, redirect, flash, url_for
from werkzeug.utils import secure_filename
import tensorflow as tf

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
    return render_template('uploaded_video.html')
	# return redirect(url_for('static', filename='uploads/' + filename), code=301)

@app.route('/predict/<query>')
def make_prediction(query):
	return "prediction" + str(query)


def frame_video():
    """ Return the frame """
    pass

def resize_video():
    """ Resize the video """
    pass

def predict():
    """ Predict the outcome """
    pass