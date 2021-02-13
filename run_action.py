#!/usr/bin/env python

import os
import sys
import json
import requests

import duplicate_code_detection


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


def similarities_to_markdown(similarities):
    markdown = str()
    for checked_file in similarities.keys():
        markdown += "### 📂 " + checked_file

        table_header = ["File", "Similarity (%)"]
        table_contents = [[f, s]
                          for (f, s) in similarities[checked_file].items()]
        entire_table = [[] for _ in range(len(table_contents) + 1)]
        entire_table[0] = table_header
        for i in range(1, len(table_contents) + 1):
            entire_table[i] = table_contents[i-1]

        markdown += make_markdown_table(entire_table)

    return markdown


def split_and_trim(input_list):
    return [token.strip() for token in input_list.split(',')]


def to_absolute_path(paths):
    return [os.path.abspath(path) for path in paths]


def main():
    fail_threshold = os.environ.get('INPUT_FAIL_THRESHOLD')
    directories = os.environ.get('INPUT_DIRECTORIES')
    ignore_directories = os.environ.get('INPUT_IGNORE_DIRECTORIES')
    project_root_dir = os.environ.get('INPUT_PROJECT_ROOT_DIR')
    file_extensions = os.environ.get('INPUT_FILE_EXTENSIONS')
    ignore_threshold = os.environ.get('INPUT_IGNORE_THRESHOLD')

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

    message = "## Duplicate code detection tool\n"
    message += "The [tool](https://github.com/platisd/duplicate-code-detection-tool)"
    message += " analyzed your source files and found the following similarities between them:\n"
    message += similarities_to_markdown(code_similarity)

    event_json_file_path = os.environ.get('GITHUB_EVENT_PATH')
    issue_number = None
    with open(event_json_file_path) as json_file:
        event = json.load(json_file)
        issue_number = event['issue']['number']

    github_token = os.environ.get('INPUT_GITHUB_TOKEN')
    github_api_url = os.environ.get('GITHUB_API_URL')
    repo = os.environ.get('GITHUB_REPOSITORY')
    request_url = '%s/repos/%s/issues/%s/comments' % (
        github_api_url, repo, str(issue_number))

    post_result = requests.post(request_url, json={'body': message}, headers={
                                'Authorization': 'token %s' % github_token})

    if post_result.status_code != 201:
        print("Posting results to GitHub failed with code: " +
              str(post_result.status_code))
        print(post_result.text)

    return detection_result


if __name__ == "__main__":
    sys.exit(main())
