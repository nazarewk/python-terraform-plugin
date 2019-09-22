import os
import shlex
import shutil
import sys
import textwrap
from pathlib import Path
from typing import Collection, Dict

from pip._internal.utils.misc import get_installed_distributions
from pkg_resources import parse_requirements, Requirement, DistInfoDistribution

script_path = Path(__file__).absolute()
repo_dir = script_path.parent
src_dir: Path = repo_dir / 'src'
package_path: Path = src_dir / 'terraform_provider'
requirements_path: Path = repo_dir / 'requirements-dev.txt'
env_path: Path = repo_dir / '.venv'

pip_install_command = ('pip', 'install', '-U', 'pip', 'setuptools', '-r', requirements_path)
self_command = ('python', script_path, *sys.argv[1:])


def main():
    ensure_virtualenv()
    ensure_packages()
    ensure_protobuf()


def ensure_virtualenv():
    os.chdir(repo_dir)
    env_path: Path = repo_dir / '.venv'

    if not env_path.exists():
        info(f'Setting up virtualenv at {env_path}')
        activate_script = env_path / 'bin' / 'activate'
        exec_shell(
            (sys.executable, '-m', 'venv', env_path),
            ('.', activate_script),
            pip_install_command,
            self_command,
        )
    else:
        info(f'virtualenv at {env_path}')


def ensure_packages():
    requirements: Dict[str, Requirement] = {
        req.project_name: req
        for req in parse_requirements(requirements_path.read_text())
    }
    packages: Dict[str, DistInfoDistribution] = {
        pkg.project_name: pkg
        for pkg in get_installed_distributions(local_only=True)
    }

    missing = {
        name
        for name in requirements.keys()
        if name not in packages
    }

    mismatch = {
        name
        for name, req in requirements.items()
        if name not in missing and packages[name].version not in req
    }

    if not missing and not mismatch:
        info('requirements up to date')
        return

    if missing:
        info('missing packages:')
        for name in sorted(missing):
            info(f'- {name}')

    if mismatch:
        info('mismatched packages:')
        for name in sorted(mismatch):
            pkg = packages[name]
            req = requirements[name]
            info(f'- {name} {pkg.version} not in {req}')

    exec_shell(pip_install_command, self_command)


def ensure_protobuf(filename='tfplugin5.1.proto'):
    import requests
    url = f'https://raw.githubusercontent.com/hashicorp/terraform/master/docs/plugin-protocol/{filename}'
    response = requests.get(url)
    response.raise_for_status()

    python_out = package_path
    python_out.mkdir(parents=True, exist_ok=True)
    python_out

    output_filename = Path(filename)
    output_filename = (
            output_filename.stem.replace('.', '') + output_filename.suffix
    )
    proto_path: Path = python_out / output_filename
    proto_path.write_text('\n'.join([
        f'// downloaded from {url}',
        '',
        response.text
    ]))

    from grpc_tools import protoc

    cwd = Path.cwd()
    os.chdir(src_dir)
    protoc_args = [
        f'-I.',
        f'--python_out=.',
        f'--grpc_python_out=.',
        f'{proto_path.relative_to(src_dir)}',
    ]
    gen_mypy = shutil.which('protoc-gen-mypy')
    if gen_mypy:
        protoc_args.insert(1, f'--mypy_out=.')
        protoc_args.insert(1, f'--plugin=protoc-gen-mypy={gen_mypy}')
    info(f'executing: protoc {" ".join(protoc_args)}')
    protoc.main(protoc_args)
    os.chdir(cwd)


def info(*args, **kwargs):
    kwargs.setdefault('file', sys.stderr)
    print(*args, **kwargs)


def sh_quote(s):
    return shlex.quote(str(s))


def exec_shell(*commands: Collection[str]):
    script = '\n'.join(
        ' '.join(map(sh_quote, command))
        for command in commands
    )

    info('Executing:')
    info(textwrap.indent(script, '$ '))
    os.execvp('sh', ['sh', '-c', script])


if __name__ == '__main__':
    main()
