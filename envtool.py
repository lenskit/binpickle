import os
import sys
import tempfile
import subprocess
from pathlib import Path
import platform
import argparse
from poetry.core.factory import Factory


def write_env(obj, out):
    try:
        import yaml
        yaml.safe_dump(obj, out)
    except ImportError:
        import json
        json.dump(obj, out, indent=2)


def parse_args():
    parser = argparse.ArgumentParser(description='Manage development environments.')
    parser.add_argument('--python-version', '-V', metavar='VER',
                        help='use Python version VER')
    parser.add_argument('--extra', '-E', metavar='EXTRA', action='append',
                        help='include EXTRA')
    parser.add_argument('--name', '-n', metavar='NAME',
                        help='name Conda environment NAME')
    parser.add_argument('--no-dev', action='store_true', help='skip dev dependencies')
    parser.add_argument('--save-env', metavar='FILE',
                        help='save environment to FILE')
    parser.add_argument('--create-env', action='store_true',
                        help='create Conda environment')
    parser.add_argument('--update-env', action='store_true',
                        help='update Conda environment')
    args = parser.parse_args()
    return args


def load_project():
    f = Factory()
    return f.create_poetry('.')


def conda_config(project):
    cfg = project.pyproject.get('tool', {})
    cfg = cfg.get('envtool', {})
    return cfg.get('conda', {})


def marker_env(args, project):
    "Get the marker environment"
    pyver = args.python_version
    if not pyver:
        pyver = project.package.python_constraint.min
    if not pyver:
        pyver = platform.python_version()
    return {
        'os_name': os.name,
        'sys_platform': sys.platform,
        'python_version': pyver,
        'platform_python_implementation': platform.python_implementation(),
        'platform_version': platform.version(),
        'platform_machine': platform.machine(),
    }


def req_active(env, req):
    if req.marker:
        return req.marker.validate(env)
    else:
        return True


def dep_str(cfg, req):
    dep = req.name
    map = cfg.get('rename', {})
    dep = str(map.get(dep, dep))
    if not req.constraint.is_any():
        dep += str(req.constraint)
    return dep


def conda_env(args, project):
    pkg = project.package
    cfg = conda_config(project)
    mkenv = marker_env(args, project)
    name = args.name
    if name is None:
        name = cfg.get('name', 'dev-env')

    env = {'name': str(name)}
    channels = cfg.get('channels')
    if channels:
        env['channels'] = [str(c) for c in channels]

    deps = []
    if args.python_version:
        deps.append(f'python={args.python_version}')
    elif pkg.python_constraint:
        deps.append('python' + str(pkg.python_constraint))

    for req in pkg.requires:
        if not req.is_optional() and req_active(mkenv, req):
            deps.append(dep_str(cfg, req))

    if not args.no_dev:
        deps += [dep_str(cfg, r)
                 for r in pkg.dev_requires
                 if req_active(mkenv, r)]

    if args.extra:
        if 'all' in args.extra:
            extras = pkg.extras.keys()
        else:
            extras = args.extra
        for e in extras:
            deps += [dep_str(cfg, r)
                     for r in pkg.extras[e]
                     if req_active(mkenv, r)]

    env['dependencies'] = deps

    return env


def create_env(env):
    from conda.cli.python_api import run_command
    with tempfile.TemporaryDirectory() as td:
        path = Path(td)
        ef = path / 'environment.yml'
        with ef.open('w') as f:
            write_env(env, f)

        run_command('env', 'create', '-f', os.fspath(ef), stdout=None, stderr=None)


def env_command(env, cmd):
    from conda.cli.python_api import run_command
    with tempfile.TemporaryDirectory() as td:
        path = Path(td)
        ef = path / 'environment.yml'
        with ef.open('w') as f:
            write_env(env, f)
        print(cmd, 'environment', ef)
        subprocess.run(['conda', 'env', cmd, '-q', '-f', os.fspath(ef)], check=True)


def main(args):
    project = load_project()
    env = conda_env(args, project)
    if args.save_env:
        with open(save_env, 'w') as ef:
            write_env(env, ef)
    elif args.create_env:
        env_command(env, 'create')
    elif args.update_env:
        env_command(env, 'update')
    else:
        write_env(env, sys.stdout)


if __name__ == '__main__':
    main(parse_args())
