import os
from datetime import datetime

from flask import Flask, render_template, request, flash, abort
from flask_uploads import IMAGES, UploadSet, configure_uploads
from flask_sqlalchemy import SQLAlchemy

from werkzeug.utils import redirect

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///gallery.db'
db = SQLAlchemy(app)

photos = UploadSet('photos', IMAGES)
app.config['UPLOADED_PHOTOS_DEST'] = 'static/data/'
app.config['SECRET_KEY'] = os.urandom(24)
configure_uploads(app, photos)


class Gallery(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    picName = db.Column(db.String(100), nullable=False, unique=True)
    tags = db.Column(db.String())
    dateUploaded = db.Column(db.DateTime, default=datetime.utcnow)
    uploadedBy = db.Column(db.String(40))

    def __repr__(self):
        return '<Picture %r>' % self.id


# A very bad way of filtering users because I couldn't work out how to do proper users
@app.before_request
def limit_remote_addr():

    file = open('authorized_ips.txt')
    ips = file.read().split(',')
    file.close()

    for ip in ips:
        if ip == request.remote_addr:
            break
    else:
        abort(403) # not whitelisted ip


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST' and 'photo' in request.files:

        # really fancy, saves the photo (adding a '_n' if file already exists) and returns the name of the photo... i should really read things before spending an hour trying to get the name of the file through other methods
        pic_picName = photos.save(request.files['photo'])
        pic_tags = "" # saved like a csv probably
        pic_uploadedBy = request.remote_addr # hardcoding stuff temporarily

        new_pic = Gallery(picName=pic_picName, tags=pic_tags, uploadedBy=pic_uploadedBy)

        try:
            db.session.add(new_pic)
            db.session.commit()
            flash('Photo saved successfully')
            return render_template('upload.html')
        except:
            flash('Photo upload failed')
            return render_template('upload.html')
        
    return render_template('upload.html')


@app.route('/dbView')
def dbView():
    gallery = Gallery.query.order_by(Gallery.id).all()
    #gallery = Gallery.query.filter(Gallery.tags.contains('m')).all()
    return render_template('dbView.html', gallery=gallery)


@app.route('/search', methods=['GET', 'POST'])
def search():
    if 'query' in request.args:
        searchTerms = request.args['query']
    else:
        if request.method == 'POST':
            return redirect('/search?query='+request.form['searchTerm'])
        else:
            return render_template('searchBox.html')

        #return 'Error: enter a valid search term' # maybe replace with search box
    
    gallery = []
    for term in searchTerms.split(','):
        for pic in Gallery.query.filter(Gallery.tags.contains(term)).all():
            gallery.append(pic)
    
    gallery = list(dict.fromkeys(gallery)) # removing dupes through python weirdness
    
    #gallery = Gallery.query.filter(Gallery.tags.contains(searchTerms)).all()

    return render_template('search.html', gallery=gallery) # replace with custom template


@app.route('/image')
def image():
    if 'id' in request.args:
        try:
            id = int(request.args['id'])
        except:
            return 'Error: invalid id'
    else:
        return 'Error: no provided id'

    imageToShow = Gallery.query.get_or_404(id)
    return render_template('image.html', pic=imageToShow)


@app.route('/updateTags', methods=['GET', 'POST'])
def updateTags():
    if 'id' in request.args:
        try:
            id = int(request.args['id'])
        except:
            return 'Error: invalid id'
    else:
        return 'Error: no provided id'
    
    imageToChange = Gallery.query.get_or_404(id)

    if request.method == 'POST':
        imageToChange.tags = request.form['tags']

        try:
            db.session.commit()
            return redirect('/image?id='+str(id))
        except:
            return 'Error: there was an issue updating the tags'
    else:
        return render_template('updateTags.html', pic=imageToChange)


if __name__ == "__main__":
    app.run(debug=True)
