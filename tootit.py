#!/usr/bin/env python

# Mastodon.media_post(media_file, mime_type=None, description=None, focus=None, file_name=None, thumbnail=None, thumbnail_mime_type=None, synchronous=False)[source]
# Post an image, video or audio file. media_file can either be data or a file name. If data is passed directly, the mime type has to be specified manually, otherwise, it is determined from the file name. focus should be a tuple of floats between -1 and 1, giving the x and y coordinates of the images focus point for cropping (with the origin being the images center).

#  Mastodon.status_post(status, in_reply_to_id=None, media_ids=None, sensitive=False, visibility=None, spoiler_text=None, language=None, idempotency_key=None, content_type=None, scheduled_at=None, poll=None, quote_id=None)[source]
# The sensitive boolean decides whether or not media attached to the post should be marked as sensitive, which hides it by default on the Mastodon web front-end. 

# Mastodon.make_poll(options, expires_in, multiple=False, hide_totals=False)[source]
# Generate a poll object that can be passed as the poll option when posting a status. options is an array of strings with the poll options (Maximum, by default: 4), expires_in is the time in seconds for which the poll should be open. Set multiple to True to allow people to choose more than one answer. Set hide_totals to True to hide the results of the poll until it has expired.
