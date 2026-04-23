from setuptools import find_packages, setup

package_name = "message_demo"

setup(
    name=package_name,
    version="0.0.1",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="Z. Kootbally",
    maintainer_email="zeidk@umd.edu",
    description="Custom message demo: publishing and subscribing with user-defined message types.",
    license="Apache-2.0",
    entry_points={
        "console_scripts": [
            "task_status_demo = message_demo.scripts.main_task_status_demo:main",
        ],
    },
)
