from distutils.core import setup

setup(
    name="jules42",
    version="0.1",
    py_modules=["jules42"],
    install_requires=["code42cli"],
    entry_points="""
        [code42cli.plugins]
        jules=jules42:main
    """,
)
