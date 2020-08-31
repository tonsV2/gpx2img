import os
from datetime import datetime, timedelta
from fractions import Fraction

import exifread
import gpxpy
import piexif
import pytz

# Inspiration: https://gist.github.com/c060604/8a51f8999be12fc2be498e9ca56adc72

gpx_directory = './data/gpx'
image_directory = './data/images/Nepal - Everest Basecamp 2016'

timezone = "Asia/Katmandu"
timedelta_threshold = 10


def nearest(needle, haystack):
    def abs_func(d):
        return abs(d - needle)

    min_value = min(haystack, key=abs_func)
    return min_value, abs_func(min_value)


def extract_points(directory):
    points_by_time = {}
    for filename in os.listdir(directory):
        if filename.endswith(".gpx"):
            path = f"{gpx_directory}/{filename}"
            print(f"Parsing: {path}")
            gpx_file = open(path, 'r')
            gpx = gpxpy.parse(gpx_file)

            points = 0
            for track in gpx.tracks:
                for segment in track.segments:
                    points += len(segment.points)
                    for point in segment.points:
                        points_by_time[point.time] = point
            print(f"Found {points} points")
    return points_by_time


def to_deg(value, loc):
    """convert decimal coordinates into degrees, munutes and seconds tuple

    Keyword arguments: value is float gps-value, loc is direction list ["S", "N"] or ["W", "E"]
    return: tuple like (25, 13, 48.343 ,'N')
    """
    if value < 0:
        loc_value = loc[0]
    elif value > 0:
        loc_value = loc[1]
    else:
        loc_value = ""
    abs_value = abs(value)
    deg = int(abs_value)
    t1 = (abs_value - deg) * 60
    min = int(t1)
    sec = round((t1 - min) * 60, 5)
    return deg, min, sec, loc_value


def change_to_rational(number):
    """convert a number to rantional

    Keyword arguments: number
    return: tuple like (1, 2), (numerator, denominator)
    """
    f = Fraction(str(number))
    return f.numerator, f.denominator


def set_gps_location(file_name, lat, lng, altitude):
    """Adds GPS position as EXIF metadata

    Keyword arguments:
    file_name -- image file
    lat -- latitude (as float)
    lng -- longitude (as float)
    altitude -- altitude (as float)

    """
    lat_deg = to_deg(lat, ["S", "N"])
    lng_deg = to_deg(lng, ["W", "E"])

    exiv_lat = (change_to_rational(lat_deg[0]), change_to_rational(lat_deg[1]), change_to_rational(lat_deg[2]))
    exiv_lng = (change_to_rational(lng_deg[0]), change_to_rational(lng_deg[1]), change_to_rational(lng_deg[2]))

    gps_ifd = {
        piexif.GPSIFD.GPSVersionID: (2, 0, 0, 0),
        piexif.GPSIFD.GPSAltitudeRef: 1,
        piexif.GPSIFD.GPSAltitude: change_to_rational(round(altitude)),
        piexif.GPSIFD.GPSLatitudeRef: lat_deg[3],
        piexif.GPSIFD.GPSLatitude: exiv_lat,
        piexif.GPSIFD.GPSLongitudeRef: lng_deg[3],
        piexif.GPSIFD.GPSLongitude: exiv_lng,
    }

    # https://gist.github.com/c060604/8a51f8999be12fc2be498e9ca56adc72#gistcomment-3072034
    #    exif_dict = {"GPS": gps_ifd}
    #    exif_bytes = piexif.dump(exif_dict)
    #    piexif.insert(exif_bytes, file_name)

    gps_exif = {"GPS": gps_ifd}

    # get original exif data first!
    exif_data = piexif.load(file_name)

    # update original exif data to include GPS tag
    exif_data.update(gps_exif)
    exif_bytes = piexif.dump(exif_data)

    piexif.insert(exif_bytes, file_name)


def cli():
    print("Parsing GPS files...")
    points_by_time = extract_points(gpx_directory)
    if not len(points_by_time):
        exit("ERROR: No points found!")

    haystack = sorted(points_by_time.keys())

    print("\nParsing image files...")
    for filename in os.listdir(image_directory):
        if filename.endswith(".JPG") or filename.endswith(".jpg"):
            path = f"{image_directory}/{filename}"
            print(f"Parsing: {path}")

            f = open(path, 'rb')
            tags = exifread.process_file(f)
            exif_datetime_tag = tags["EXIF DateTimeOriginal"]

            tz = pytz.timezone(timezone)
            exif_datetime = datetime.strptime(str(exif_datetime_tag), "%Y:%m:%d %H:%M:%S").replace(tzinfo=tz)

            found, distance = nearest(exif_datetime, haystack)
            if distance > timedelta(minutes=timedelta_threshold):
                print(f"WARNING! Distance bigger than {timedelta_threshold} mins: {distance}")
            else:
                print(f"Found good match! {distance}")
                point = points_by_time[found]
                # set_gps_location(path, point.latitude, point.longitude, point.elevation)
