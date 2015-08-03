from ansible import utils, errors
import boto.ec2
import os
import sys
import time
import pickle

# region/stack/param
class LookupModule(object):
  def __init__(self, basedir=None, **kwargs):
    self.basedir = basedir
    self.cache_dir = os.path.join(os.environ['HOME'],'.get_azs')
    self.cache_time = 60

  def check_cache(self, file):
    now = int(time.time())
    data = ''
    if os.path.isfile(file):
      # check time stamp of file
      if ( now - int(os.path.getmtime(file)) ) < self.cache_time:
        fh = open(file, 'r')
        data = pickle.load(fh)

    return data

  def get_regions(self):
    regions_cache = os.path.join(self.cache_dir, 'regions')
    regions = self.check_cache(regions_cache)
    if regions:
      pass
    else:
      try:
        regions = boto.ec2.regions()
        regions = [ r.name for r in regions ]
        fh = open(regions_cache, 'w')
        pickle.dump(regions, fh)
      except:
        raise errors.AnsibleError('Couldn\'t retrieve aws regions')

    return regions

  def _get_azs(self, region):
    az_cache = os.path.join(self.cache_dir, region + '-' + 'azs')
    azs = self.check_cache(az_cache)
    if azs:
      pass
    else:
      conn = boto.ec2.connect_to_region(region)
      azs = [ az.name for az in conn.get_all_zones() ]
      try:
        fh = open(az_cache, 'w')
        pickle.dump(azs, fh)
      except:
        azs = ''

    return azs

  def run(self, terms=None, inject=None, **kwargs):
    if not os.path.isdir(self.cache_dir):
      os.mkdir(self.cache_dir)

    regions = self.get_regions()

    if terms:
      if terms in regions:
        region = terms
      else:
        raise errors.AnsibleError('%s is not a valid aws region' % terms)

    else:
      if 'AWS_REGION' in os.environ:
        region = os.environ['AWS_REGION']
        if not region in regions:
          raise errors.AnsibleError('%s is not a valid aws region' % region)
      else:
        raise errors.AnsibleError('aws region not found in argument or AWS_REGION env var')

    azs = []
    azs = self._get_azs(region)

    if len(azs) == 0:
      raise errors.AnsibleError('Nothing was retured by lookup')

    return azs
