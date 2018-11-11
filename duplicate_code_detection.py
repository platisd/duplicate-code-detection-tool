import os
import sys
import argparse
import gensim
from nltk.tokenize import word_tokenize
from collections import OrderedDict

source_code_file_extensions = [".c", ".cpp", ".cc", ".java", ".py", ".cs"]

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def main():
    parser_description = "=== Duplicate Code Detection Tool ==="
    parser = argparse.ArgumentParser(description=parser_description)
    parser.add_argument("-p", "--path",
                        help="Relative path to repo to check for duplicates",
                        required=True)
    args = parser.parse_args()

    if not os.path.isdir(args.path):
        print("Repository does not exist or is not a directory:", args.path)
        sys.exit(1)

    # Get a list with all the source code files within the repository
    source_code_files = list()
    for dirpath, _, filenames in os.walk(args.path):
        for name in filenames:
            _, file_extension = os.path.splitext(name)
            if file_extension in source_code_file_extensions:
                filename = os.path.join(dirpath, name)
                source_code_files.append(filename)
    largest_string_length = len(max(source_code_files, key=len))

    # Parse the contents of all the source files
    source_code = OrderedDict()
    for source_code_file_path in source_code_files:
        with open(source_code_file_path, 'r') as f:
            # Store source code with the file path as the key
            source_code[source_code_file_path] = f.read()

    # Create a Similarity object of all the source code
    gen_docs = [[word.lower() for word in word_tokenize(source_code[source_file])]
                for source_file in source_code]
    dictionary = gensim.corpora.Dictionary(gen_docs)
    corpus = [dictionary.doc2bow(gen_doc) for gen_doc in gen_docs]
    tf_idf = gensim.models.TfidfModel(corpus)
    sims = gensim.similarities.Similarity('.',tf_idf[corpus],
                                          num_features=len(dictionary))

    for source_file in source_code:
        # Check for similarities
        query_doc = [w.lower() for w in word_tokenize(source_code[source_file])]
        query_doc_bow = dictionary.doc2bow(query_doc)
        query_doc_tf_idf = tf_idf[query_doc_bow]

        print("\n\n\n" + bcolors.HEADER + "Similarities for " + source_file + bcolors.ENDC)
        print("-" * (largest_string_length + 14))
        print(bcolors.BOLD + "%s %s" % ("File".center(largest_string_length), "Similarity (%)") + bcolors.ENDC)
        print("-" * (largest_string_length + 14))

        for similarity, source in zip(sims[query_doc_tf_idf], source_code):
            # Ignore similarities for the same file
            if source == source_file:
                continue
            similarity_percentage = similarity * 100
            color = bcolors.OKGREEN if similarity_percentage < 10.0 else (bcolors.WARNING if similarity_percentage < 20 else bcolors.FAIL)
            print ("%s     " % (source.ljust(largest_string_length)) + color + "%.2f" % (similarity_percentage) + bcolors.ENDC)

if __name__ == "__main__":
    main()
