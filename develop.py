# author: Lara Peeters (@laraPPr)
#
# license: GPLv2
#

# Can also be added to the app.cfg file of the bot
develop_base_dir = "/scratch/gent/461/vsc46128/EESSI/dev"
development_repos = [
    'laraPPr/lammps'
]



# Standard library imports
from datetime import datetime, timezone
import glob
import json
import os
import re
import sys

# Argsparse
import argparse
import subprocess

#Functions form eessi-bot-software-layer tools/__init__.py
def run_cmd(cmd, log_msg='', working_dir=None, log_file=None, raise_on_error=True):
    """
    Runs a command in the shell and raises an error if one occurs.

    Args:
        cmd (string): command to run
        log_msg (string): message describing the purpose of the command
        working_dir (string): location of the job's working directory
        log_file (string): path to log file
        raise_on_error (bool): if True raise an exception in case of error

    Returns:
        tuple of 3 elements containing
        - stdout (string): stdout of the process
        - stderr (string): stderr of the process
        - exit_code (string): exit code of the process

    Raises:
        RuntimeError: raises a RuntimeError if exit code was not zero and
            raise_on_error is True
    """
    # TODO use common method for logging function name in log messages
    stdout, stderr, exit_code = run_subprocess(cmd, log_msg, working_dir, log_file)

    if exit_code != 0:
        error_msg = (
            f"run_cmd(): Error running '{cmd}' in '{working_dir}\n"
            f"           stdout '{stdout}'\n"
            f"           stderr '{stderr}'\n"
            f"           exit code {exit_code}"
        )
        print(error_msg, log_file)
        if raise_on_error:
            raise RuntimeError(error_msg)
    else:
        print(f"run_cmd(): Result for running '{cmd}' in '{working_dir}\n"
            f"           stdout '{stdout}'\n"
            f"           stderr '{stderr}'\n"
            f"           exit code {exit_code}", log_file)

    return stdout, stderr, exit_code

