"""
Utility to manage SSH-Tunnel to CINECA clusters.

- To open an SSH-Tunnel to the Leonardo cluster login with the default options:
  $ tunneller -u USER -c leonardo

  This is the same of running: ssh -L 9999:localhost:9999 USER@login01-ext.leonardo.cineca.it -N

- To open a double SSH-Tunnel to the Leonardo compute node lrdn2655 on the port 9998 passing through login02
  $ tunneller -u USER -c leonardo -p 9998 -n lrdn2655

  This is the same of: ssh -L 9998:localhost:9998 USER@login02-ext.leonardo.cineca.it ssh -L 9998:localhost:9998 lrdn2655 -N

- To kill all processes that have network connections on port 9998 on Leonardo cluster login02:
  $ tunneller -u USER -c leonardo -p 9998 -l 2 --port-clean
"""
import os
import subprocess
import argparse
import configparser

import logging

logger = logging.getLogger()

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s SSHFS_PY-%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)


cfg = configparser.ConfigParser()
cfg.read(os.path.join(os.path.dirname(__file__), "cluster.ini"))

cluster_list = cfg.sections()

logger.debug(f"cluster list: {', '.join(cfg.sections())}")


def ssh_command(user, login, port, cluster, node=None):
    """Returns command for SSH-Tunnel"""

    ssh_tunnel = f"ssh -L {port}:localhost:{port} {user}@{login} "

    if node is not None:
        ssh_tunnel = f"{ssh_tunnel} ssh -L {port}:localhost:{port} {node}"
    ssh_tunnel += " -N "

    return ssh_tunnel


def ssh_tunnel(user, login, port, cluster, node=None, dry_run=False):

    ssh_tunnel = ssh_command(user, login, port, cluster, node)

    cmd_jupyter = f"jupyter notebook --port={port} --no-browser"

    header = """
   _                          _ _
  | |_ _   _ _ __  _ __   ___| | | ___ _ __
  | __| | | | '_ \| '_ \ / _ \ | |/ _ \ '__|
  | |_| |_| | | | | | | |  __/ | |  __/ |
   \__|\__,_|_| |_|_| |_|\___|_|_|\___|_|

"""

    print(header)

    if node is None:
        print(
            f"""You want to open a SSH-Tunnel between your LOCAL machine and the LOGIN node ({login}) on {cluster}."""
        )
    else:
        print(
            f"""You want to open a ssh tunnel between your LOCAL machine and the COMPUTE node \"{node}\" on {cluster}."""
        )

    if dry_run:
        print("""You are on remote machine (or in dry-run mode).""")
    else:
        print("""You are on your local machine.""")

    print(
        f'You are using the username "{user}". This should be your username on the {cluster} cluster.'
    )

    jupyter_info = f"""
Step 1. Launch jupyter notebook

On your REMOTE machine run the following command to open a jupyter notebook:
    {cmd_jupyter}

NB: once you have also completed step 2, open a browser on your local machine and copy the URL in the address bar.
    """

    ssh_tunnel_info = f"""
On your LOCAL machine open a SSh-Tunnel with the following command:
    {ssh_tunnel}
    """

    # logger.info(cmd_jupyter)
    # logger.info(ssh_tunnel)

    print(jupyter_info)

    print(
        """
Step 2. Open SSH-Tunnel
    """
    )

    if dry_run:
        print(
            """You are on remote machine (or in dry-run mode), thus following the istructions"""
        )
        print(ssh_tunnel_info)
    else:

        print(
            """You are on your local machine, thus we open the SSH-Tunnel ...
ATTENTION: until the shell hangs, the ssh-tunnel is working
        """
        )
        run(ssh_tunnel, True)
        raise ConnectionError(f"SSH-Tunnel not working")


def login_address(cluster, login=None):
    """Returns address of login cluster"""

    url = cfg[cluster]["url"]
    logger.debug(f"URL for {cluster}: {url}")

    suffix = cfg[cluster]["suffix"]

    login_name = "login"
    if login is not None:
        login_name = f"login{login:02d}{suffix}"

    logger.debug(f"login: {login_name}")

    s = f"{login_name}.{url}"

    logger.debug(f"address: {s}")

    return s


