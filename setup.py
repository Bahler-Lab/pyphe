from setuptools import setup

with open("README.md", "r") as fh:
    long_description = fh.read()
    
    
setup(name='pyphe',
      version='0.982',
      description='Python toolbox for phenotype analysis of arrayed microbial colonies',
      long_description=long_description,
      long_description_content_type="text/markdown",
      url='https://github.com/Bahler-Lab/pyphe',
      author='Stephan Kamrad',
      author_email='stephan.kamrad@gmail.com',
      license='MIT',
      packages=['pyphe'],
      scripts=['bin/pyphe-scan', 'bin/pyphe-scan-timecourse', 'bin/pyphe-growthcurves', 'bin/pyphe-analyse', 'bin/pyphe-quantify', 'bin/pyphe-interpret',
      'bin/pyphe-analyse-gui',
      'bin/pyphe-growthcurves.bat', 'bin/pyphe-analyse.bat', 'bin/pyphe-quantify.bat', 'bin/pyphe-interpret.bat',],
      install_requires=[
          'pandas',
          'matplotlib',
          'numpy',
          'seaborn',
          'scipy',
          'scikit-image',
          'scikit-learn'
      ],
      classifiers=[
        "Development Status :: 4 - Beta", 
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        ],
      python_requires='>=3.7')
