from setuptools import setup

setup(name='pyphe',
      version='0.91.20191202',
      description='Python toolbox for phenotype analysis of arrayed microbial colonies',
      url='https://github.com/Bahler-Lab/pyphe',
      author='Stephan Kamrad',
      author_email='stephan.kamrad@crick.ac.uk',
      license='MIT',
      packages=['pyphe'],
      scripts=['bin/pyphe-scan', 'bin/pyphe-scan-timecourse', 'bin/pyphe-growthcurves', 'bin/pyphe-analyse', 'bin/pyphe-quantify', 'bin/pyphe-analyse-gui'],
      install_requires=[
          'pandas',
          'matplotlib',
          'numpy',
          'seaborn',
          'scipy',
          'scikit-image',
          'scikit-learn'
      ],
      zip_safe=False)
