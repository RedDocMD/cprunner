import setuptools

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setuptools.setup(
    name='cprunner',
    version="0.1.0",
    author="Deep Majumder",
    author_email="deep.majumder2019@gmail.com",
    description="A helper script to run competitive programs and diff output",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/RedDocMD/cprunner",
    project_urls={
        "Bug Tracker": "https://github.com/RedDocMD/cprunner/issues"
    },
    license='GPLv3',
    classifiers=[
        "Programming Language :: Python :: 3.6",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Competitive Programming :: Build Tools",
        "License :: OSI Approved :: GPL v3",
    ],
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    python_requires=">=3.6",
    install_requires=[
        "termcolor"
    ],
    entry_points={
        'console_scripts': [
            'cpr=cprunner.run:executor'
        ]
    }
)
