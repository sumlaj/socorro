# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

try:
  import json
except ImportError:
  import simplejson as json

import signal

import socorro.lib.JsonDumpStorage as jds
import socorro.storage.crashstorage as cstore
import socorro.lib.util as sutil
import socorro.lib.iteratorWorkerFramework as iwf


#-------------------------------------------------------------------------------
def move (conf,
          sourceCrashStorageClass=cstore.CrashStorageSystemForLocalFS,
          destCrashStorageClass=cstore.CrashStorageSystemForHBase):
  logger = conf.logger
  crashStoragePoolForSource = cstore.CrashStoragePool(conf, sourceCrashStorageClass)
  crashStoragePoolForDest = cstore.CrashStoragePool(conf, destCrashStorageClass)
  signal.signal(signal.SIGTERM, iwf.respondToSIGTERM)
  signal.signal(signal.SIGHUP, iwf.respondToSIGTERM)

  #-----------------------------------------------------------------------------
  def theIterator():
    """This infinite iterator will walk through the file system storage,
    yielding the ooids of every new entry in the filelsystem.  If there
    are no new entries, it yields None"""
    sourceStorage = crashStoragePoolForSource.crashStorage() # thread local
    try:
      while True:
        i = 0
        for i, ooid in enumerate(sourceStorage.newUuids()):
          yield ooid
        if i == 0:
          yield None
    except KeyboardInterrupt:
      pass
  #-----------------------------------------------------------------------------

  #-----------------------------------------------------------------------------
  def doSubmission(ooidTuple):
    logger.debug('received: %s', str(ooidTuple))
    try:
      sourceStorage = crashStoragePoolForSource.crashStorage()
      destStorage = crashStoragePoolForDest.crashStorage()
      ooid = ooidTuple[0]
      try:
        jsonContents = sourceStorage.get_meta(ooid)
      except ValueError:
        logger.warning('the json for %s is degenerate and cannot be loaded'  \
                       ' - saving empty json', ooid)
        jsonContents = {}
      dumpContents = sourceStorage.get_raw_dump(ooid)
      logger.debug('pushing %s to dest', ooid)
      result = destStorage.save_raw(ooid, jsonContents, dumpContents)
      if result == cstore.CrashStorageSystem.ERROR:
        return iwf.FAILURE
      elif result == cstore.CrashStorageSystem.RETRY:
        return iwf.RETRY
      sourceStorage.quickDelete(ooid)
      return iwf.OK
    except Exception, x:
      sutil.reportExceptionAndContinue(logger)
      return iwf.FAILURE
  #-----------------------------------------------------------------------------

  submissionMill = iwf.IteratorWorkerFramework(conf,
                                               jobSourceIterator=theIterator,
                                               taskFunc=doSubmission,
                                               name='submissionMill')

  try:
    submissionMill.start()
    submissionMill.waitForCompletion() # though, it only ends if someone hits
                                       # ^C or sends SIGHUP or SIGTERM - any of
                                       # which will get translated into a
                                       # KeyboardInterrupt exception
  except KeyboardInterrupt:
    while True:
      try:
        submissionMill.stop()
        break
      except KeyboardInterrupt:
        logger.warning('We heard you the first time.  There is no need for '
                       'further keyboard or signal interrupts.  We are '
                       'waiting for the worker threads to stop.  If this app '
                       'does not halt soon, you may have to send SIGKILL '
                       '(kill -9)')



