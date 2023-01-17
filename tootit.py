#!/usr/bin/env python

# Identify posts that should be posted
import argparse
import requests
from mastodon import Mastodon
import subprocess
import time
import base64
import os
import glob
import re
import yaml
import copy
import datetime
import pytz

from dataclasses import dataclass
from typing import Optional

global TOOT_LENGTH
TOOT_LENGTH = 500

@dataclass
class Poll:
    options: list[str]


@dataclass
class Image:
    url: str
    alt: str
    remote: bool
    path: str = None
    REGEX = "!\[(?P<alt>.*)\]\((?P<url>.*)\)"

    @classmethod
    def from_match(cls, match):
        url = match.group('url')
        alt = match.group('alt')
        return cls(url=url, alt=alt, remote=bool(re.findall('https?://', url)))

    @classmethod
    def from_text(cls, text):
        return cls.from_match(re.match(cls.REGEX, text))

    def file_path(self):
        if self.remote:
            # Caches the image in our tmp path (mostly for testing.)
            path_hash = base64.b32encode(self.url.encode('utf-8')).decode('utf-8')
            tmpfile = os.path.join('/tmp', path_hash)

            if not os.path.exists(tmpfile):
                print(f"Downloading {url=}")
                results = requests.get(self.url)
                with open(tmpfile, 'wb') as f:
                    f.write(results.content)

            self.path = tmpfile
        else:
            self.path = self.url

        return self.path

    def mime_type(self):
        p = self.file_path()
        file_output = subprocess.check_output(['file', p, '--mime']).decode('utf-8')
        return file_output.split(':')[1].split(';')[0].strip()

@dataclass
class Album:
    images: list[Image]

    def path_and_mime(self):
        return [
            (i.file_path(), i.mime_type())
            for i in self.images
        ]

    def upload(self, masto, are_you_sure=False):
        if are_you_sure:
            # Mastodon.media_post(media_file, mime_type=None, description=None, focus=None, file_name=None, thumbnail=None, thumbnail_mime_type=None, synchronous=False)[source]
            # Post an image, video or audio file. media_file can either be data or a file name. If data is passed directly, the mime type has to be specified manually, otherwise, it is determined from the file name. focus should be a tuple of floats between -1 and 1, giving the x and y coordinates of the images focus point for cropping (with the origin being the images center).

            return [
                masto.media_post(media_file=i.file_path(), mime_type=i.mime_type(), description=i.alt)
                for i in self.images
            ]
        else:
            print([
                f"masto.media_post(media_file={i.file_path()}, mime_type={i.mime_type()}, description={i.alt})"
                for i in self.images
            ])


@dataclass
class Toot:
    """A class representing a markdown toot"""
    contents: list[str]
    language: str = "en"
    date: str = None
    cw: str = None
    visibility: str = "private" # One of "direct", "private", "public"
    auto_thread_emoji: bool = True

    @classmethod
    def from_text(cls, data):
        if '---\n' in data:
            meta = yaml.safe_load(data.split('---')[1])
            data = data.split('---')[2].strip().split('\n\n')
        else:
            meta = {}
            data = data.strip().split('\n\n')

        return cls(contents=data, **meta)

    def calculate_length(self, para):
        return len(self.cw if self.cw else "") + sum(len(p) for p in para if type(p) == str) # TODO: URLs count as 33 chars or some nonsense.

    @classmethod
    def looks_like_images(cls, para):
        return all(x.startswith('![') for x in para.split('\n'))

    @classmethod
    def looks_like_poll(cls, para):
        return all(x.startswith('- [ ] ') for x in para.split('\n'))

    def convert_content(self, contents):
        if self.looks_like_images(contents):
            return Album(images=[Image.from_text(i) for i in contents.split('\n')])
        elif self.looks_like_poll(contents):
            return Poll(options=[i[6:] for i in contents.split('\n')])
        else:
            return contents

    @classmethod
    def textonly(cls, contents):
        return '\n\n'.join([
            x for x in contents
            if isinstance(x, str)
        ])

    def split_contents(self):
        contents = list(self._split_contents())

        if self.auto_thread_emoji and len(contents) > 1:
            for idx, toot in enumerate(contents):
                if self.calculate_length(toot) < TOOT_LENGTH - 6:
                    toot.append(f"\n{idx + 1}/{len(contents)}")
                yield toot
        else:
            yield from contents

    def _split_contents(self):
        current = []
        remaining_contents = copy.copy(self.contents)
        while True:
            # End of contents.
            if len(remaining_contents) == 0:
                if len(current) > 0:
                    yield current
                break

            # If adding a new paragraph would go over the max char length
            too_long = self.calculate_length(current + [self.convert_content(remaining_contents[0])]) > TOOT_LENGTH
            too_much_media = any(isinstance(x, Album) for x in current) and isinstance(self.convert_content(remaining_contents[0]), Album)
            too_many_polls = any(isinstance(x, Poll) for x in current) and isinstance(self.convert_content(remaining_contents[0]), Poll)

            if too_long or too_much_media or too_many_polls:
                yield current
                current = [self.convert_content(remaining_contents.pop(0))]
            else:
                current.append(self.convert_content(remaining_contents.pop(0)))

