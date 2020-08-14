import nebula
from nx.connection import DB
from nx.objects import Asset
from nxtools.logging import logging
from nebula import ARCHIVED
import json
import os
import os.path
import sys
import time

def adcouncil(asset):
  asset_path = asset["path"]
  full_path = asset.file_path
  logging.debug("asset '%s' looking for metadata at '%s'" % (asset_path, full_path+".json"))
  if asset_path.startswith("FOR_CHANNEL_HD/PSAs/") and os.path.exists(full_path+".json"):
    asset["commercial/client"] = "adcouncil"
    asset["mark_in"] = 10
    psa = json.loads(open(full_path+".json").read())
    asset["title/original"] = asset["title"]
    asset["title"] = psa["asset"]["title"]
    asset["date/valid"] = time.mktime(time.strptime(psa["asset"]["dateExpiry"], "%m-%d-%Y"))
    asset["language"] = {'English': 'en', 'Spanish': 'es'}.get(psa['asset']['language'])
    asset["commercial/campaign"] = psa['group']['campaign-name']
    duration = int(psa['asset']['length'][1:])
    asset["mark_out"] = asset["mark_in"] + duration
    if asset["language"] == 'en':
      asset["id_folder"] = 9
    elif asset["language"] == 'es':
      asset["status"] = ARCHIVED
    playout_path = os.path.join(os.path.dirname(full_path.replace("/PSAs/", "/PSAs/.playout/")), "%s.mp4" % psa['asset']['adId'])
    if os.path.exists(playout_path):
      asset.save(set_mtime=False)
      try:
        os.remove(asset.get_playout_full_path(1))
      except FileNotFoundError:
        pass
      os.link(playout_path, asset.get_playout_full_path(1))

def main(asset_ids):
  for asset_id in asset_ids:
    a = Asset(asset_id)
    adcouncil(a)
    a.save()

if __name__ == '__main__':
  main(int(a) for a in sys.argv[1:])
