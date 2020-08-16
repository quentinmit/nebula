import nebula
from nebula import file_types, FILE, OFFLINE
from nx.connection import DB
from nx.objects import Asset
from nx.jobs import send_to
from nxtools.logging import logging
from nx.plugins.worker import WorkerPlugin

import os.path
import time
import feedparser

class Plugin(WorkerPlugin):
    def on_main(self):
        db = DB()

        feeds = self.service.settings.findall("feed")
        for feed in feeds:
            self.fetch_feed(db, feed)

    def fetch_feed(self, db, feed):
        id_storage = int(feed.attrib.get("id_storage", 1))
        id_folder = int(feed.attrib.get("id_folder", 12))
        directory = feed.attrib["directory"]
        send_action = feed.attrib.get("send_action")
        url = feed.attrib["url"]
        logging.debug("Fetching %s" % (url))
        d = feedparser.parse(url)
        for e in d.entries:
            title = e.title
            description = e.description
            pubDate = e.published_parsed
            guid = e.id
            if not e.enclosures:
                continue
            enclosure = e.enclosures[0]
            href = enclosure.href
            length = enclosure.length

            ext = os.path.splitext(href)[1].lstrip(".").lower()
            if ext not in file_types:
                continue

            db.query("SELECT meta FROM assets WHERE meta->>'id/guid' = %s", [guid])
            for meta, in db.fetchall():
                #asset = Asset(db=db, meta=meta)
                #TODO: Update existing asset if size/URL changes
                break
            else:
                now = time.time()
                asset = Asset(db=db)
                asset["content_type"] = file_types[ext]
                asset["media_type"] = FILE
                asset["id_storage"] = id_storage
                asset["id/guid"] = guid
                asset["path"] = os.path.join(directory, os.path.basename(href))
                asset["ctime"] = now
                asset["mtime"] = now
                asset["status"] = OFFLINE
                asset["id_folder"] = id_folder
                asset["title"] = title
                asset["description"] = description
                asset["date"] = time.mktime(pubDate)
                asset["source"] = url
                asset["source/url"] = href
                if length:
                    asset["file/size"] = length
                for meta in feed.findall("meta"):
                    asset[meta.attrib["name"]] = meta.attrib["value"]
                asset.save(set_mtime=False)
                if send_action:
                    result = send_to(
                        asset.id,
                        send_action,
                        restart_existing=True,
                        restart_running=False,
                        db=db,
                    )
                    if result == 201:
                        logging.info("Sending %s to download: %s" % (asset, result.message))
