#!/usr/bin/env python

import os
import sys

import duplicate_code_detection

def split_and_trim(input_list):
    return [token.strip() for token in input_list.split(',')]

def main():
    fail_threshold = os.environ.get('INPUT_FAIL_THRESHOLD')
    directories = os.environ.get('INPUT_DIRECTORIES')
    ignore_directories = os.environ.get('INPUT_IGNORE_DIRECTORIES')
    project_root_dir = os.environ.get('INPUT_PROJECT_ROOT_DIR')
    file_extensions = os.environ.get('INPUT_FILE_EXTENSIONS')
    ignore_threshold = os.environ.get('INPUT_IGNORE_THRESHOLD')
    github_token = os.environ.get('INPUT_GITHUB_TOKEN')

    directories_list = split_and_trim(directories)
    ignore_directories_list = split_and_trim(ignore_directories)
    file_extensions_list = split_and_trim(file_extensions)

    files_list = None
    ignore_files_list = None
    json_output = True

    result, _ = duplicate_code_detection.run(fail_threshold, directories, files_list,
                                                        ignore_directories, ignore_files_list,
                                                        json_output, project_root_dir, file_extensions,
                                                        ignore_threshold)

    return result


if __name__ == "__main__":
    sys.exit(main())
