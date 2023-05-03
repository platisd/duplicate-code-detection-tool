from setuptools import setup

setup(
    name='duplicate code detection tool',
    entry_points={
        'console_scripts': ['duplicate-code-detection=duplicate_code_detection:main']
    },
    py_modules=['duplicate_code_detection'],
    package_dir={
        'duplicate_code_detection': '.',
    },
    install_requires=[
        'gensim>=3.8',
        'nltk>=3.5',
        'astor>=0.8.1'
    ],
    setuptools_git_versioning={
        "enabled": True,
    },
    setup_requires=["setuptools-git-versioning<2"],
)
