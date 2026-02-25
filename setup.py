from setuptools import find_packages, setup

from chamber.version import get_version


setup(
    python_requires=">=3.10",
    name='skip-django-chamber',
    version=get_version(),
    description='Utilities library meant as a complement to django-is-core.',
    author='Lubos Matl, Oskar Hollmann',
    author_email='matllubos@gmail.com, oskar@hollmann.me',
    url='http://github.com/skip-pay/django-chamber',
    packages=find_packages(include=['chamber']),
    include_package_data=True,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Framework :: Django',
    ],
    install_requires=[
        'django>=5.2',
        'Unidecode>=1.1.1',
        'pyprind>=2.11.2',
        'python-magic>=0.4.27'
    ],
    extras_require={
        'boto3storage': ['django-storages<2.0', 'boto3'],
    },
)
