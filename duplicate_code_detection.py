'''
A simple Python3 tool to detect similarities between files within a repository.

Document similarity code adapted from Jonathan Mugan's tutorial:
https://www.oreilly.com/learning/how-do-i-compare-document-similarity-using-python
'''
import os
import sys
import argparse
import gensim
import ast
import astor
import re
import tempfile
import json
from enum import Enum
from nltk.tokenize import word_tokenize
from collections import OrderedDict

source_code_file_extensions = ["h", "c", "cpp", "cc", "java", "py", "cs"]
file_column_label = "File"
similarity_column_label = "Similarity (%)"
similarity_label_length = len(similarity_column_label)


class ReturnCode(Enum):
    SUCCESS = 0
    BAD_INPUT = 1
    THRESHOLD_EXCEEDED = 2


class CliColors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def get_all_source_code_from_directory(directory, file_extensions):
    """ Get a list with all the source code files within the directory
    """
    source_code_files = list()
    for dirpath, _, filenames in os.walk(directory):
        for name in filenames:
            _, file_extension = os.path.splitext(name)
            if file_extension[1:] in file_extensions:
                filename = os.path.join(dirpath, name)
                source_code_files.append(filename)

    return source_code_files


def conditional_print(text, machine_friendly_output):
    if not machine_friendly_output:
        print(text)

def remove_comments_and_docstrings(source_code: str) -> str:
    """Strip comments and docstrings from source code

    .. seealso::

        https://gist.github.com/phpdude/1ae6f19de213d66286c8183e9e3b9ec1

    :param source_code: Raw source code as a single string
    :type source_code: str
    :return: Stripped source code as a single string
    :rtype: str
    """
    parsed = ast.parse(source_code)
    for node in ast.walk(parsed):
        if not isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef, ast.Module)):
            continue

        if not len(node.body):
            continue

        if not isinstance(node.body[0], ast.Expr):
            continue

        if not hasattr(node.body[0], 'value') or not isinstance(node.body[0].value, ast.Str):
            continue

        node.body = node.body[1:]

    source_code_clean  = astor.to_source(parsed)
    return source_code_clean


def main():
    parser_description = CliColors.HEADER + CliColors.BOLD + \
        "=== Duplicate Code Detection Tool ===" + CliColors.ENDC
    parser = argparse.ArgumentParser(description=parser_description)
    parser.add_argument("-t", "--fail-threshold", type=int, default=100,
                        help="The maximum allowed similarity before the script exits with an error.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-d", "--directories", nargs="+",
                       help="Check for similarities between all files of the specified directories.")
    group.add_argument('-f', "--files", nargs="+", help="Check for similarities between specified files. \
                        The more files are supplied the more accurate are the results.")
    parser.add_argument("--ignore-directories", nargs="+", default=list(),
                        help="Directories to ignore.")
    parser.add_argument("--ignore-files", nargs="+", help="Files to ignore.")
    parser.add_argument("-j", "--json", type=bool,
                        default=False, help="Print output as JSON.")
    parser.add_argument("--project-root-dir", type=str, default=str(),
                        help="The relative path to the project root directory to be removed when printing out results.")
    parser.add_argument("--file-extensions", nargs="+", default=source_code_file_extensions,
                        help="File extensions to check for similarities.")
    parser.add_argument("--ignore-threshold", type=int, default=0,
                        help="Don't print out similarity below the ignore threshold")
    parser.add_argument("--only-code", action="store_true", help="Removes comments and docstrings from the source code before analysis")
    args = parser.parse_args()

    result = run(args.fail_threshold, args.directories, args.files, args.ignore_directories,
                 args.ignore_files, args.json, args.project_root_dir, args.file_extensions,
                 args.ignore_threshold, args.only_code)

    return result


