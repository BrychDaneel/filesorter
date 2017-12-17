import configparser
import os
import sys
from datetime import datetime
import argparse
from mimetypes import MimeTypes
import shutil


MIN_DAYS = 7
CHANGE_MONTH = 1
MONTH_PREFIX = 'archive'


def change_date(path):
    if os.path.isfile(path):
        ct = os.path.getctime(path)
        dt = datetime.fromtimestamp(ct)
        return dt

    mx = None
    for d, _, files in os.walk(path):
        for f in files:
            file_path = os.path.join(path, d, f)
            if not mx:
                mx = change_date(file_path)
            else:
                mx = max(mx, change_date(file_path))
    return mx


def month_prefix(dt):
    now = datetime.now()
    if  (now.year == dt.year) and (now.month - dt.month < CHANGE_MONTH):
        return ''

    pr = dt.strftime("%m.%y")
    return os.path.join(MONTH_PREFIX, pr)


def mmi_prefix(path):
    if os.path.isdir(path):
        return 'dirs'

    mt = MimeTypes()
    main_type, _ = mt.guess_type(path)
    if main_type:
        return main_type.split('/')[1]

    filename, file_extension = os.path.splitext(path)
    if file_extension:
        return file_extension.replace('.','')

    return 'unknown'


def sortfiles(source, dist):
    for elm in os.listdir(source):
        path = os.path.join(source, elm)
        if os.path.exists(dist) and os.path.samefile(dist, path):
            continue

        dt = change_date(path)
        if not dt:
            shutil.rmtree(path, True)
            continue
        now = datetime.now()

        if (now - dt).days <= MIN_DAYS:
            continue

        month_pr = month_prefix(dt)
        mime_pr = mmi_prefix(path)
        dr = os.path.join(dist, month_pr, mime_pr)
        os.makedirs(dr, exist_ok=True)
        new_path = os.path.join(dr, elm)
        os.rename(path, new_path)


def resort(dist):
    if not os.path.exists(dist):
        return

    for dr in os.listdir(dist):
        if os.path.commonprefix([dr, MONTH_PREFIX]):
            continue
        empty = True
        dr_path = os.path.join(dist, dr)
        for el in os.listdir(dr_path):
            path = os.path.join(dr_path, el)
            dt = change_date(path)
            if not dt:
                shutil.rmtree(path, True)
                continue

            now = datetime.now()
            if now.month - dt.month < CHANGE_MONTH:
                empty = False
                continue

            month_pr = month_prefix(dt)
            new_dr = os.path.join(dr_path, month_pr)
            os.makedirs(new_dr, exist_ok=True)
            new_path = os.path.join(dr, el)

            os.rename(path, new_path)

        if empty:
            shutil.rmtree(dr_path, True)


if __name__ == '__main__':
    script_dir = os.path.dirname(os.path.realpath(__file__))

    config = configparser.ConfigParser()
    try:
        config.read(['filesorter.ini', 
                    os.path.join(script_dir, 'filesorter.ini'),
                    '~/filesorter.ini', '/etc/filesorter.ini'])
        cfg = dict(config.items('DEFAULT'))
        cfg['days'] = int(cfg['days'])
        cfg['month'] = int(cfg['month'])
    except:
        cfg = {'source':None, 'dist':None, 'days':None, 
               'month':None, 'mprefix':None}

    parser = argparse.ArgumentParser(description='Sort file by date and MMI')
    parser.add_argument('--source', '-s', 
                        help='source dir', default=cfg['source'])
    parser.add_argument('--archive', '-a', help='target dir', default=cfg['dist'])
    parser.add_argument('--days', '-d', help='min days', default=cfg['days'])
    parser.add_argument('--month', '-m', help='min moth', default=cfg['month'])
    parser.add_argument('--mprefix', '-p', 
                        help='moth dir name', default=cfg['mprefix'])

    args = parser.parse_args()

    if args.days:
        MIN_DAYS = args.days
    if args.month:
        CHANGE_MONTH = args.month
    if args.mprefix:
        MONTH_PREFIX = args.mprefix

    if not args.source or not args.archive:
        print('Command line must contains source and dist dirs.')
        sys.exit(1)

    source = os.path.expanduser(args.source)
    archive = os.path.expanduser(args.archive)
    resort(archive)
    sortfiles(source, archive)
