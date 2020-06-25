import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name='qunetsim',
    version='0.1.0post5',
    scripts=['bin/template'],
    author="Stephen DiAdamo",
    author_email="stephen.diadamo@gmail.com",
    description="A Quantum Network Simulation Framework",
    license='MIT',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/tqsd/QuNetSim",
    download_url="https://github.com/tqsd/QuNetSim/releases/tag/0.1.0.post4",
    keywords=['quantum', 'networks', 'simulator', 'internet', 'QuNetSim'],
    install_requires=[
        'eqsn',
        'networkx',
        'numpy',
        'matplotlib',
    ],
    packages=setuptools.find_packages(),
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: MIT License',
        "Operating System :: OS Independent",
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
    ],
    python_requires='>=3.6',
)
