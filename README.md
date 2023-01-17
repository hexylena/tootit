# TootIt, a collaborative tooting experience

This action will send toots from an inbox, or with specified markdown files.

## Features

By writing markdown documents placed in `inbox/`, you can automatically convert these into toots!

- Automatic threading, if a post is longer than the maximum length characters, it will be split
- Automatic thread offset counters (e.g. a 1/3 added to the end of your toot)
- Image uploading (local files or via URL) with alt text (mandatory)
- Support for toot metadata
    - Language
    - Content Warning
- Will only toot a toot after it's date has passed, allowing pre-prepared toots to be edited right up until their posting date


## Inputs

There are two modes: from file, and from directory. From file lets you toot immediately the contents of a markdown file, while from directory lets you toot any files in the inbox that must be tooted (and afterwards they will be moved to an outbox, please commit them if you would like to keep them.)

### `inbox`

The location of the inbox, a folder of markdown documents which each constitute an individual toot. (If using file based tooting, ignore this.)

### `outbox`

The location of the outbox, a folder to which sent toots will be moved. (If using file based tooting, ignore this.)

### `server`

**Required** Your server's domain name, e.g. `mastodon.social` or `tech.lgbt`

### `toot_length`

Defaults to 500 characters, but you can increase this if your server supports longer toots.

### `token`

**Required** Your access token. You **must** create an "application" yourself to send toots. It only needs:

- write:media
- write:statuses

We recommend naming it "TootIt" after this project to help folks discover it. You can then copy the "access token" to a secret.

### `file`

If you would like to send the contents of a single markdown document, rather than from an 'inbox', just specify the path to the document here.

### `visibility`

If using the file method, this will let you set the visibility of the toot (public, unlisted, private, direct)

## Example usage

```
uses: hexylena/tootit@v1
with:
  server: tech.lgbt
  token: ${{ secrets.access_token }}
  visibility: public
  file: README.md
```

```
uses: hexylena/tootit@v1
with:
  server: tech.lgbt
  token: ${{ secrets.access_token }}
  inbox: comms/inbox/
  outbox: comms/outbox/
  toot_length: 1024
```


## License

AGPL-3.0 or later