def is_cluster(cluster):
    """Return True if running on the cluster, False otherwise"""
    out = subprocess.check_output(["hostname", "-d"])

    if cfg[cluster]["hostname"] == out.decode().strip():
        return True

    return False


def run(cmd, verbose=False):

    logger.debug(f"RUN: {cmd}")

    if verbose:
        print(f"{cmd}")

    p = subprocess.Popen(
        cmd,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    stdout, stderr = p.communicate()

    return stdout.decode().strip(), stderr.decode().strip()


def ping_address(ip):
    """Ping ip address"""

    stdout, stderr = run(f"ping -c 2 -i 0.2 {ip}")

    if "0 received" in stdout or "Name or service not known" in stderr:
        raise ConnectionError(f"cluster not found: {ip}")
    else:
        logger.debug(f"succesfully ping: {ip}")


def port_list(addr, user, port, cluster):
    """List all open files on the port"""

    cmd = f"lsof -ti:{port}"

    if not is_cluster(cluster):
        cmd = f"ssh {user}@{addr} {cmd}"

    stdout, stderr = run(cmd)

    if stdout:
        logger.info(f"at port {port} found {stdout}")


def port_clean(addr, user, port, cluster):
    """Kills all open files on the port"""

    if is_cluster(cluster):
        cmd = f"lsof -ti:{port} | xargs kill -9"
    else:
        cmd = f"ssh {user}@{addr} lsof -ti:{port} | xargs ssh {user}@{addr} kill -9"

    stdout, stderr = run(cmd)

    if stdout:
        print(stdout)


def main():

    parser = argparse.ArgumentParser(
        prog="tunneller",
        description=__doc__,
        formatter_class=argparse.RawTextHelpFormatter,
    )

    parser.add_argument(
        "--version",
        action="version",
        version="0.1.6",
        help="print version and exit",
    )

    group_cluster = parser.add_argument_group("Cluster options")

    group_cluster.add_argument(
        "-u",
        "--user",
        default=os.environ["USER"],
        help="user name on the cluster. (default %(default)s)",
    )

    group_cluster.add_argument(
        "-c",
        "--cluster",
        choices=cluster_list,
        default=cluster_list[0],
        help="cluster to use. (default %(default)s)",
    )

    group_cluster.add_argument(
        "-l",
        "--login",
        dest="login",
        default=1,
        type=int,
        help="login ID to use. (default %(default)s)",
    )

    group_cluster.add_argument(
        "-n",
        "--node",
        dest="compute",
        default=None,
        help="compute node. (default %(default)s)",
    )

    group_port = parser.add_argument_group("Port options")

    group_port.add_argument(
        "-p",
        "--port",
        default=9999,
        help="port to use for SSH-Tunnel. (default %(default)s)",
    )

    group_port.add_argument(
        "--port-list",
        action="store_true",
        help="list all processes IDs that have network connections on the current port. To check if a port is already in use",
    )

    group_port.add_argument(
        "--port-clean",
        action="store_true",
        help="kill all processes that have network connections on the current port",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="dry-run mode. Do not execute SSH-Tunnel (default %(default)s)",
    )

    parser.add_argument(
        "-v", "--verbose", action="count", default=0, help="increase verbosity level"
    )

    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    logger.debug(args)

    logger.debug(f"select cluster: {args.cluster}")

    login = login_address(args.cluster, args.login)

    dry_run = args.dry_run

    if not dry_run:
        dry_run = is_cluster(args.cluster)
        if dry_run:
            logger.debug(f"enabling dry_run mode on {args.cluster}")

    # if not dry_run:
    #    ping_address(login)

    if args.port_list:
        port_list(login, args.user, args.port, args.cluster)
        return

    if args.port_clean:
        port_clean(login, args.user, args.port, args.cluster)
        return

    ssh_tunnel(args.user, login, args.port, args.cluster, args.compute, dry_run)


if __name__ == "__main__":
    main()
