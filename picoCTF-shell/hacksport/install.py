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
from shell_manager.package import package_problem
from shell_manager.util import get_problem, DEB_ROOT, FatalException, join, HACKSPORTS_ROOT, get_problem_root_hashed
from hacksport.deploy import generate_staging_directory

logger = logging.getLogger(__name__)


def install_problem(args, config):
    """
    Installs a problem from a source directory.

    Args:
        args: argparse Namespace
            problem_path: path to the problem source directory
        config: unused, passed by argparse – @todo remove
    """
    if not args.problem_path:
        logger.error("No problem source path specified")
        raise FatalException
    problem_path = args.problem_path

    lock_file = join(HACKSPORTS_ROOT, "deploy.lock")
    if os.path.isfile(lock_file):
        logger.error(
            "Another problem installation or deployment appears in progress. If you believe this to be an error, "
            "run 'shell_manager clean'")
        raise FatalException

    problem_obj = get_problem(problem_path)
    if os.path.isdir(get_problem_root_hashed(problem_obj)):
        logger.error(f"Problem {problem_obj['unique_name']} is already installed")
        raise FatalException
    logger.info(f"Installing problem {problem_obj['unique_name']}...")

    logger.debug(f"{problem_obj['unique_name']}: obtained deployment lock file ({str(lock_file)})")
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
        subprocess.run(f'apt-get install --reinstall {generated_deb_path}',
                       shell=True, check=True, stdout=subprocess.PIPE)
    except subprocess.CalledProcessError:
        logger.error("An error occurred while installing problem packages.")
        raise FatalException
    finally:
        os.remove(lock_file)
        logger.debug(f"{problem_obj['unique_name']}: released deployment lock file ({str(lock_file)})")
    logger.debug(f"{problem_obj['unique_name']}: installed package")
    logger.info(f"{problem_obj['unique_name']} installed successfully")
