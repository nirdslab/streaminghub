from setuptools import setup, find_packages

VERSION = '0.0.1'

ENTRY_POINTS = {
    'orange3.addon': (
        'streaming = streaming',
    ),
    # Entry point used to specify packages containing tutorials accessible
    # from welcome screen. Tutorials are saved Orange Workflows (.ows files).
    'orange.widgets.tutorials': (
        # Syntax: any_text = path.to.package.containing.tutorials
    ),
    # Entry point used to specify packages containing widgets.
    'orange.widgets': (
        # Syntax: any_text = path.to.package.containing.widgets
        'Streaming = streaming.widgets',
    ),
    # Widget help
    "orange.canvas.help": (
        'html-index = streaming.widgets:WIDGET_HELP_PATH',
    )
}

if __name__ == '__main__':
    setup(
        name="Orange3-Streaming",
        description="Orange3 add-on for working with data and metadata stream_labels through LSL",
        version=VERSION,
        author="Yasith Jayawardana",
        author_email="yasith@cs.odu.edu",
        url="https://github.com/nirdslab/streaminghub/",
        license='MIT',
        keywords=(
            'stream',
            'data',
            'metadata',
            'LSL',
        ),
        packages=find_packages(),
        package_data={
            "streaming.widgets": ["icons/*.svg",
                                  "*.js"],
            "streaming": ["datasets/*.tab",
                          "datasets/*.csv"],
        },
        install_requires=[
            'Orange3',
            'numpy',
            'pylsl',
            'pyQt5'
        ],
        entry_points=ENTRY_POINTS,
        classifiers=[
            "Development Status :: 1 - Planning",
            "Environment :: Plugins",
            "Intended Audience :: Developers",
            "License :: OSI Approved :: MIT License",
            "Natural Language :: English",
            "Operating System :: OS Independent",
            "Programming Language :: Python :: 3"
        ],
    )