def run_subprocess(cmd, log_msg, working_dir, log_file):
    """
    Runs a command in the shell. No error is raised if the command fails.

    Args:
        cmd (string): command to run
        log_msg (string): purpose of the command
        working_dir (string): location of the job's working directory
        log_file (string): path to log file

    Returns:
        tuple of 3 elements containing
        - stdout (string): stdout of the process
        - stderr (string): stderr of the process
        - exit_code (string): exit code of the process
    """
    # TODO use common method for logging function name in log messages
    if working_dir is None:
        working_dir = os.getcwd()

    if log_msg:
        print(f"run_subprocess(): '{log_msg}' by running '{cmd}' in directory '{working_dir}'", log_file)
    else:
        print(f"run_subprocess(): Running '{cmd}' in directory '{working_dir}'", log_file)

    result = subprocess.run(cmd,
                            cwd=working_dir,
                            shell=True,
                            encoding="UTF-8",
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    stdout = result.stdout
    stderr = result.stderr
    exit_code = result.returncode

    return stdout, stderr, exit_code
    

# Generating of EasyConfig functions
def request_bot_dev_pr(repo_name, pr_number):
    """
    Query the github API for the pr info.

    Args:
        repo_name (string): name of the repository (format USER_OR_ORGANISATION/REPOSITORY)
        pr_number (int): number og the pr

    Returns:
        head_branch (string): name of the head branch in the pr
        base_branch (string): name of the base branch in the pr
    """

    curl_cmd = f'curl -L https://api.github.com/repos/{repo_name}/pulls/{pr_number}'
    curl_output, curl_error, curl_exit_code = run_cmd(curl_cmd, "fetch pr")

    pr_info = json.loads(curl_output)

    head_branch = pr_info['head']['ref']
    base_branch = pr_info['base']['ref']
    if args.commit:
        commit = args.commit
    else:
        commit = pr_info['head']['sha']

    return head_branch, base_branch, commit

def create_dev_dir(pr_number, repo_name, commit, develop_base_dir):
    """
    Create directory where the generated patch files and or sources can be put
    for dev.eessi.io builds. Full path to the directory has the format

    config.DEVELOP_SETTINGS_DEVELOP_DIR/<year>.<month>/pr_<pr number>

    where config.DEVELOP_SETTINGS_DEVELOP_DIR is defined in the configuration 
    (see 'app.cfg'), year contains four digits, and month contains two digits

    Args:
        pr (github.PullRequest.PullRequest): instance representing the pull request
        develop_base_dir (ConfigParser): typically read from 'app.cfg'

    Returns:
        tuple of 3 elements containing
        - (string): year_month with format '<year>.<month>' (year with four
              digits, month with two digits)
        - (string): pr_id with format 'pr_<pr number>'
        - (string): run_dir which is the complete path to the created directory
              with format as described above
    """

    pr_id = 'pr_%s_cm_%s' % (pr_number, commit)
    develop_dir = os.path.join(develop_base_dir, repo_name, pr_id)

    os.makedirs(develop_dir, exist_ok=True)
    return develop_dir

def generate_easyconfig(develop_dir, repo_name, commit, base_branch):
    """
    Generate an easyconfig with `--copy-ec`

    Args:

    Returns:

    """

    #develop = cfg[config.SECTION_DEVELOP]
    
    if os.listdir(develop_dir) != []:
        generate_msg = 'easyconfig is already generated'
        
    else:
        #TODO: This dev command will only work in the the laraPPr/lammps repo
        # need to add more cases or a different machanism
        # Can make a for loop through all repos listed unde
        
        place_holder_files = os.listdir(f'{develop_base_dir}/placeholder_ec')
        
        if repo_name == "laraPPr/lammps":
            module_name = 'LAMMPS'
            version = '_'.join(base_branch.split('_')[1:])
            toolchain = args.toolchain
            versionsuffix = 'kokkos'
            
            easyconfig = '-'.join([module_name, version, toolchain, f'{versionsuffix}.eb'])
            
            print(easyconfig)
            
            if easyconfig in place_holder_files:
                with open(f'{develop_base_dir}/placeholder_ec/{easyconfig}', 'r') as file:
                    file_contents = file.read()
                
                source_url = f'https://github.com/{repo_name}/archive/'
                sources = f'{commit}.tar.gz'
           
                updated_contents = file_contents.replace('_VERSIONSUFFIX', '"-kokkos-dev_OBMD"')
                updated_contents = updated_contents.replace('_SOURCE_URL', f'"{source_url}"')
                updated_contents = updated_contents.replace('_SOURCES', f'"{sources}"')
                updated_contents = updated_contents.replace('_GENERAL_PACKAGES', f'\n    "DPD-BASIC",\n"    MOLECULE",\n"    OBMD"')
                updated_contents = updated_contents.replace('_CHECK_FILES', f'\n    "balance", "crack", "friction", "indent",\n    "melt", "min", "nemd", "obstacle", "OBMD"\n')
                
                with open(f'{develop_dir}/LAMMPS-2Aug2023_update2-foss-2023a-kokkos-dev_OBMD.eb', 'w') as file:
                    file.write(updated_contents)
                
                # update checksums (Not sure where to best do this)
                #            checksums_cmd = ' '.join(['eb --detect-loaded-modules=purge', new_ec, 
                #                '--inject-checksums --force'])
                #            checksum_output, checksum_error, checksum_exit_code = run_cmd(checksums_cmd, 'inject new checksums in easyconfig')
                generate_msg = f'easyconfig was generated in path {develop_dir}'

            else:
                # Only add a patch to the easyconfig and add OBMB to the list of general packages and add a list of check_files
                eb_cmd = ' '.join([f'cd {develop_dir} && eb --copy-ec', easyconfig])
                eb_output, eb_error, eb_exit_code = run_cmd(eb_cmd, "create eb")
                
                if eb_exit_code != 0:
                     gerenate_msg = f'No config can be generated from unkown easyconfig'
                else:
                    # generate patch from commit
                    curl_cmd = ' '.join(['cd {develop_dir} && curl', f'-o {commit}.patch', f'https://github.com/{repo_name}/commit/{commit}.patch'])
                    curl_output, curl_error, curl_exit_code = run_cmd(curl_cmd, f'get patch of https://github.com/{repo_name}/commit/{commit}')
                    
                    with open(f'{develop_base_dir}/placeholder_ec/{easyconfig}', 'r') as file:
                        file_contents = file.read()
                    
                    # This will only work for develop branch where OBMD is included !!!!!
                    list_of_lines = file_contents.split('\n')
                    
                    index_general_packages = list_of_lines.index('general_packages = [')
                    list_of_lines.insert(index_general_packages + 1, "    'OBMD',")
                    
                    index_patches = list_of_lines.index('patches = [')
                    list_of_lines.insert(index_patches + 1, "    '{commit}.patch',")
                    
                    # ToDo: have to add the check_files to this 
                    check_files = "check_files = [\n    'atm', 'balance', 'colloid', 'crack', 'dipole', 'friction',\n    \
                    'hugoniostat', 'indent', 'melt', 'min', 'msst',\n    'nemd', 'obstacle', 'pour', 'voronoi', 'OBMD'\n]\n"
                    list_of_lines.insert(-2, check_files)
                    
                    updated_contents = '\n'.join(list_of_lines)
                
                    with open(f'{develop_dir}/{easyconfig}', 'w') as file:
                        file.write(updated_content)
                    
                    gerenate_msg = f'No config can be generated from unkown base branch {base_branch}'    
                    
        else:
            # simply add a patch for some packages this will probably work out of the box
            
            #TODO how to generate the easyconfig where the patch should be added
            
            curl_cmd = ' '.join(['cd {develop_dir} && curl', f'-o {commit}.patch', f'https://github.com/{repo_name}/commit/{commit}.patch'])
            curl_output, curl_error, curl_exit_code = run_cmd(curl_cmd, f'get patch of https://github.com/{repo_name}/commit/{commit}')
            
            if curl_exit_code != 0:
                gerenate_msg = f'Could not generate a patch from https://github.com/{repo_name}/commit/{commit}'
            else:
                generate_msg = f'A patch file was gerenerated in {develop_dir}'
                
            
            generate_msg = f'No config can be generated from unkwown repo {repo_name}. Please add an EasyConfig that can be used for development'
        
            

    return generate_msg
    


    

    
# Can also get this info form the build bot. See request_bot_dev_pr.
parser = argparse.ArgumentParser()
parser.add_argument("repo_name", help="Name of the repo where the development is done")
# Can use commit if you do not want to use the last made commit in the pr
parser.add_argument("--commit", required=False, help="commit you would like to get build with dev.eessi.io",)
# Need pr_number but can get the last commit from this one so commit is not necessary
parser.add_argument("pr_number", help="The pr-number of the pr from which the bot will build")
parser.add_argument("toolchain", help="The toolchain you would like to have an easyconfig for")
args = parser.parse_args()

repo_name = args.repo_name
print(args.repo_name)
pr_number = args.pr_number
print(args.pr_number)
print(args.toolchain)
if args.commit:
    print(args.commit)

if repo_name in development_repos:
    
    head_branch, base_branch, commit = request_bot_dev_pr(repo_name, pr_number)
    print(head_branch)
    print(base_branch)
    print(commit)

    develop_dir = create_dev_dir(pr_number, repo_name, commit, develop_base_dir)
    print(develop_dir)
    
    generate_easyconfig(develop_dir, repo_name, commit, base_branch)
    
else:
    print("There is no development set up for this repo")

