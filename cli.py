import os
from clize import run
# setting up django
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "beaverdam.settings")
django.setup()
from annotator.models import Video
from subprocess import call


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


if __name__ == '__main__':
    run([add_videos, prepare_videos])
