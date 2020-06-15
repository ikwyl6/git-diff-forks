# git-diff-forks
Show all the forks for an upstream repository that do not have the same commit id as the upstream repository. The script only downloads the ```.git``` files enough to do comparisons on the repos themselves. IE: It will only do a ```git fetch``` on the repository and it's forks that are listed on the github website.
This can be added as a git custom command if you add the script to your path. Then you can do ```git diff-forks -r name|link-to-github-repo``` instead of just ```./git-diff-forks.py```

Right now the script only compares each ```master``` branch of the upstream and its forks. 

## Usage
```
$ ./git-diff-forks.py -r https://github.com/user/repository(.git)?
$ ./git-diff-forks.py -r ssh://github.com/user/repository(.git)?
$ ./git-diff-forks.py -r user/repository
```

## Options
```
-h | --help  show help message and command line options
-r | --repo  name or link to repository. This can be in the form of 'user/repository-name', 
            'https://github.com/user/repository-name', 
            'ssh://guthub.com/user/repository-name'
-d | --dir   directory that you want to create the ```.git``` files in (default: /tmp)
```

Options to be implemented:
```
-b  | --branch	            Specify a different branch to use instead of 'master' branch
-df | --diff-files      show the files from each fork that are different from the upstream files
-dr | --delete-remotes  delete the .git files after completion of script 
                        (default: /tmp/repo_user-repo_name/)
-v  | --verbose         verbose output
```
## Sample Output
```
$ ./git-diff-forks.py -r https://github.com/eshmu/gphotos-upload
eshmu / gphotos-upload (67f66af)
  |- fork-MartMet/master (b3fb2bd) 2020-01-02
  |- fork-Tommzs/master (7bcb269) 2019-12-02
  |- fork-johnedstone/master (dcd786d) 2020-04-30
  |- fork-jorgeas80/master (d81e79b) 2020-04-13
  |- fork-petryx/master (137783f) 2019-06-22
  |- fork-rock-meister/master (f9c3671) 2020-04-07
```
## Want more options?
Create an issue and I'll look into it!
