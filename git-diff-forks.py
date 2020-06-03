#!/usr/bin/python

import requests, argparse, re, json, logging
from subprocess import run,DEVNULL #,CompletedProcess
from os import path,mkdir,chdir

# CONSTANTS
regex_user_repo = '(([\w-]+)/([\w-]+))'
regex_http = 'http[s]?://github\.com/' + regex_user_repo + '(\.git)?'
regex_ssh = 'ssh://git@github/' + regex_user_repo + '(\.git)?'
github_api = 'https://api.github.com/repos/'
github_web = 'https://github.com/'
fork_list = [] # List of forks
fork_remote_prepend = "fork-"
# Create a list of git diff or log cmds that user wants to use against 
# the data set.
git_diff_cmd=["git for-each-ref --sort=-committerdate",
        "git log --oneline --shortstat", # or '--stat'
        "git log --name-only", # --name-status
        "git log --numstat"]


## COMMAND LINE ARGS ##
cla = argparse.ArgumentParser(prog='git-diff-forks', \
        description='Show the diffs of all forks of a git repo project')
cla.add_argument('-r', '--repo', \
        help='address or short form address of github repo')
cla.add_argument('-d', '--dir', default='/tmp', \
        help='target dir that is used for all work')
cla.add_argument('-n', '--newdir', \
        help='Create a new directory for comparing the upstream repo and \
        all forks')
cla.add_argument('-df', '--diff-files', \
        help='Show only the files that different from the fork and upstream \
        repo')
cla.add_argument('-dr', '--delete-remotes', \
        help='Delete all remotes created from this diff comparisoni after \
        script is completed')
cla.add_argument('-v', '--verbose', \
        help='Show verbose information/debug')
# https://stackoverflow.com/questions/14097061/easier-way-to-enable-verbose-logging
#parser.add_argument(
#            '-d', '--debug',
#                help="Print lots of debugging statements",
#                    action="store_const", dest="loglevel", const=logging.DEBUG,
#                        default=logging.WARNING,
#                        )
#parser.add_argument(
#            '-v', '--verbose',
#                help="Be verbose",
#                    action="store_const", dest="loglevel", const=logging.INFO,
#                    )
#args = parser.parse_args()    
#logging.basicConfig(level=args.loglevel)
clargs = cla.parse_args()

def branch_exists(branch_name):
    cp = run(["git", "branch", "-v"], capture_output=True, text=True)
    m = re.search(branch_name, cp.stdout)
    if (m):
        return True


# Parse the user and repo name first
if (not clargs.repo):
    print ("No github repository supplied. Exiting.")
    exit()
else:
    # Check if shortform (user/repo) or link
    repo_match_short = re.search('^' + regex_user_repo, clargs.repo)
    repo_match_http = re.search(regex_http, clargs.repo)
    repo_match_ssh = re.search(regex_ssh, clargs.repo)
    try:
        if (repo_match_short):
            #logging ("short: " + str(repo_match_short.group(0)))
            repo = repo_match_short.group(1)
            repo_user = repo_match_short.group(2)
            repo_name = repo_match_short.group(3)
            repo_git_link = github_web + repo_user + "/" + repo_name + ".git"
            print ('user: ' + repo_user + ", name: " + repo_name)
        elif (repo_match_http):
            #logging ("http: " + str(repo_match_http.group(1)))
            repo = repo_match_http.group(1)
            repo_user = repo_match_http.group(2)
            repo_name = repo_match_http.group(3)
            if repo_match_http.group(4):
                repo_git_link = github_web + repo_user + "/" + repo_name + \
                        repo_match_http.group(4)
            else:
                repo_git_link = github_web + repo_user + "/" + repo_name + \
                        ".git"
            print ('user: ' + repo_user + ", name: " + repo_name)
        elif (repo_match_ssh):
            #logging ("ssh: " + str(repo_match_ssh.group(1)))
            repo = repo_match_ssh.group(1)
            repo_user = repo_match_ssh.group(2)
            repo_name = repo_match_ssh.group(3)
            if repo_match_http.group(4):
                repo_git_link = github_web + repo_user + "/" + repo_name + \
                        repo_match_http.group(4)
            else:
                repo_git_link = github_web + repo_user + "/" + repo_name + \
                        ".git"
            print ('user: ' + repo_user + ", name: " + repo_name)
        else:
            print("Could not find repository address: " + clargs.repo)
            exit()
        print("repo_git_link: " + repo_git_link)
    except (AttributeError) as e:
        print("repo_match_* error " + str(e))
    # Set up the api url to grab all forks
    github_api_forks = github_api + repo + '/forks'
    print("link: " + github_api_forks)
    response = requests.get(github_api_forks)
    if response.status_code == 404:
        print("Server returned 404. Exiting.")
        response.raise_for_status()
        exit()
    elif (response.ok):
        for fork in response.json():
            #print("fork url: " + fork['clone_url'])
            fork_list.append(fork['clone_url'])
    else:
        print("Server returned status code: " + response.status_code)
        exit()

