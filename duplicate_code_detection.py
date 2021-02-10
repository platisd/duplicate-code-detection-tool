'''
A simple Python3 tool to detect similarities between files within a repository.

Document similarity code adapted from Jonathan Mugan's tutorial:
https://www.oreilly.com/learning/how-do-i-compare-document-similarity-using-python
'''
import os
import sys
import argparse
import gensim
import tempfile
import json
from nltk.tokenize import word_tokenize
from collections import OrderedDict

source_code_file_extensions = ["h", "c", "cpp", "cc", "java", "py", "cs"]
file_column_label = "File"
similarity_column_label = "Similarity (%)"
similarity_label_length = len(similarity_column_label)


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
    parser.add_argument("--ignore-directories", nargs="+", help="Directories to ignore.")
    parser.add_argument("--ignore-files", nargs="+", help="Files to ignore.")
    parser.add_argument("-j", "--json", type=bool, default=False, help="Print output as JSON.")
    parser.add_argument("--project-root-dir", type=str,
        help="The relative path to the project root directory to be removed when printing out results.")
    parser.add_argument("--file-extensions", nargs="+", default=source_code_file_extensions,
        help="File extensions to check for similarities.")
    parser.add_argument("--ignore-threshold", type=int, default=0,
        help="Don't print out similarity below the ignore threshold")
    args = parser.parse_args()

    # Determine which files to compare for similarities
    source_code_files = list()
    files_to_ignore = list()
    if args.directories:
        for directory in args.directories:
            if not os.path.isdir(directory):
                print("Path does not exist or is not a directory:", directory)
                sys.exit(1)
            source_code_files += get_all_source_code_from_directory(directory, args.file_extensions)
        for directory in args.ignore_directories:
            files_to_ignore += get_all_source_code_from_directory(directory, args.file_extensions)
    else:
        if len(args.files) < 2:
            print("Too few files to compare, you need to supply at least 2")
            sys.exit(1)
        for supplied_file in args.files:
            if not os.path.isfile(supplied_file):
                print("Supplied file does not exist:", supplied_file)
                sys.exit(1)
        source_code_files = args.files

    files_to_ignore += args.ignore_files if args.ignore_files else list()
    source_code_files = list(set(source_code_files) - set(files_to_ignore))
    if len(source_code_files) < 2:
        print("Not enough source code files found")
        sys.exit(1)

    # Get the project root directory path to remove when printing out the results
    project_root_index = 0
    if args.project_root_dir:
        if not os.path.isdir(args.project_root_dir):
            print("The project root directory does not exist or is not a directory:", args.project_root_dir)
            sys.exit(1)
        project_root_index = len(os.path.abspath(args.project_root_dir)) + 1  # Remove the first slash

    # Parse the contents of all the source files
    source_code = OrderedDict()
    for source_code_file in source_code_files:
        with open(source_code_file, 'r') as f:
            # Store source code with the file path as the key
            source_code[source_code_file] = f.read()

    # Create a Similarity object of all the source code
    gen_docs = [[word.lower() for word in word_tokenize(source_code[source_file])]
                for source_file in source_code]
    dictionary = gensim.corpora.Dictionary(gen_docs)
    corpus = [dictionary.doc2bow(gen_doc) for gen_doc in gen_docs]
    tf_idf = gensim.models.TfidfModel(corpus)
    sims = gensim.similarities.Similarity(tempfile.gettempdir() + os.sep, tf_idf[corpus],
                                          num_features=len(dictionary))

    largest_string_length = len(max(source_code_files, key=len))
    exit_code = 0
    code_similarity = dict()
    for source_file in source_code:
        # Check for similarities
        query_doc = [w.lower() for w in word_tokenize(source_code[source_file])]
        query_doc_bow = dictionary.doc2bow(query_doc)
        query_doc_tf_idf = tf_idf[query_doc_bow]

        short_source_file_path = source_file[project_root_index:]
        conditional_print("\n\n\n" + CliColors.HEADER +
              "Code duplication probability for " + short_source_file_path + CliColors.ENDC, args.json)
        conditional_print("-" * (largest_string_length + similarity_label_length), args.json)
        conditional_print(CliColors.BOLD + "%s %s" %
              (file_column_label.center(largest_string_length), similarity_column_label) + CliColors.ENDC, args.json)
        conditional_print("-" * (largest_string_length + similarity_label_length), args.json)

        code_similarity[short_source_file_path] = dict()
        for similarity, source in zip(sims[query_doc_tf_idf], source_code):
            # Ignore similarities for the same file
            if source == source_file:
                continue
            similarity_percentage = similarity * 100
            # Ignore very low similarity
            if similarity_percentage < args.ignore_threshold:
                continue
            short_source_path = source[project_root_index:]
            code_similarity[short_source_file_path][short_source_path] = round(similarity_percentage, 2)
            if similarity_percentage > args.fail_threshold:
                exit_code = 1
            color = CliColors.OKGREEN if similarity_percentage < 10 else (
                CliColors.WARNING if similarity_percentage < 20 else CliColors.FAIL)
            conditional_print("%s     " % (short_source_path.ljust(largest_string_length)) +
                  color + "%.2f" % (similarity_percentage) + CliColors.ENDC, args.json)
    if exit_code == 1: 
        conditional_print("Code duplication threshold exceeded. Please consult logs.", args.json)
    if args.json:
        similarities_json = json.dumps(code_similarity, indent=4)
        print(similarities_json)
    exit(exit_code)

if __name__ == "__main__":
    main()
