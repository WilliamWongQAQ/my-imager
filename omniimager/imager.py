import argparse
import json
import os
import subprocess
import sys
import time
import yaml
import shutil
import signal

from omniimager import rootfs_worker
from omniimager import installer_maker
from omniimager import iso_worker
from omniimager import pkg_fetcher
from omniimager.log_utils import logger
from omniimager.params_parser import parser
from omniimager.rootfs_worker import make_raw_rootfs

ROOTFS_DIR = 'rootfs'
DNF_COMMAND = 'dnf'

TYPE_VHD = 'vhd'
TYPE_INSTALLER = 'installer-iso'
TYPE_LIVECD = 'livecd-iso'
TYPE_RAW = 'raw'
SUPPORTED_BUILDTYPE = [TYPE_LIVECD, TYPE_INSTALLER, TYPE_VHD, TYPE_RAW]

INITRD_PKG_LIST = [
    "filesystem", "audit", "bash", "ncurses", "ncurses-libs",
    "cronie", "coreutils", "basesystem", "file", "bc", "bash",
    "bzip2", "sed", "procps-ng", "findutils", "gzip", "grep",
    "libtool", "openssl", "pkgconf", "readline", "sed", "sudo",
    "systemd", "util-linux", "bridge-utils", "e2fsprogs",
    "elfutils-libelf", "expat", "setup", "gdbm", "tar",
    "xz", "zlib", "iproute", "dbus", "cpio", "file",
    "procps-ng", "net-tools", "nspr", "lvm2", "firewalld",
    "glibc", "grubby", "hostname", "initscripts", "iprutils",
    "irqbalance", "kbd", "kexec-tools", "less", "openssh",
    "openssh-server", "openssh-clients", "parted", "passwd",
    "policycoreutils", "rng-tools", "rootfiles",
    "selinux-policy-targeted", "sssd", "tuned", "vim-minimal",
    "xfsprogs", "NetworkManager", "NetworkManager-config-server",
    "authselect", "dracut-config-rescue", "kernel-tools", "sysfsutils",
    "linux-firmware", "lshw", "lsscsi", "rsyslog", "security-tool",
    "sg3_utils", "dracut-config-generic", "dracut-network", "rdma-core",
    "selinux-policy-mls", "kernel"
]
REQUIRED_BINARIES = ["createrepo", "dnf", "mkisofs"]


def parse_package_list(list_file):
    if not list_file:
        raise Exception

    with open(list_file, 'r') as inputs:
        input_dict = json.load(inputs)

    package_list = input_dict["packages"]
    return package_list


def clean_up_dir(target_dir):
    if os.path.exists(target_dir):
        shutil.rmtree(target_dir)


def binary_exists(name):
    return False if shutil.which(name) is None else True


def prepare_workspace(config_options):
    work_dir = config_options['working_dir']
    clean_up_dir(work_dir)
    os.makedirs(work_dir)

    verbose = True
    if config_options.get('debug'):
        verbose = False

    # prepare an empty rootfs folder with repo file in place
    rootfs_dir = config_options['working_dir'] + '/' + ROOTFS_DIR
    rootfs_repo_dir = rootfs_dir + '/etc/yum.repos.d'

    repo_file = config_options['repo_file']

    clean_up_dir(rootfs_dir)
    os.makedirs(rootfs_dir)
    os.makedirs(rootfs_repo_dir)
    shutil.copy(repo_file, rootfs_repo_dir)

    logger.debug('Create a clean dir to hold all files required to make iso ...')
    iso_base_dir = work_dir + '/iso'
    os.makedirs(iso_base_dir)

    return rootfs_dir, config_options['working_dir'], iso_base_dir, repo_file, rootfs_repo_dir, verbose


