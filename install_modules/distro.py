#!/bin/python3

import argparse
import os
import shutil
import tarfile
from functools import reduce
from itertools import groupby
from pathlib import Path
from tempfile import TemporaryFile

import yaml

parsedModules = []
temp_files = {}


class DistroException(Exception):
    pass


class OSConfig:
    def __init__(self, name, package_install_command, package_update_command):
        self.name = name
        self.package_install_command = package_install_command
        self.package_update_command = package_update_command


class ModuleParser:
    def __init__(self, yaml_file: str, module, osConfig: OSConfig, module_paths: dict, input_path: str, output_path: str):
        self.yaml_file = yaml_file
        self.osConfig = osConfig
        self.module_paths = module_paths
        self.input_path = input_path
        self.output_path = output_path
        self.module = module

    def parse(self):
        if not os.path.basename(self.yaml_file) in parsedModules:
            if self.module.get(self.osConfig.name):
                self._parseDependencies()
                self._parseOSModule()
                parsedModules.append(os.path.basename(self.yaml_file))
            else:
                raise DistroException(
                    f"Module config for '{self.osConfig.name()}' not defined in {self.yaml_file}")

    def _parseDependencies(self):
        dependencies = self._getParameter(self.osConfig.name, 'dependencies')
        if dependencies:
            for dependency in dependencies:
                if self.module_paths.get(dependency):
                    ModuleParser(
                        dependency, self.module_paths[dependency], self.osConfig, self.module_paths, self.input_path, self.output_path).parse()
                else:
                    raise DistroException(
                        f"Could not find dependency '{dependency}' in {self.yaml_file}")

    def _parseOSModule(self):
        self._copyFiles()
        self._parseInstallConfig('pre-install')
        self._parsePackageInstall()
        self._parseInstallConfig('post-install')

    def _parsePackageInstall(self):
        if self.module[self.osConfig.name].get('install'):
            priority = self._getPriority('install')
            stage = self._getStage('install')
            temp_file = self._getTempFile(
                stage, 'install', priority, self.osConfig.package_install_command)

            packages = self._getParameter(
                self.osConfig.name, 'install', 'packages')
            if packages:
                if isinstance(packages, list):
                    packages = reduce(lambda a, b: f'{a} {b}', packages)

                temp_file.write(f" {packages}".encode('utf-8'))

    def _parseInstallConfig(self, step):
        if self.module[self.osConfig.name].get(step):
            priority = self._getPriority(step)
            stage = self._getStage(step)
            temp_file = self._getTempFile(stage, step, priority)

            self._addComment(temp_file, step, priority)
            self._addEcho(temp_file, step)
            self._addCommand(temp_file, step)
            self._addScript(temp_file, step)

    def _getTempFile(self, stage, step, priority, package_install_command=None):
        if temp_files.get((stage, step, priority)):
            return temp_files[(stage, step, priority)]
        else:
            temp = TemporaryFile()
            if step == 'install':
                self._addComment(temp, step, priority)
                temp.write(package_install_command.encode('utf-8'))

            temp_files[(stage, step, priority)] = temp
            return temp

    def _getParameter(self, *args, **kwargs):
        parameter = self.module
        for arg in args:
            if isinstance(parameter, dict) and parameter.get(arg):
                parameter = parameter[arg]
            else:
                parameter = None
                break

        if not parameter == None:
            return parameter
        elif self.module[args[0]].get('inherit'):
            return self._getParameter(self.module[self.osConfig.name]['inherit'], *args[1:])
        else:
            return None

    def _getPriority(self, step):
        priority = self._getParameter(self.osConfig.name, step, 'priority')

        if not priority:
            priority = self._getParameter(self.osConfig.name, 'priority')

        if not priority:
            priority = 10

        return priority

    def _getStage(self, step):
        stage = self._getParameter(self.osConfig.name, step, 'stage')

        if not stage:
            stage = self._getParameter(self.osConfig.name, 'stage')

        if not stage:
            stage = f'{self.osConfig.name}-install.sh'

        return stage

    def _addComment(self, file, step, priority):
        if step == 'install':
            file.write(
                f"# Package install (priority: {priority})\n".encode('utf-8'))
        else:
            file.write(
                f"\n# {os.path.splitext(os.path.basename(self.yaml_file))[0]} {step} (priority: {priority})\n".encode('utf-8'))

    def _addEcho(self, file, step):
        echo = self._getParameter(self.osConfig.name, step, 'echo')
        if echo:
            file.write(f'echo "{echo}"\n'.encode('utf-8'))

    def _addCommand(self, file, step):
        command = self._getParameter(self.osConfig.name, step, 'command')
        if command:
            file.write(f'{command.strip()}\n'.encode('utf-8'))

    def _addScript(self, file, step):
        script = self._getParameter(self.osConfig.name, step, 'script')
        if script:
            with open(os.path.expanduser(script), 'r') as f:
                script_lines = f.read()
                file.write(f"\n# {os.path.basename(script)}\n".encode('utf-8'))
                file.write(f"{script_lines}\n".encode('utf-8'))

    def _copyFiles(self):
        files = self._getParameter(self.osConfig.name, 'files')
        if files:
            for file in files:
                file = os.path.expanduser(file)
                if os.path.exists(file):
                    if os.path.isdir(file):
                        shutil.copytree(
                            file, f'{self.output_path}/{os.path.basename(file)}', symlinks=True)
                    else:
                        shutil.copy2(
                            file, f'{self.output_path}/{os.path.basename(file)}')
                else:
                    raise DistroException(
                        f"'{file}' does not exist. In module {self.yaml_file}")


