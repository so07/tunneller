# SSH-Tunnels maker aka `tunneller`

Utility to manage SSH-Tunnel to CINECA clusters.

An SSH tunnel is a secure method for forwarding network traffic between two devices over an encrypted connection.

## Usage

- To open an SSH-Tunel to Leonardo cluster login node with the default options:
```
tunneller -c leonardo
```
**NB1**: the $USER environment variable is used to setup the username  
**NB2**: This is the same of running: `ssh -L 9999:localhost:9999 $USER@login01-ext.leonardo.cineca.it -N`

- To open an SSH-Tunnel to the Leonardo cluster login using a different username:
```
tunneller -u USERNAME -c leonardo
```
This is the same of running: `ssh -L 9999:localhost:9999 USERNAME@login01-ext.leonardo.cineca.it -N`

- To open a double SSH-Tunnel to the Leonardo compute node `lrdn2655` on the port 9998 passing through `login02`
```
tunneller -c leonardo -p 9998 -n lrdn2655
```
This is the same of: `ssh -L 9998:localhost:9998 $USER@login02-ext.leonardo.cineca.it ssh -L 9998:localhost:9998 lrdn2655 -N`

- To list all processes IDs that have network connections on port 9999 on Leonardo login node:
```
tunneller -c leonardo -p 9999 --port-list
```
This is the same of running `lsof -ti:9999` on the login node of Leonardo cluster or running `ssh $USER@login01-ext.leonardo.cineca.it lsof -ti:9999` on your local machine.

- To kill all processes that have network connections on port 9998 on Leonardo cluster `login02`:
```
tunneller -c leonardo -p 9998 -l 2 --port-clean
```
This is the same of running `lsof -ti:9999 | xarg kill -9` on the login node of Leonardo cluster.
