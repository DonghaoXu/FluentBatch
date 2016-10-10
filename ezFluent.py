import json
from subprocess import call
import os
import time

PBS_TEMPLATE = '''
#!/bin/bash
### Job name
#PBS -N {jobname}
### Error and output file
#PBS -j oe
### Queue name
#PBS -q workq
### Number of nodes
#PBS -l nodes={nodes}:ppn={ppn}
### Walltime
#PBS -l walltime={walltime}

cd $PBS_O_WORKDIR

echo Running on host `hostname` > {log}
echo Time is `date` >> {log}
echo Directory is `pwd` >> {log}
echo This jobs runs on the following processors: >> {log}
echo `cat $PBS_NODEFILE` >> {log}

# Use following line to specify MPI for message-passing instead
NCORES=`wc -l $PBS_NODEFILE |awk '{print $1}'`

/data/ansys161/v161/fluent/bin/fluent {version} -ssh -t$NCORES -cnf=$PBS_NODEFILE -g -i {journal} >> {log}

exit
'''

class batch:
	def __init__(self, template, BC):
		self.template = template
		self.BC = BC
		self.joufiles = []
		self._queue = dict()
		self.__done = dict()

	def get_template(self):
		with open(self.template, 'r') as f:
			return f.read()

	def get_BC(self):
		with open(self.BC, 'r') as f:
			return json.load(f)

	def make_journal(self, joufiles=None, predix=None):
		if predix is None:
			predix = 'EzJ'
		template = self.get_template()
		BCs = self.get_BC()
		# Autonaming if joufiles is None
		if joufiles is None:
			joufiles = [predix + '-' + str(i) + '.jou' for i in range(len(BCs))]
		else:
			assert len(BCs) == len(joufiles)
		# Write journal files
		for BC, joufile in zip(BCs, joufiles):
			jou = template.format(**BC)
			with open(joufile, 'w') as f:
				f.write(jou)
		self.joufiles = joufiles

	def make_pbs(self, cores=8):
		for joufile in self.joufiles:
			jobname = joufile.strip('.jou')
			if cores <= 48:
				nodes = 1
				ppn = cores
			else:
				nodes = (cores - 1) / 48 + 1
				ppn = (cores - 1) / nodes + 1

			config = {
				'jobname': jobname,
				'nodes': nodes,
				'ppn': ppn,
				'walltime': '24:00:00',
				'log': jobname + '.log',
				'version': '3ddp',
				'journal': joufile,
				'print $1': '{print $1}'
			}
			with open(jobname + '.pbs', 'w') as f:
				pbs = PBS_TEMPLATE.format(**config)
				f.write(pbs)

	def execute(self, joufile, number=None):
		jobname = joufile.strip('.jou')
		call(['echo', 'submitting', jobname])
		call(['qsub', jobname + '.pbs'])
		if number is None:
			number = raw_input('Enter the queue number for ' + jobname + ':')
		self._queue[joufile] = number
		return int(number)

	def executemany(self, joufiles):
		number = None
		for joufile in joufiles:
			number = self.execute(joufile, number)
			number += 1

	def kill(self, joufile):
		call(['qdel', self._queue[joufile]])
		self.__done[joufile] = self._queue.pop(joufile)

	def killmany(self, joufiles):
		for joufile in joufiles:
			self.kill(joufile)

	def check_state(self, joufile, display=False):
		jobname = joufile.strip('.jou')
		if not os.path.exists(jobname + '.log'):
			return -10
		with open(jobname + '.log', 'r') as f:
			f.seek(-100, os.SEEK_END)
			tail = f.read()
		if display:
			call(['echo', '##########', joufile, '##########'])
			call(['tail', jobname + '.log'])
			call(['echo', ''])
		'''
		0: exit normally
		1: critical error
		2: commands error
		-1: still running or unknown errors
		-10: not started yet
		'''
		if tail.find('Warning: An error or interrupt occurred while reading the journal file.') != -1:
			return 1
		# elif tail.find(''):
		# 	return 2
		elif tail.find('Halting due to end of file on input') != -1:
			return 0
		else:
			return -1

	def autokill(self, display=False, limits=1e+10):
		count = 0
		while count <= limits and len(self._queue) > 0:
			for joufile, _ in self._queue.items():
				flag = self.check_state(joufile, display)
				if flag >= 0:
					call(['echo', joufile, 'exits with flag==' + str(flag)])
					self.kill(joufile)
			# recheck&kill after 1min
			time.sleep(60)
			count += 1

	def main(self, joufiles=None, cores=8, auto=True):
		self.make_journal(joufiles)
		self.make_pbs(cores)
		self.executemany(self.joufiles)
		if auto:
			self.autokill()







