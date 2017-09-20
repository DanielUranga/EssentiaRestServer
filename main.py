from json_tricks.np import dump, dumps, load, loads, strip_comments
from flask import Flask, request, redirect, url_for
from flask_restful import Resource, Api
from webargs import fields, validate
from webargs.flaskparser import use_kwargs, parser

import os
import essentia
import essentia.standard

ALLOWED_EXTENSIONS = set(['flac', 'mp3'])

app = Flask(__name__)
api = Api(app)

app.config['UPLOAD_FOLDER'] = '/tmp/'
app.config['UPLOAD_FILE'] = 'essentia'
app.config['UPLOAD_COMPLETE_FILENAME'] =                                    \
    app.config['UPLOAD_FOLDER'] + '/' + app.config['UPLOAD_FILE']

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.route("/upload/", methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        file = request.files['file']
        if file and allowed_file(file.filename):
            file.save(os.path.join(                                         \
                app.config['UPLOAD_FOLDER'],                                \
                app.config['UPLOAD_FILE']))
            return redirect(url_for('index'))
    return """
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form action="" method=post enctype=multipart/form-data>
      <p><input type=file name=file>
         <input type=submit value=Upload>
    </form>
    """

RESULT_OK = { 'Result' : 'Ok' }
def RESULT_FAIL(reason):
    return { 'Result' : 'Fail', 'Reason' : reason }

audio = None

class RunEssentia(Resource):
    def get(self):
        global audio
        loader = essentia.standard.MonoLoader(                              \
          filename = app.config['UPLOAD_COMPLETE_FILENAME'])
        audio = loader()
        return RESULT_OK
api.add_resource(RunEssentia, '/run_essentia')

class DurationInSeconds(Resource):
    global audio
    def get(self):
        if audio is None:
            return RESULT_FAIL({ 'no_audio' : audio is None })
        return { 'duration' : int(audio.size / 44100) }
api.add_resource(DurationInSeconds, '/duration')

class AudioArray(Resource):
    args = {
        'start': fields.Int(required=True),
        'end': fields.Int(required=True)
    }
    @use_kwargs(args)
    def get(self, start, end):
        global audio
        if audio is None or start > end or start < 0:
            return RESULT_FAIL(                                             \
                {'no_audio' : audio is None, 'start' : start, 'end' : end } \
            )
        return dumps(audio[start * 44100 : end * 44100])
api.add_resource(AudioArray, '/audio_array')

class BeatTrackerDegara(Resource):
    def get(self):
        global audio
        if audio is None:
            return RESULT_FAIL({ 'no_audio' : audio is None })
        beat_tracker = essentia.standard.BeatTrackerDegara()
        return dumps(beat_tracker(audio))
api.add_resource(BeatTrackerDegara, '/beat_tracker_degara')

class BeatTrackerMultiFeature(Resource):
    def get(self):
        global audio
        if audio is None:
            return RESULT_FAIL({ 'no_audio' : audio is None })
        beat_tracker = essentia.standard.BeatTrackerMultiFeature()
        return dumps(beat_tracker(audio))
api.add_resource(BeatTrackerMultiFeature, '/beat_tracker_multifeature')

if __name__ == '__main__':
    app.run(debug=True)
