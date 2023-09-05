# SSh-Tunnel maker aka `tunneller`

Utility to manage SSH-Tunnel to CINECA clusters.


## Usage


- To open an SSH-Tunnel to the Leonardo cluster login with the default options:
```
tunneller -u USER -c leonardo
```
This is the same of running: `ssh -L 9999:localhost:9999 USER@login01-ext.leonardo.cineca.it -N`

- To open a double SSH-Tunnel to the Leonardo compute node lrdn2655 on the port 9998 passing through login 02
```
tunneller -u USER -c leonardo -p 9998 -n lrdn2655
```
This is the same of: `ssh -L 9998:localhost:9998 sorland2@login02-ext.leonardo.cineca.it ssh -L 9998:localhost:9998 lrdn2655 -N`

- To clean of opened files related to port 9998 on Leonardo cluster login 02:
```
tunneller -u USER -c leonardo -p 9998 -l 2 --port-clean
```