def filePrecedence(tup):
    if tup[1] == 'pre-install':
        return 3 * tup[2]
    elif tup[1] == 'install':
        return 3 * tup[2] + 1
    else:
        return 3 * tup[2] + 2


def combineFiles(output_dir, osConfig: OSConfig):
    for file_name, files in groupby(temp_files, lambda file_name: file_name[0]):
        with open(f'{output_dir}/{file_name}', 'w') as f:
            f.write(
                f"# Update packages\n{osConfig.package_update_command}\n\n")
            files = sorted(list(files), key=filePrecedence)
            for i, file in enumerate(files):
                temp = temp_files.get(file)
                temp.seek(0)
                f.write(temp.read().decode())

                if i < len(files) - 1:
                    f.write('\n')

        os.chmod(f'{output_dir}/{file_name}', 0o775)


def cleanTempFiles():
    for file in temp_files.values():
        file.close()


def readYAML(path):
    try:
        stream = open(os.path.expanduser(path), 'r')
        return yaml.load(stream, Loader=yaml.FullLoader)
    except:
        raise DistroException(
            f"Could not find file {path}")


parser = argparse.ArgumentParser()

parser.add_argument(
    '--os', choices=['debian', 'arch', 'fedora', 'macos'], help='Operating system to generate install script for', required=True)
parser.add_argument('-p', '--path', type=str, default='./',
                    help='Relative path to look for module files')
parser.add_argument('-m', '--modules', type=str,
                    help="List of modules to include in install script")
parser.add_argument('-o', '--output', type=str, default='./build/',
                    help='Directory to output script(s) and file dependencies')
parser.add_argument(
    '-t', '--tar', type=str, help='Create a tarball of install script(s) and file dependencies with argument as name of the tarball')

supported_os = {
    'debian': OSConfig('debian', 'sudo apt install -y', 'sudo apt update -y && sudo apt upgrade -y'),
    'arch':   OSConfig('arch', 'sudo pacman -S', 'sudo pacman -Syyu'),
    'fedora': OSConfig('fedora', 'sudo dnf install -y', 'sudo dnf update -y'),
    'macos':  OSConfig('macos', 'brew install', 'brew update')
}

if __name__ == '__main__':
    try:
        args = parser.parse_args()

        yaml_files = dict(filter(lambda yaml: not yaml[1].get(args.os) == None, map(lambda file: (os.path.basename(
            file), readYAML(file)), Path(args.path).rglob('*.yml'))))

        if args.modules:
            modules = args.modules.split(' ')
        else:
            print(f"Modules found in path: '{args.path}'")
            print(reduce(lambda a, b: f'{a}\n{b}',
                  list(yaml_files)[1:], list(yaml_files)[0]))
            modules = input(
                'Enter modules seperated by spaces (enter for all): ')

            if modules == '':
                modules = reduce(
                    lambda a, b: f'{a} {b}', yaml_files).split(' ')
            else:
                modules = modules.split(' ')

        for module in modules:
            if not yaml_files.get(module) or not yaml_files[module].get(args.os):
                raise DistroException(
                    f"'{module}' is not a valid yaml configuration file for {args.os}")

        if not os.path.isdir(args.output):
            os.mkdir(args.output)

        for module in modules:
            ModuleParser(
                module, yaml_files[module], supported_os[args.os], yaml_files, args.path, args.output).parse()

        combineFiles(args.output, supported_os[args.os])

        if args.tar:
            with tarfile.open(f"{os.path.dirname(os.path.expanduser(args.output))}/{args.tar}.tar.gz", "w:gz") as tar:
                tar.add(args.output, arcname=os.path.basename(args.output))
    except DistroException as e:
        print(e)
    finally:
        cleanTempFiles()
