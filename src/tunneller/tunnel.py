import os
import subprocess
import argparse
import configparser

import logging

logger = logging.getLogger()

logging.basicConfig(
    level=logging.INFO,
    # level=logging.DEBUG,
    format="[%(asctime)s SSHFS_PY-%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)


cfg = configparser.ConfigParser()
cfg.read(os.path.join(os.path.dirname(__file__), "cluster.ini"))

cluster_list = cfg.sections()

logger.debug(f"cluster list: {', '.join(cfg.sections())}")


def ssh_command(user, login, port, cluster, node=None):

    ssh_tunnel = f"ssh -L {port}:localhost:{port} {user}@{login} "

    if node is not None:
        ssh_tunnel = f"{ssh_tunnel} ssh -L {port}:localhost:{port} {node}"
    ssh_tunnel += " -N "
    return ssh_tunnel


def ssh_tunnel(user, login, port, cluster, node=None, dry_run=False):

    ssh_tunnel = ssh_command(user, login, port, cluster, node)

    cmd_jupyter = f"jupyter notebook --port={port} --no-browser"

    if node is None:
        print(f"""
You want to open a ssh tunnel between your local machine and the LOGIN node ({login}) on {cluster}
        """)
    else:
        print(f"""
You want to open a ssh tunnel between your local machine and the COMPUTE node \"{node}\" on {cluster}
        """)

    jupyter_info = f"""
    On your remote machine run:
    {cmd_jupyter}
    """

    ssh_tunnel_info = f"""
    On your local machine run:
    {ssh_tunnel}
    """

    #logger.info(cmd_jupyter)
    #logger.info(ssh_tunnel)

    print(jupyter_info)

    if dry_run:
        print("""
You are on remote machine (or in dry-run mode)
        """)
        print(ssh_tunnel_info)

    else:

        print("""
You are on your local machine, opening tunnel ...
ATTENTION: until the shell hangs, the ssh-tunnel is working
        """)
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


def list_port(addr, user, port, cluster):

    if is_cluster(cluster):
        cmd = f"lsof -ti:{port}"
    else:
        cmd = f"ssh {user}@{addr} lsof -ti:{port}"

    stdout, stderr = run(cmd)

    if stdout:
        logger.info(f"at port {port} found {stdout}")


def clean_port(addr, user, port, cluster):

    if is_cluster(cluster):
        cmd = f"lsof -ti:{port} | xargs kill -9"
    else:
        cmd = f"ssh {user}@{addr} lsof -ti:{port} | xargs ssh {user}@{addr} kill -9"

    stdout, stderr = run(cmd)

    if stdout:
        print(stdout)


def main():

    parser = argparse.ArgumentParser(
        prog="ssh-tunnel",
        description=__doc__,
        formatter_class=argparse.RawTextHelpFormatter,
    )

    parser.add_argument(
        "--version",
        action="version",
        version="0.0.0",
        help="version",
    )

    parser.add_argument(
        "-v", "--verbose", action="count", default=0, help="increase verbosity"
    )

    parser.add_argument(
        "-l",
        "--login",
        dest="login",
        default=1,
        type=int,
        help="login. (default %(default)s)",
    )
    parser.add_argument(
        "-n",
        "--node",
        dest="compute",
        default=None,
        help="compute node. (default %(default)s)",
    )

    parser.add_argument(
        "-c",
        "--cluster",
        choices=cluster_list,
        default=cluster_list[0],
        help="cluster. (default %(default)s)",
    )
    parser.add_argument(
        "-p", "--port", default=9999, help="port. (default %(default)s)"
    )
    parser.add_argument(
        "-u", "--user", default=os.environ["USER"], help="user. (default %(default)s)"
    )

    parser.add_argument(
        "--clean-port", action="store_true", help="clean port. (default %(default)s)"
    )

    parser.add_argument(
        "--list-port", action="store_true", help="list port. (default %(default)s)"
    )

    parser.add_argument(
        "--dry-run", action="store_true", help="dry-run mode. (default %(default)s)"
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

    #if not dry_run:
    #    ping_address(login)

    if args.list_port:
        list_port(login, args.user, args.port, args.cluster)
        return

    if args.clean_port:
        clean_port(login, args.user, args.port, args.cluster)
        return

    ssh_tunnel(args.user, login, args.port, args.cluster, args.compute, dry_run)


if __name__ == "__main__":
    main()
