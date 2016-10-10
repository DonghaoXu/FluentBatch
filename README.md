# FluentBatch
An automatic tool to generate Fluent journal files and submit jobs to clusters through pbs. 

### Usage
First, prepare a journal template and a boundary condition file.
``` sh
$ cat template.jou
/file/read-case "{CaseFile}" no
/solve/initialize/initialize-flow
/solve/iterate {Niters}
/file/write-data {DatFile}
```
