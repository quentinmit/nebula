from nebula import *
from .ffprobe import FFProbe

probes = [
        FFProbe()
    ]

class Service(BaseService):
    def on_init(self):
        self.conds = []
        for cond in self.settings.findall("cond"):
            if cond is None:
                continue
            if not cond.text:
                continue
            exec ("x = lambda asset: {}".format(cond.text))
            self.conds.append(x)

    def on_main(self):
        self.mounted_storages = []
        for id_storage in storages:
            storage_path = storages[id_storage].local_path
            if os.path.exists(storage_path) and len(os.listdir(storage_path)) != 0:
                self.mounted_storages.append(id_storage)

        db = DB()
        # do not scan trashed and archived files
        db.query("SELECT id, meta FROM assets WHERE media_type=%s AND status NOT IN (3, 4)", [FILE])
        for id, meta in db.fetchall():
            asset = Asset(meta=meta, db=db)
            self.process(asset)


    def process(self, asset):
        for cond in self.conds:
            if not cond(asset):
                return False

        full_path = asset.file_path
        if asset["id_storage"] not in self.mounted_storages:
            logging.warning("Skipping unmounted storage {}".format(asset["id_storage"]))
            return

        if not os.path.exists(full_path):
            if asset["status"] in [ONLINE, RESET, CREATING]:
                logging.warning("{}: Turning offline (File does not exist)".format(asset))
                asset["status"] = OFFLINE
                asset.save()
            return

        try:
            fmtime = int(os.path.getmtime(full_path))
            fsize  = int(os.path.getsize(full_path))
        except Exception:
            log_traceback("{}: Unable to get file attributes".format(asset))
            return

        if fsize == 0:
            if asset["status"] != OFFLINE:
                logging.warning("{}: Turning offline (empty file)".format(asset))
                asset["status"] = OFFLINE
                asset.save()
            return

        if fmtime != asset["file/mtime"] or asset["status"] == RESET:
            try:
                f = open(full_path, "rb")
            except Exception:
                logging.debug("{} is not accessible (file creation in progress?)".format(asset))
                return
            else:
                f.seek(0,2)
                fsize = f.tell()
                f.close()

            if asset["status"] == RESET:
                asset.load_sidecar_metadata()

            # Filesize must be changed to update metadata automatically.
            # It sucks, but mtime only condition is.... errr doesn't work always

            if fsize == asset["file/size"] and asset["status"] != RESET:
                logging.debug("{}: File mtime has been changed. Updating.".format(asset))
                asset["file/mtime"] = fmtime
                asset.save(set_mtime=False, notify=False)
            else:
                logging.info("{}: File size changed. Updating.".format(asset))

                keys = list(asset.meta.keys())
                for key in keys:
                    if meta_types[key]["ns"] in ("f", "q"):
                        del (asset.meta[key])

                asset["file/size"]  = fsize
                asset["file/mtime"] = fmtime
                asset["file/ctime"] = int(os.path.getmtime(full_path))

                for probe in probes:
                    if probe.accepts(asset):
                        logging.debug("{}: probing using {}".format(asset, probe))
                        result = probe(asset)
                        if result:
                            asset = result
                        elif asset["status"] != CREATING:
                            asset["status"] = CREATING
                            asset.save()
                            return
                        else:
                            return

                if asset["status"] == RESET:
                    asset["status"] = ONLINE
                    logging.info("{}: Reset completed".format(asset))
                else:
                    asset["status"] = CREATING
                asset.save()

        if asset["status"] == CREATING and asset["mtime"] + 15 > time.time():
            logging.debug("{}: Waiting for completion assurance.".format(asset))
            asset.save(set_mtime=False, notify=False)

        elif asset["status"] in (CREATING, OFFLINE):
            logging.goodnews("{}: Turning online".format(asset))
            asset["status"] = ONLINE
            asset.save()

            db = DB()
            db.query("""
                UPDATE jobs SET
                    status=5,
                    retries=0,
                    creation_time=%s,
                    start_time=NULL,
                    end_time=NULL,
                    message='Restarting after source update'
                WHERE
                    id_asset=%s
                    AND status IN (1,2,3,4)
                RETURNING id
                """,
                    [time.time(), asset.id]

                )
            res = db.fetchall()
            if res:
                logging.info("{}: Changed. Restarting jobs {}".format(asset, ", ".join([str(l[0]) for l in res])))
            db.commit()
