# FluentBatch
FluentBatch is an automatic tool to generate Fluent journal files and submit jobs to clusters through pbs. It can automatically generate journal files for one case using different boundary conditions. Therefore, it is highly efficient in dealing with parametric studies.

### Usage
First, prepare a journal template.
``` sh
# A journal template looks like below.
$ cat template.jou
/file/read-case "{CaseFile}" no
;; Boundary condition settings
;; Solver configuration
/solve/initialize/initialize-flow
/solve/iterate {Niters}
/file/write-data {DatFile}
```

Second, prepare a series of boundary conditions to be batched in json.
``` sh
# A boundary condition json file looks like below.
$ cat bc.json
[{'CaseFile': 'test1.cas', 'Niters': 3000, 'DatFile': 'test1-3000.dat', ...}, 
{'CaseFile': 'test1.cas', 'Niters': 3000, 'DatFile': 'test1-3000.dat', ...}]
```

Then leave 'almost' everything to the script.
``` sh
# Autoscript can be defined as below.
$ cat go.py
import sys
from ezFluent import *
template = sys.argv[1]
BC = sys.argv[2]
Ncores = int(sys.argv[3])
SimSlave = batch(template, BC)
SimSlave.main(cores=Ncores)
```

Finally, tell your batcher the job number given by pbs and wait for the jobs to be finished and killed.
``` sh
# Automate the batch simulation using template.jou as the journal template and BC.json as the boundary conditions with 24 cores
$ python go.py ./template.jou ./BC.json 24
111.GXM
Enter the queue number for <jobname> : 111
```
