import os
from clize import run
import numpy as np
# setting up django
import shutil
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "beaverdam.settings")
django.setup()
from annotator.models import Video
from subprocess import call
import json
import cv2
from skimage.io import imread
from skimage.io import imsave

def prepare_videos(folder='annotator/static/videos'):
    for name in os.listdir(folder):
        path = os.path.join(folder, name)
        call('scripts/convert-to-h264 {}'.format(path), shell=True)


def add_videos(folder='annotator/static/videos', host='/static/videos/'):
    Video.objects.filter().delete()
    for name in os.listdir(folder):
        nb = Video.objects.filter(filename=name).count()
        if nb > 0:
            print('{} is already on the DB'.format(name))
            continue
        video = Video()
        video.filename = name
        video.host = host
        video.save()

def check_annotations():
    video_id = 33
    video = Video.objects.filter(id=video_id).first()
    filename = 'exported_annotations/{}.json'.format(video_id)
    anns = json.load(open(filename))
    if not os.path.exists('tmp'):
        os.mkdir('tmp')
        _generate_frames_video(os.path.join('annotator/static/videos/{}'.format(video.filename)), 'tmp')
    ims = {}
    for obj in anns:
        for frame in obj['frames']:
            frameid = frame['frameid']
            filename = os.path.join('tmp', 'image_{:05d}.jpg'.format(frame['frameid']))
            bbox_list = [
                ((frame['x'], frame['y'], frame['w'], frame['h']), obj['type']) 
            ]
            im = ims.get(frameid, imread(filename))
            draw_bounding_boxes(im, bbox_list, color=[255, 255, 255])
            ims[frameid] = im
            print(frame['frameid'], frame['x'], frame['y'], frame['w'], frame['h'])
    print(ims.keys())
    for k, im in ims.items():
        imsave('res/{}.png'.format(k), im)

def draw_bounding_boxes(
    image,
    bbox_list, 
    color=[1.0, 1.0, 1.0], 
    text_color=(1, 1, 1), 
    font=cv2.FONT_HERSHEY_PLAIN, 
    font_scale=1.0,
    pad=0):
    for bb in bbox_list:
        if len(bb) == 3:
            bbox, class_name, score = bb
        elif len(bb) == 2:
            bbox, class_name = bb
            score = None
        else:
            raise ValueError(bb)
        x, y, w, h = bbox
        x = int(x) + pad
        y = int(y) + pad
        w = int(w)
        h = int(h)
        xmin, ymin, xmax, ymax = x, y, x + w, y + h
        xmin = np.clip(xmin, 0, image.shape[1])
        xmax = np.clip(xmax, 0, image.shape[1])
        ymin = np.clip(ymin, 0, image.shape[0])
        ymax = np.clip(ymax, 0, image.shape[0])

        image = cv2.rectangle(image, (xmin, ymin), (xmax, ymax), color, thickness=10)
        if score:
            text = '{}({:.2f})'.format(class_name, score)
        else:
            text = class_name
        image = cv2.putText(image, text, (x, y), font, font_scale, text_color, 2, cv2.LINE_AA)
    

def _generate_video_from_frames(pattern, dest):
    # creates a video from a set of images obeying the `pattern`
    # and name the video `dest`
    cmd = "ffmpeg -i {} -vf fps=25 {}".format(pattern, dest)
    call(cmd, shell=True)


def _generate_frames_video(filename, dest):
    # generate frames of a video
    cmd = 'ffmpeg -i {} {}/image_%05d.jpg'.format(filename, dest)
    call(cmd, shell=True)


if __name__ == '__main__':
    run([add_videos, prepare_videos, check_annotations])
