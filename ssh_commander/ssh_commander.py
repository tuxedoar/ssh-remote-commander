# Copyright 2020 by Tuxedoar <tuxedoar@gmail.com>

# LICENSE

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from ssh_key_helper import get_ssh_homedir_content
from ssh_session import setup_ssh_session_args
from ssh_session import start_ssh_session
from ssh_session import manage_ssh_session
import argparse
import sys
import re
import logging
import concurrent.futures
import coloredlogs
from colorama import init
from _version import __version__


def main():
    """ Setup CLI arguments and multithreading  """
    try:
        # Setup colorful output
        coloredlogs.install(level='INFO', fmt='[%(hostname)s] %(asctime)s %(message)s')
        init(autoreset=True)
        args = menu_handler()
        target_hosts = read_hosts_file(args.FILE)
        if not target_hosts:
            logging.critical("No valid hosts were found. Nothing to do!")
            sys.exit(1)
        nworkers = len(target_hosts)
        cmd = args.COMMANDS
        ssh_session_args = setup_ssh_session_args(args)
    except (KeyboardInterrupt, IOError) as err:
        logging.critical("%s\n", err)
        sys.exit()

    logging.info("[+] Setting up remote sessions with user: %s", args.USER)
    start_multithreaded_sessions(nworkers, target_hosts, ssh_session_args, cmd)


def start_multithreaded_sessions(nworkers, target_hosts, ssh_session_args, cmd):
    """ Start multithreaded SSH sessions on remote hosts """
    with concurrent.futures.ThreadPoolExecutor(max_workers=nworkers) as executor:
        for target_host in target_hosts:
            executor.submit(
                            manage_ssh_session,
                            ssh_session_args,
                            target_host,
                            cmd
                            )
    return None


def menu_handler():
    """ Setup CLI arguments """
    parser = argparse.ArgumentParser(
        description='Excecute commands on several remote hosts, with SSH.')
    parser.add_argument('FILE', help='Plain text file with list of hosts')
    parser.add_argument('USER', help='User to login on remote hosts')
    parser.add_argument('COMMANDS', help='Comma separated commands to be \
                         executed on remote hosts')
    parser.add_argument('-p', '--port', nargs='?', type=int,
                        default=22, help='Specify SSH port to connect to hosts')
    parser.add_argument('-i','--identity_file', help="Public key auth file")
    parser.add_argument('-v', '--version', action='version',
                        version="%(prog)s {version}".format(version=__version__),
                        help='Show current version')
    args = parser.parse_args()
    return args


def validate_ip_addr(ip_addr):
    """ Validate an IP address """
    validate_ip = re.search("^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", ip_addr)
    return bool(validate_ip)


def read_hosts_file(hosts_file):
    """ Read the file and get the IP adresses  """
    remote_hosts = []
    with open(hosts_file, 'r') as file:
        for line in file.readlines():
            ip = line.strip()
            if line and not line.startswith('#'):
                logging.warning("The IP %s is NOT valid. Ignored!", ip) \
                if not validate_ip_addr(ip) else remote_hosts.append(ip)
    return remote_hosts

if __name__ == "__main__":
    main()