def prepare_raw_workspace(config_options, image_name="test.raw"):
    work_dir = config_options['working_dir']
    clean_up_dir(work_dir)
    os.makedirs(work_dir)
    # prepare an empty rootfs folder with repo file in place
    rootfs_dir = config_options['working_dir'] + '/' + ROOTFS_DIR
    rootfs_repo_dir = rootfs_dir + '/etc/yum.repos.d'

    repo_file = config_options['repo_file']

    clean_up_dir(rootfs_dir)
    os.makedirs(rootfs_dir)
    imager_name = work_dir + '/' + image_name
    subprocess.run('chmod 777 /home/python_projects/my-imager/omniimager/test.sh', shell=True)
    logger.debug('create a virtual image...')
    os.system(f'/home/python_projects/my-imager/omniimager/test.sh {imager_name} {rootfs_dir}')

    os.makedirs(rootfs_repo_dir)
    shutil.copy(repo_file, rootfs_repo_dir)
    return rootfs_dir, work_dir, repo_file, rootfs_repo_dir


def omni_interrupt_handler(signum, frame):
    print('\nKeyboard Interrupted! Cleaning Up and Exit!')
    sys.exit(1)


def main():
    signal.signal(signal.SIGINT, omni_interrupt_handler)
    start_time = time.time()
    # parse config options and args
    parsed_args = parser.parse_args()

    build_type = parsed_args.build_type
    if build_type not in SUPPORTED_BUILDTYPE:
        logger.debug('Unsupported build-type, Stopped ...')
        sys.exit(1)
    else:
        logger.debug(f'Building:{build_type}')

    for command in REQUIRED_BINARIES:
        if not binary_exists(command):
            logger.debug(f'binary not found: {command}')
            sys.exit(1)

    with open(parsed_args.config_file, 'r') as config_file:
        config_options = yaml.load(config_file, Loader=yaml.SafeLoader)

    packages = parse_package_list(parsed_args.package_list)
    user_specified_packages = []
    config_options['auto_login'] = False
    # Installer ISO have different rootfs with other image type
    if build_type == TYPE_INSTALLER:
        user_specified_packages = packages
        packages = INITRD_PKG_LIST
        config_options['auto_login'] = True
        rootfs_dir, work_dir, iso_base, repo_file, rootfs_repo_dir, verbose = prepare_workspace(config_options)
        use_cached = config_options.get('use_cached_rootfs')
        if not use_cached:
            rootfs_worker.make_rootfs(
                rootfs_dir, packages, config_options, repo_file, rootfs_repo_dir, build_type, verbose)

            if build_type == TYPE_INSTALLER:
                installer_maker.install_and_configure_installer(
                    config_options, rootfs_dir, repo_file, rootfs_repo_dir, user_specified_packages)
        else:
            rootfs_worker.unzip_rootfs(work_dir, config_options, repo_file, rootfs_repo_dir, build_type, verbose)
        logger.debug('Compressing rootfs ...')
        rootfs_worker.compress_to_gz(rootfs_dir, work_dir)

        if build_type == TYPE_INSTALLER:
            logger.debug('Downloading RPMs for installer ISO ...')
            rpms_dir = iso_base + '/RPMS'
            os.makedirs(rpms_dir)
            pkg_fetcher.fetch_pkgs(rpms_dir, user_specified_packages, rootfs_dir, verbose=True)
            subprocess.run('createrepo ' + rpms_dir, shell=True)

        iso_worker.make_iso(iso_base, rootfs_dir, parsed_args.output_file)
        logger.debug(f'ISO: openEuler-test.iso generated in: {work_dir}')
    elif build_type == TYPE_RAW:
        rootfs_dir, work_dir, repo_file, rootfs_repo_dir = prepare_raw_workspace(config_options)
        make_raw_rootfs(rootfs_dir, packages, config_options, repo_file, rootfs_repo_dir, build_type)
        imager_name = work_dir + '/' + 'test.raw'
        subprocess.run(f'grub2-install --boot-directory={rootfs_dir} --target=i386-pc --modules=part_msdos  {imager_name}',shell=True)
    end_time = time.time()
    elapsed_time = end_time - start_time
    logger.debug(f'Elapsed time: {elapsed_time} s')
