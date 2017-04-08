#!/usr/bin/env python3
import datetime
import os

import dropbox
import sys

import logging
from dropbox.exceptions import AuthError, ApiError
from dropbox.files import WriteMode

from config import TOKEN, BACKUP_PATH

if __name__ == '__main__':

    dbx = dropbox.Dropbox(TOKEN)

    try:
        dbx.users_get_current_account()
    except AuthError as err:
        sys.exit("ERROR: Invalid access token; try re-generating an "
                 "access token from the app console on the web.")

    try:
        file = sys.argv[1]
    except IndexError as e:
        sys.exit('File is undefined')
        exit(1)

    if not os.path.exists(file):
        raise Exception('File not found')

    logging.basicConfig(
        level='INFO',
        filename='backup_%s.log' % os.path.basename(file).replace('.', '_'),
        format='%(levelname)s   %(asctime)s %(process)d   %(message)s'
    )

    logging.info('\n\n')

    upload_path = '%s%s' % (BACKUP_PATH, os.path.basename(file))

    logging.info('Uploading %s to Dropbox as %s' % (file, upload_path))

    entries = dbx.files_list_revisions(upload_path, limit=10).entries
    revisions = reversed(sorted(entries, key=lambda entry: entry.server_modified))

    logging.info('%s last %d revisions:' % (upload_path, len(entries)))
    for revision in revisions:
        logging.info('{revision}: {date}'.format(revision=revision.rev, date=revision.server_modified))

    with open(file, 'rb') as f:
        try:
            dbx.files_upload(f.read(), upload_path, mode=WriteMode('overwrite'))
        except ApiError as e:
            if (e.error.is_path() and
                    e.error.get_path().error.is_insufficient_space()):
                logging.error("ERROR: Cannot back up; insufficient space.")
                exit(1)
            elif e.user_message_text:
                logging.error(e.user_message_text)
                exit(1)
            else:
                logging.error(e)
                exit(1)

        logging.info('Uploaded')