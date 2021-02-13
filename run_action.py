#!/usr/bin/env python

import os
import sys
import json
import requests
import argparse

import duplicate_code_detection

WARNING_SUFFIX = " ⚠️"


def make_markdown_table(array):
    """ Input: Python list with rows of table as lists
               First element as header. 
        Output: String to put into a .md file 

    Ex Input: 
        [["Name", "Age", "Height"],
         ["Jake", 20, 5'10],
         ["Mary", 21, 5'7]] 

     Adopted from: https://gist.github.com/m0neysha/219bad4b02d2008e0154
    """
    markdown = "\n" + str("| ")

    for e in array[0]:
        to_add = " " + str(e) + str(" |")
        markdown += to_add
    markdown += "\n"

    markdown += '|'
    for i in range(len(array[0])):
        markdown += str("-------------- | ")
    markdown += "\n"

    for entry in array[1:]:
        markdown += str("| ")
        for e in entry:
            to_add = str(e) + str(" | ")
            markdown += to_add
        markdown += "\n"

    return markdown + "\n"


def get_markdown_link(file, url):
    return "[%s](%s%s)" % (file, url, file)


def get_warning(similarity, warn_threshold):
    return str(similarity) if similarity < int(warn_threshold) else str(similarity) + WARNING_SUFFIX


def similarities_to_markdown(similarities, url_prefix, warn_threshold):
    markdown = str()
    for checked_file in similarities.keys():
        markdown += "<details><summary>%s</summary>\n\n" % checked_file
        markdown += "### 📄 %s\n" % get_markdown_link(checked_file, url_prefix)

        table_header = ["File", "Similarity (%)"]
        table_contents = [[get_markdown_link(f, url_prefix), get_warning(s, warn_threshold)]
                          for (f, s) in similarities[checked_file].items()]
        # Sort table contents based on similarity
        table_contents.sort(
            reverse=True, key=lambda row: float(row[1].replace(WARNING_SUFFIX, "")))
        entire_table = [[] for _ in range(len(table_contents) + 1)]
        entire_table[0] = table_header
        for i in range(1, len(table_contents) + 1):
            entire_table[i] = table_contents[i-1]

        markdown += make_markdown_table(entire_table)
        markdown += "</details>\n"

    return markdown


def split_and_trim(input_list):
    return [token.strip() for token in input_list.split(',')]


def to_absolute_path(paths):
    return [os.path.abspath(path) for path in paths]


def main():
    parser = argparse.ArgumentParser(
        description="Duplicate code detection action runner")
    parser.add_argument("--latest-head", type=str,
                        default="master", help="The latest commit hash or branch")
    parser.add_argument("--pull-request-id", type=str,
                        required=True, help="The pull request id")
    args = parser.parse_args()

    fail_threshold = os.environ.get('INPUT_FAIL_ABOVE')
    directories = os.environ.get('INPUT_DIRECTORIES')
    ignore_directories = os.environ.get('INPUT_IGNORE_DIRECTORIES')
    project_root_dir = os.environ.get('INPUT_PROJECT_ROOT_DIR')
    file_extensions = os.environ.get('INPUT_FILE_EXTENSIONS')
    ignore_threshold = os.environ.get('INPUT_IGNORE_BELOW')

    directories_list = split_and_trim(directories)
    directories_list = to_absolute_path(directories_list)
    ignore_directories_list = split_and_trim(
        ignore_directories) if ignore_directories != '' else list()
    ignore_directories_list = to_absolute_path(ignore_directories_list)
    file_extensions_list = split_and_trim(file_extensions)
    project_root_dir = os.path.abspath(project_root_dir)

    files_list = None
    ignore_files_list = None
    json_output = True

    detection_result, code_similarity = duplicate_code_detection.run(int(fail_threshold), directories_list, files_list,
                                                                     ignore_directories_list, ignore_files_list,
                                                                     json_output, project_root_dir, file_extensions_list,
                                                                     int(ignore_threshold))

    if detection_result == duplicate_code_detection.ReturnCode.BAD_INPUT:
        print("Action aborted due to bad user input")
        return detection_result.value
    elif detection_result == duplicate_code_detection.ReturnCode.THRESHOLD_EXCEEDED:
        print(
            "Action failed due to maximum similarity threshold exceeded, check the report")

    repo = os.environ.get('GITHUB_REPOSITORY')
    files_url_prefix = 'https://github.com/%s/blob/%s/' % (
        repo, args.latest_head)
    warn_threshold = os.environ.get('INPUT_WARN_ABOVE')

    message = "## 📌 Duplicate code detection tool report\n"
    message += "The [tool](https://github.com/platisd/duplicate-code-detection-tool)"
    message += " analyzed your source code and found the following degree of"
    message += " similarity between the files:\n"
    message += similarities_to_markdown(code_similarity,
                                        files_url_prefix, warn_threshold)

    github_token = os.environ.get('INPUT_GITHUB_TOKEN')
    github_api_url = os.environ.get('GITHUB_API_URL')
    request_url = '%s/repos/%s/issues/%s/comments' % (
        github_api_url, repo, args.pull_request_id)

    post_result = requests.post(request_url, json={'body': message}, headers={
                                'Authorization': 'token %s' % github_token})

    if post_result.status_code != 201:
        print("Posting results to GitHub failed with code: " +
              str(post_result.status_code))
        print(post_result.text)

    return detection_result.value


if __name__ == "__main__":
    sys.exit(main())