def run(fail_threshold, directories, files, ignore_directories, ignore_files,
        json_output, project_root_dir, file_extensions, ignore_threshold, only_code,):
    # Determine which files to compare for similarities
    source_code_files = list()
    files_to_ignore = list()
    if directories:
        for directory in directories:
            if not os.path.isdir(directory):
                print("Path does not exist or is not a directory:", directory)
                return (ReturnCode.BAD_INPUT, {})
            source_code_files += get_all_source_code_from_directory(
                directory, file_extensions)
        for directory in ignore_directories:
            files_to_ignore += get_all_source_code_from_directory(
                directory, file_extensions)
    else:
        if len(files) < 2:
            print("Too few files to compare, you need to supply at least 2")
            return (ReturnCode.BAD_INPUT, {})
        for supplied_file in files:
            if not os.path.isfile(supplied_file):
                print("Supplied file does not exist:", supplied_file)
                return (ReturnCode.BAD_INPUT, {})
        source_code_files = files

    files_to_ignore += ignore_files if ignore_files else list()
    source_code_files = list(set(source_code_files) - set(files_to_ignore))
    if len(source_code_files) < 2:
        print("Not enough source code files found")
        return (ReturnCode.BAD_INPUT, {})
    source_code_files = [os.path.abspath(f) for f in source_code_files]

    # Get the absolute project root directory path to remove when printing out the results
    if project_root_dir:
        if not os.path.isdir(project_root_dir):
            print(
                "The project root directory does not exist or is not a directory:", project_root_dir)
            return (ReturnCode.BAD_INPUT, {})
        project_root_dir = os.path.abspath(project_root_dir)
        project_root_dir = os.path.join(
            project_root_dir, '')  # Add the trailing slash

    # Find the largest string length to format the textual output
    largest_string_length = len(max(source_code_files, key=len).replace(project_root_dir, ""))

    # Parse the contents of all the source files
    source_code = OrderedDict()
    for source_code_file in source_code_files:
        try:
            # read file but also recover from encoding errors in source files
            with open(source_code_file, 'r', errors='surrogateescape') as f:
                # Store source code with the file path as the key
                content = f.read()
                if only_code and source_code_file.endswith('py'):
                    content = remove_comments_and_docstrings(content)
                source_code[source_code_file] = content
        except Exception as err:
            print(f'ERROR: Failed to open file {source_code_file}, reason: {str(err)}')

    # Create a Similarity object of all the source code
    gen_docs = [[word.lower() for word in word_tokenize(source_code[source_file])]
                for source_file in source_code]
    dictionary = gensim.corpora.Dictionary(gen_docs)
    corpus = [dictionary.doc2bow(gen_doc) for gen_doc in gen_docs]
    tf_idf = gensim.models.TfidfModel(corpus)
    sims = gensim.similarities.Similarity(tempfile.gettempdir() + os.sep, tf_idf[corpus],
                                          num_features=len(dictionary))

    exit_code = ReturnCode.SUCCESS
    code_similarity = dict()
    for source_file in source_code:
        # Check for similarities
        query_doc = [w.lower()
                     for w in word_tokenize(source_code[source_file])]
        query_doc_bow = dictionary.doc2bow(query_doc)
        query_doc_tf_idf = tf_idf[query_doc_bow]

        short_source_file_path = source_file.replace(project_root_dir, '')
        conditional_print("\n\n\n" + CliColors.HEADER +
                          "Code duplication probability for " + short_source_file_path + CliColors.ENDC, json_output)
        conditional_print("-" * (largest_string_length +
                                 similarity_label_length), json_output)
        conditional_print(CliColors.BOLD + "%s %s" %
                          (file_column_label.center(largest_string_length), similarity_column_label) + CliColors.ENDC, json_output)
        conditional_print("-" * (largest_string_length +
                                 similarity_label_length), json_output)

        code_similarity[short_source_file_path] = dict()
        for similarity, source in zip(sims[query_doc_tf_idf], source_code):
            # Ignore similarities for the same file
            if source == source_file:
                continue
            similarity_percentage = similarity * 100
            # Ignore very low similarity
            if similarity_percentage < ignore_threshold:
                continue
            short_source_path = source.replace(project_root_dir, '')
            code_similarity[short_source_file_path][short_source_path] = round(
                similarity_percentage, 2)
            if similarity_percentage > fail_threshold:
                exit_code = ReturnCode.THRESHOLD_EXCEEDED
            color = CliColors.OKGREEN if similarity_percentage < 10 else (
                CliColors.WARNING if similarity_percentage < 20 else CliColors.FAIL)
            conditional_print("%s     " % (short_source_path.ljust(largest_string_length)) +
                              color + "%.2f" % (similarity_percentage) + CliColors.ENDC, json_output)
    if exit_code == ReturnCode.THRESHOLD_EXCEEDED:
        conditional_print(
            "Code duplication threshold exceeded. Please consult logs.", json_output)
    if json_output:
        result = {}
        with open('result.json', mode='w+', encoding='utf-8') as file:
            for key, v in code_similarity.items():
                v_sort = dict(sorted(filter(lambda y: y[1] >= 50, v.items()), key=lambda x: x[1], reverse=True))
                if v_sort:
                    result[key] = v_sort
            json.dump(result, file,  indent=4)

    return (exit_code, code_similarity)


if __name__ == "__main__":
    exit_code, _ = main()
    sys.exit(exit_code.value)
