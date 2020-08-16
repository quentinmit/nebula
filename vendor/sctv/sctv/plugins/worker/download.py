import nebula
from nebula import s2words, RESTART, ABORTED, RETRIEVING
from nx.action_service import ActionService
from nxtools.logging import logging
from services.conv.common import temp_file

import os
import time
import requests

COPY_BUFSIZE = 16*1024

class Plugin(ActionService):
    service_type = "download"

    def __init__(self, service):
        self.service = service
        self.id_service = service.id_service

    def process_job(self, job):
        asset = job.asset
        action = job.action

        job_start_time = last_info_time = time.time()

        url = asset["source/url"]

        asset["status"] = RETRIEVING
        asset.save()

        length = asset.get("file/size")

        temp = temp_file(asset["id_storage"], None)

        with requests.get(url, stream=True) as r:
            if 'content-length' in r.headers:
                length = int(r.headers['content-length'])
            try:
                with open(temp, 'wb') as f:
                    i = 0
                    last_now = None
                    while True:
                        buf = r.raw.read(COPY_BUFSIZE)
                        if not buf:
                            break
                        i += len(buf)
                        f.write(buf)
                        now = int(time.time())
                        if now != last_now and now % 2 == 0:
                            last_now = now
                            if length:
                                job.set_progress(int(100 * i / length), "Downloaded %d of %d bytes" % (i, length))
                            else:
                                job.set_progress(50, "Downloaded %d of unknown bytes" % (i,))
                            stat = job.get_status()
                            if stat == RESTART:
                                job.restart()
                                return
                            elif stat == ABORTED:
                                job.abort()
                                return
                os.rename(temp, asset.file_path)
            finally:
                try:
                    os.unlink(temp)
                except OSError:
                    pass

        elapsed_time = time.time() - job_start_time
        speed = i / elapsed_time / 1024

        job.done("Finished in {} ({:.02f} KBps)".format(s2words(elapsed_time), speed))