# Start doing git commands
if clargs.dir:
    wd = clargs.dir + "/" + repo_user + "-" + repo_name
    if path.isdir(wd):
        # logging(dir exists)
        pass
    else:
        try:
            mkdir(wd)
        except (OSError):
            print("Could not create directory " + wd)
            exit()
        else:
            # logging(dir does not exist, creating)
            pass
    # TODO try/check you can chdir to wd
    chdir(wd)
    cmd = run(["git", "rev-parse", "--is-inside-work-tree"], \
        capture_output=True, text=True)
    if not cmd.returncode == 0:
        print("No .git directory found, creating")
        cmd = run(["git", "init"], capture_output=True, text=True)
    # See if the upstream remote already exists, if not create.
    cmd = run(["git", "remote", "-v"], capture_output=True, text=True)
    match_repo_git = re.search(repo, cmd.stdout)
    if (match_repo_git):
        print("remote already exists: " + match_repo_git.group(0))
    else:
        # create the git remote
        #logging print("Creating git remote. git remote add upstream" + repo_git_link)
        run(["git", "remote", "add", "upstream", repo_git_link], capture_output=False)
    print("Fetching upstream..")
    run(["git", "fetch", "upstream"])#, stdout=DEVNULL, stderr=DEVNULL) 
    # go through all forks and create remotes
    for fork_link in fork_list:
        match_fork_ur = re.search(regex_user_repo + "\.git", fork_link)
        if (match_fork_ur):
            remote_fork_name = match_fork_ur.group(2)
        else:
            # didn't match on fork_name, better skip this one
            print ("Skipping..fork name didn't match: " + \
                match_fork_ur.group(1) + "with " + \
                regex_user_repo + "\.git")
            continue
        cmd = run(["git", "remote", "-v"], capture_output=True, text=True)
        match_fork_git = re.search(remote_fork_name, cmd.stdout)
        if (match_fork_git):
            pass
            #print("fork already exists: " + match_fork_git.group(0))
        else:
            #print("git remote add fork-" + remote_fork_name + " " + fork_link)
            cmd = run(["git", "remote", "add", "fork-" + remote_fork_name, \
                    fork_link], stdout=None)
        #run(["git", "fetch", "fork-" + remote_fork_name], capture_output=False)
    run(["git", "fetch", "--all"], stderr=DEVNULL, stdout=DEVNULL)
    cmd = run (["git", "log", "-1", "upstream/master", "--format=%h"], \
            capture_output=True, text=True)
    repo_head = cmd.stdout.rstrip()
    # logging print("repo_head: " + repo_head)
    cmd = run(["git", "for-each-ref", \
        # "--sort='-committerdate'" \
          "--format=%(objectname:short) %(authordate:short) %(refname:short)", \
          "refs/remotes/*/master"], \
          capture_output=True, text=True)
    if not cmd.returncode == 0:
        print("Error return code from " + str(cmd.args))
        print("Output from cmd:\n" + cmd.stderr)
        exit()
    lines = cmd.stdout.split('\n')
    print("\n" + repo_user + " / " + repo_name + " (" + repo_head + ")")
    for line in lines:
        #print("line: " + line)
        #print("re: " + "^(?!" + repo_head + ").*")
        match_neg_la = re.search("^(?!(" + repo_head + "))", line)
        if match_neg_la:
            match_commit_info = re.search("^([\w]+)\ ([\w-]+)\ (.*)", line)
            if match_commit_info:
                fork_commit_head = match_commit_info.group(1)
                fork_commit_date = match_commit_info.group(2)
                fork_name = match_commit_info.group(3)
                print("  |- " + fork_name + " (" + fork_commit_head + ") " \
                        + fork_commit_date)
            else:
                pass
                #print("found fork with same commit")
        else:
            pass
            #print("No match_neg_la" + line)
    # git ls-remote --heads git@github.com:user/repo.git branch-name
        #  
        # https://stackoverflow.com/questions/8223906/how-to-check-if-remote-branch-exists-on-a-given-remote-repository#30524983

        # run 'git for-each-ref --sort=-committerdate' and check if each fork 
        # has same commit as repo
