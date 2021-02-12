#!/usr/bin/env python

import os
import sys

import duplicate_code_detection

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
    github_token = os.environ.get('INPUT_GITHUB_TOKEN')

    directories_list = split_and_trim(directories)
    directories_list = to_absolute_path(directories_list)
    ignore_directories_list = split_and_trim(ignore_directories) if ignore_directories != '' else list()
    ignore_directories_list = to_absolute_path(ignore_directories_list)
    file_extensions_list = split_and_trim(file_extensions)
    project_root_dir = os.path.abspath(project_root_dir)

    files_list = None
    ignore_files_list = None
    json_output = True

    print("!!!!!!!!!!!")
    print(os.environ)
    print("-----------")
    print(os.environ.get('GITHUB_API_URL'))
    print(os.environ.get('GITHUB_REPOSITORY'))
    print(os.environ.get('GITHUB_REPOSITORY_OWNER'))
    print(os.environ.get('GITHUB_EVENT_NAME'))
    print(os.environ.get('GITHUB_EVENT_PATH'))
    print(os.environ.get('GITHUB_REF'))
    print(os.environ.get('GITHUB_RUN_ID'))
    print("-----------")

    return 1

    result, code_similarity = duplicate_code_detection.run(int(fail_threshold), directories_list, files_list,
                                                        ignore_directories_list, ignore_files_list,
                                                        json_output, project_root_dir, file_extensions_list,
                                                        int(ignore_threshold))

    return result


if __name__ == "__main__":
    sys.exit(main())
