from setuptools import setup

setup(name='pyphe',
      version='0.9',
      description='Python toolbox for phenotype analysis of arrayed microbial colonies',
      url='https://github.com/Bahler-Lab/pyphe',
      author='Stephan Kamrad',
      author_email='stephan.kamrad@crick.ac.uk',
      license='MIT',
      packages=['pyphe'],
      scripts=['bin/pyphe-scan', 'bin/pyphe-scan', 'bin/pyphe-scan-timecourse', 'bin/pyphe-growthcurves', 'bin/pyphe-analysis', 'bin/pyphe-quantify'],
      install_requires=[
          'pandas',
          'matplotlib',
          'numpy',
          'seaborn',
          'scipy',
          'PySimpleGUI'
      ],
      zip_safe=False)
