"""
Handles installation of problems onto the shell server(s).

When a problem is _installed_, this means that the problem source files have
been parsed and converted into a debian package stored at
HACKSPORTS_ROOT/shared/debs.

Additionally, the source files of the problem will be copied (via the debian
package) into HACKSPORTS_ROOT/shared/sources.

The problem will then appear in the list of available problems, which is
determined by traversing the HACKSPORTS_ROOT/shared/sources directory.

When this problem is _deployed_, shell_manager will attempt to reinstall the
debian package first, in case the problem has dependencies that have not
been fulfilled on the current shell server.
"""
import logging
import subprocess
import os
import shutil
from shell_manager.package import package_problem
from shell_manager.util import get_problem, DEB_ROOT, FatalException, join, HACKSPORTS_ROOT, get_problem_root_hashed, get_bundle2, PROBLEM_ROOT, BUNDLE_ROOT, sanitize_name
from hacksport.deploy import generate_staging_directory

logger = logging.getLogger(__name__)


def install_problem(problem_path):
    """
    Install a problem from a source directory.

    Args:
        problem_path: path to the problem source directory
    """
    lock_file = join(HACKSPORTS_ROOT, "deploy.lock")
    if os.path.isfile(lock_file):
        logger.error(
            "Another problem installation or deployment appears in progress. If you believe this to be an error, "
            "run 'shell_manager clean'")
        raise FatalException

    problem_obj = get_problem(problem_path)
    if os.path.isdir(get_problem_root_hashed(problem_obj, absolute=True)):
        logger.error(f"Problem {problem_obj['unique_name']} is already installed")
        raise FatalException
    logger.info(f"Installing problem {problem_obj['unique_name']}...")

    logger.debug(f"{problem_obj['unique_name']}: obtained lock file ({str(lock_file)})")
    with open(lock_file, "w") as f:
        f.write("1")

    staging_dir_path = generate_staging_directory(
        problem_name=problem_obj['unique_name'])
    logger.debug(f"{problem_obj['unique_name']}: created staging directory" +
                 f" ({staging_dir_path})")

    generated_deb_path = package_problem(
        problem_path, staging_path=staging_dir_path, out_path=DEB_ROOT)
    logger.debug(f"{problem_obj['unique_name']}: created debian package")

    try:
        subprocess.run('DEBIAN_FRONTEND=noninteractive apt-get -y install ' +
                       f'--reinstall {generated_deb_path}',
                       shell=True, check=True, stdout=subprocess.PIPE)
    except subprocess.CalledProcessError:
        logger.error("An error occurred while installing problem packages.")
        raise FatalException
    finally:
        os.remove(lock_file)
        logger.debug(f"{problem_obj['unique_name']}: released lock file ({str(lock_file)})")
    logger.debug(f"{problem_obj['unique_name']}: installed package")
    logger.info(f"{problem_obj['unique_name']} installed successfully")


def find_problem_sources(root_path):
    """
    Find all problem source directories that exist under the given root.

    Any directory with a problem.json is considered a source directory.

    Args:
        root_path: the problem directory
    Returns:
        A list of problem paths.
    """
    problem_source_paths = []
    for dir_path, _, files in os.walk(root_path):
        if "problem.json" in files and "__staging" not in dir_path:
            problem_source_paths.append(dir_path)
    return problem_source_paths


def install_problems(args, config):
    """
    Entrypoint for problem installation.

    Allows for installation of multiple/nested problem source folders.
    """
    if not args.problem_paths:
        logger.error("No problem source path(s) specified")
        raise FatalException

    problem_paths = []
    for base_path in args.problem_paths:
        problem_paths.extend(find_problem_sources(base_path))

    for problem_path in problem_paths:
        install_problem(problem_path)


def install_bundle(args, config):
    """
    "Installs" a bundle (validates it and stores a copy).

    "Bundles" are just JSON problem unlock weightmaps which are exposed to
    and used by the web server.

    All problems specified in a bundle must already be installed.
    """
    if not args.bundle_path:
        logger.error("No problem source path specified")
        raise FatalException
    bundle_path = args.bundle_path
    bundle_obj = get_bundle2(bundle_path)

    if os.path.isdir(join(BUNDLE_ROOT, sanitize_name(bundle_obj['name']))):
        logger.error(f"A bundle with name {bundle_obj['name']} is " +
                     "already installed")
        raise FatalException

    for problem_name in bundle_obj['problems']:
        if not os.path.isdir(join(PROBLEM_ROOT, problem_name)):
            logger.error(f"Problem {problem_name} must be installed " +
                         "before installing bundle")
            raise FatalException

    bundle_destination = join(
        BUNDLE_ROOT, sanitize_name(bundle_obj['name']), 'bundle.json')
    os.makedirs(os.path.dirname(bundle_destination), exist_ok=True)
    shutil.copy(bundle_path, bundle_destination)
    logger.info(f"Installed bundle {bundle_obj['name']}")


def uninstall_bundle(args, config):
    """
    Uninstall a bundle by deleting it from the shell servers.

    Problems referenced within the bundle are not affected.
    """
    if not args.bundle_name:
        logger.error("No bundle name specified")
        raise FatalException
    bundle_name = args.bundle_name

    bundle_dir = join(BUNDLE_ROOT, sanitize_name(bundle_name))
    if not os.path.isdir(bundle_dir):
        logger.error(f"Bundle '{bundle_name}' is not installed")
    else:
        shutil.rmtree(bundle_dir)
        logger.info(f"Bundle '{bundle_name}' successfully removed")
