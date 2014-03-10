from distutils.core import setup

setup(
    name='pysheetmusic',
    description='Python sheet music library.',
    author='Ray',
    author_email='ray040123@gmail.com',
    packages=['pysheetmusic'],
    package_data={
        'pysheetmusic': ['shaders/*.glsl', 'schema/*.xsd', 'templates.png', 'templates.json'],
    },
)
