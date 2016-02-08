# -*- coding: utf-8 -*-
import sys
import time
from mql import mql
data_dir = sys.argv[1]

data_infile = 'mql.txt'
data_outfile = 'results.txt'
data_inpath = '{}/{}'.format(data_dir, data_infile)
data_outpath = '{}/{}'.format(data_dir, data_outfile)

#

class Timestamp(object):
    def __init__(self, log_file=None, verbose=None):
        self.timestamp = time.time()


    def msg(self, msg, newline=True, withtime=True):
        timed_msg = "{:>7} ".format(self._elapsed()) if withtime else ''
        timed_msg += msg
        if newline: timed_msg += "\n"
        sys.stderr.write(timed_msg)
        sys.stderr.flush()

    def reset(self): self.timestamp = time.time()

    def _elapsed(self):
        interval = time.time() - self.timestamp
        if interval < 10: return "{: 2.2f}s".format(interval)
        interval = int(round(interval))
        if interval < 60: return "{:>2d}s".format(interval)
        if interval < 3600: return "{:>2d}m {:>02d}s".format(interval // 60, interval % 60)
        return "{:>2d}h {:>02d}m {:>02d}s".format(interval // 3600, (interval % 3600) // 60, interval % 60)

print 'Reading data from {}'.format(data_inpath)

def count_monads(rows):
    covered = set()
    for (b,e) in rows: covered |= set(xrange(b, e+1))
    return len(covered)

text = ''
with open(data_inpath) as dp:
    text = dp.read()
items = text.split('\n==========\n')

nq = 0
resultdata = {}
alltime = Timestamp()

for item in items:
    if item == '': continue
    (mqlbody, qinfo, idstr) = item.split('\n----------\n')
    ids = idstr.split(',')
    (qid, qname) = qinfo.split('..........')
    nq += 1
    alltime.msg('{:>3} qid={:>3} {:<30} ...'.format(nq, qid, qname[0:29]), newline=False)
    thistime = Timestamp()
    (good, nresults, xmonads) = mql('4', mqlbody)
    if good:
        nresultmonads = count_monads(xmonads)
        for id in ids:
            resultdata[id] = (nresults, nresultmonads)
        thistime.msg('OK - {} - {}'.format(nresults, nresultmonads))
    else:
        sys.stdout.write('ERROR\n')
alltime.msg('Done')


with open(data_outpath, 'w') as dp:
    for id in sorted(resultdata):
        dp.write(u'{}\t{}\t{}\n'.format(id, resultdata[id][0], resultdata[id][1]))

print 'Written data to {}'.format(data_outpath)