def parseToot(fn):
    print(f"Parsing {fn}")
    with open(fn, 'r') as handle:
        data = handle.read()
        return Toot.from_text(data)

def sendToot(toot, mastodon):
    in_reply_to_id = None
    for post in toot.split_contents():
        print('=====')
        if toot.cw:
            print(f"CW: {toot.cw}")

        media = [x for x in post if isinstance(x, Album)]
        poll = [x for x in post if isinstance(x, Poll)]

        media_ids = None

        if media:
            album = media[0]
            print("MEDIA", album)
            print(album.path_and_mime())
            media_ids = album.upload(mastodon, True)

        #if any(isinstance(x, Poll) for x in post):
        #    print("POLL")
        # TODO: poll lifetime
        # TODO: poll multiple

        text = Toot.textonly(post)
        print(f"PREPARING TOOT {in_reply_to_id=} {text=}")

        response = mastodon.status_post(text, in_reply_to_id=in_reply_to_id, media_ids=media_ids, sensitive=False, spoiler_text=toot.cw, language=toot.language, visibility=toot.visibility, poll=None)
        in_reply_to_id = response['id']
        print(f"SENT TOOT id={in_reply_to_id}")
        time.sleep(5)

        # TODO: support sensitive-media? (well it's handled automatically by CW'ing the post, so, maybe not necessary.)
        # TODO: idempotency_key

def gitMvToot(fn, args):
    files = subprocess.check_output(['git', 'ls-files']).decode('utf-8').split('\n')
    if fn not in files:
        # File not tracked by git, probably a dev testing locally.
        return None

    # Create an outbox if it doesn't exist.
    os.makedirs(args.outbox, exist_ok=True)

    subprocess.check_call([
        'git', 'mv',
        fn, fn.replace(args.inbox, args.outbox)
    ])

if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='tootit')
    parser.add_argument('inbox')
    parser.add_argument('outbox')
    parser.add_argument('server', help='FQDN only')
    parser.add_argument('token')
    parser.add_argument('file', nargs='*', help="toot a specific md, if specified, rather than discovering from the inbox")
    parser.add_argument('--toot-length', default=500, type=int)
    #parser.add_argument('--visibility', default='private', choices=['public', 'private'], type=str, help="Only really relevant when tooting from md.")
    args = parser.parse_args()

    TOOT_LENGTH = args.toot_length

    mastodon = Mastodon(
        api_base_url=args.server,
        access_token=os.environ['FEDI_ACCESS_TOKEN']
    )

    files = []
    if len(args.file) > 0:
        files = args.file
    else:
        files = glob.glob(os.path.join(args.inbox, '*'))

    for fn in files:
        toot = parseToot(fn)

        # If there's no date, send now
        if not toot.date:
            sendToot(toot, mastodon)
            gitMvToot(fn, args)

        # Otherwise, check if we're past that date.
        now = datetime.datetime.now(tz=pytz.UTC)
        if toot.date < now:
            sendToot(toot, mastodon)
            gitMvToot(fn, args)

        # Otherwise we can ignore it for now.
