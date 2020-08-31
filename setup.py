import os

from setuptools import setup


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name='gpx2img',
    version='1.0.0',
    description='See https://github.com/tonsV2/gpx2img',
    python_requires='>=3',
    py_modules=['gpx2img'],
    install_requires=[
        'gpxpy',
        'ExifRead',
        'piexif',
        'pytz'
    ],
    entry_points='''
        [console_scripts]
        gpx2img=gpx2img:cli
    ''',
    long_description=read('README.md'),
)
