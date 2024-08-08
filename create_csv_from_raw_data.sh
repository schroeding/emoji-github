#!/usr/bin/env bash

if [ -z "$1" ]; then
  echo "no programming language given"
  echo "Usage: $0 <language>"
  exit 1
fi

DATA_DIR="github_data/${1}_data"
DATA_JSON="${1}_data.json"

if [ ! -d "${DATA_DIR}" ]; then
	echo "no directory '${DATA_DIR}' - correct language given?"
	exit 1
fi

if [ ! -f "${DATA_DIR}/${DATA_JSON}" ]; then
	echo "no JSON file under '${DATA_DIR}/${DATA_JSON}' - correct data preparation?"
	exit 1
fi
temp_csv_data=$(sed ':a;N;$!ba;s/\n/ /g' "${DATA_DIR}/${DATA_JSON}" | jq -r 'to_entries[] | "\"\(.key)\",\"\(.value.created_at)\",\"\(.value.updated_at)\",\"\(.value.language)\",\(.value.stargazers_count),\(.value.fork),\(.value.forks_count),\(.value.open_issues_count),\"\(.value.description)\""')
# if you want to filter the data before reading the actual readmes (the most expensive operation here), you can add
# additional filters to this output (e.g. via awk)
filtered_temp_csv_data=$(echo "${temp_csv_data}")

#repo_slugs_and_description=$(echo "${filtered_temp_csv_data}" | awk -F ',' '{ print substr($1, 2, length($1) - 2)","$9$10$11$12$13$14$15$16$17$18$19$20$21$22$23$24$25 }')
repo_slugs_with_readme=""
while IFS= read -r line; do
	slug=$(echo "${line}" | awk -F ',' '{ print substr($1, 2, length($1) - 2) }')
	# this is a nice botch, if a description has more than 20 commas we will loose some data - quite unlikely, as the total
	# length is like 250 chars max
	description=$(echo "${line}" | awk -F ',' '{ print $9$10$11$12$13$14$15$16$17$18$19$20$21$22$23$24$25$26$27$28$29 }')
	slug_filename=$(echo "${slug}.readme" | sed 's/\//_/')
#	echo "processing: ${slug} (${slug_filename})"
	if [ ! -f "${DATA_DIR}/${slug_filename}" ]; then
		echo "has no readme, skip"
		continue
	fi
	no_emoji_readme_github=$(grep -o -f emojis_list.txt "${DATA_DIR}/${slug_filename}" | wc -l)
	no_emoji_readme_unicode=$(grep -o -P "[\x{1f300}-\x{1f5ff}\x{1f900}-\x{1f9ff}\x{1f600}-\x{1f64f}\x{1f680}-\x{1f6ff}\x{2600}-\x{26ff}\x{2700}-\x{27bf}\x{1f1e6}-\x{1f1ff}\x{1f191}-\x{1f251}\x{1f004}\x{1f0cf}\x{1f170}-\x{1f171}\x{1f17e}-\x{1f17f}\x{1f18e}\x{3030}\x{2b50}\x{2b55}\x{2934}-\x{2935}\x{2b05}-\x{2b07}\x{2b1b}-\x{2b1c}\x{3297}\x{3299}\x{303d}\x{00a9}\x{00ae}\x{2122}\x{23f3}\x{24c2}\x{23e9}-\x{23ef}\x{25b6}\x{23f8}-\x{23fa}]" "${DATA_DIR}/${slug_filename}" | wc -l)
	no_emoji_readme=$((no_emoji_readme_github + no_emoji_readme_unicode))
#	echo "$description"
	no_emoji_desc_github=$(echo "${description}" | grep -o -f emojis_list.txt | wc -l)
	no_emoji_desc_unicode=$(echo "${description}" | grep -o -P "[\x{1f300}-\x{1f5ff}\x{1f900}-\x{1f9ff}\x{1f600}-\x{1f64f}\x{1f680}-\x{1f6ff}\x{2600}-\x{26ff}\x{2700}-\x{27bf}\x{1f1e6}-\x{1f1ff}\x{1f191}-\x{1f251}\x{1f004}\x{1f0cf}\x{1f170}-\x{1f171}\x{1f17e}-\x{1f17f}\x{1f18e}\x{3030}\x{2b50}\x{2b55}\x{2934}-\x{2935}\x{2b05}-\x{2b07}\x{2b1b}-\x{2b1c}\x{3297}\x{3299}\x{303d}\x{00a9}\x{00ae}\x{2122}\x{23f3}\x{24c2}\x{23e9}-\x{23ef}\x{25b6}\x{23f8}-\x{23fa}]" | wc -l)
	no_emoji_desc=$((no_emoji_desc_github + no_emoji_desc_unicode))
#	echo "emojis: ${no_emoji_readme} ${no_emoji_desc}"
	repo_slugs_with_readme+=$(echo "$line" | awk -F ',' '{ print $1","$2","$3","$4","$5","$6","$7","$8 }')
	repo_slugs_with_readme+=",${no_emoji_readme},${no_emoji_desc}"
	repo_slugs_with_readme+=$'\n'
done <<< "${filtered_temp_csv_data}"

echo "repo,created_at,last_update_at,language,stars_count,is_fork_itself,forks_count,issues_count,emojis_readme,emojis_description" > "github_$1.csv"
echo "$repo_slugs_with_readme" >> "github_$1.csv"

echo "saved csv output to github_$1.csv, done"
