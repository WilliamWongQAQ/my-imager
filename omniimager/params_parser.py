import argparse

parser = argparse.ArgumentParser(description='clone and manipulate git repositories')
parser.add_argument('--package-list', metavar='<package_list>',
                    dest='package_list', required=True,
                    help='Input file including information like package lists and target version.')
parser.add_argument('--config-file', metavar='<config_file>',
                    dest='config_file', required=True,
                    help='Configuration file for the software, including working dir, number of workers etc.')
parser.add_argument('--build-type', metavar='<config_file>',
                    dest='build_type', required=True,
                    help='Specify the build type, should be one of: vhd, livecd-iso, installer-iso')
parser.add_argument('--output-file', metavar='image-name', dest='output_file', const='openEuler-image.iso',
                    nargs='?', type=str, default="openEuler-image.iso",
                    help="Specify the name of the build image")