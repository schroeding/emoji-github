## WAL Project - Emojis and Github

#### Data Preparation

Change to the directory you want to save the data to, i.e. in this case create a new directory under `github_data` for
the desired programming language, which the repos should use, e.g. `github_data/java_data` for Java.

Execute `gh-sampler.py` for the desired programming language and min amount of stars, like so:

```
../gh-sampler.py -t ghp_<github token(s)> -s 10 -l java -o java_data.json
```

Gather a list of emojis which can be used in Github, save it as `emojis.md` and run `emoji_list_from_markdown_table.sh` to
generate a clean text file with one emoji per line. If you only want to search for certain emojis, alter this step and filter
down the resulting list.

#### Generate CSV Data From Prepared Data

After preparing all data, run `create_csv_from_raw_data.sh <language>`. Note that the naming of the prepared data is important and
failure to follow it will cause the script to error out. It is expected that the scraped data is in `github_data/<language>_data/`,
with the json file being under `github_data/<language>_data/<language>_data.json`

The resulting `github_data.csv` will contain the following columns:

`repo` - the slug of the repo, i.e. "username/reponame"
`created_at` - date at which repo was created
`last_update_at` - last update to the repo
`language` - the programming language, in which the code of the repo is (mainly) written
`stars_count` - the number of stars
`is_fork_itself` - if the repo itself is a fork of another repo
`forks_count` - the number of forks
`issues_count` - count of open issues
`emojis_readme` - the number of emojis used in the readme
`emojis_description` - the number of emojis used in the description (which is shown when searching for repos)
