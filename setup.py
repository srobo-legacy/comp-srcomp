from setuptools import find_packages, setup


with open('README.md') as f:
    description = f.read()


setup(name='sr.comp',
      version='1.0.0',
      packages=find_packages(),
      namespace_packages=['sr', 'sr.comp'],
      description=description,
      author='Student Robotics Competition Software SIG',
      author_email='srobo-devel@googlegroups.com',
      install_requires=['nose >=1.3, <2',
                        'PyYAML >=3.11, <4',
                        'sr.comp.ranker >=1.0, <2',
                        'mock >=1.0.1, <2',
                        'python-dateutil >=2.2, <3'])
