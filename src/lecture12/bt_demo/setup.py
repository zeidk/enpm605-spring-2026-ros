import os
from glob import glob

from setuptools import find_packages, setup

package_name = "bt_demo"

setup(
    name=package_name,
    version="0.0.1",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        (os.path.join("share", package_name, "launch"), glob("launch/*.launch.py")),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="Z. Kootbally",
    maintainer_email="zeidk@umd.edu",
    description="Behavior tree demo using py_trees and py_trees_ros: drive-to-goal with P-control and Timeout/Spin recovery.",
    license="Apache-2.0",
    entry_points={
        "console_scripts": [
            "drive_to_goal_exe = bt_demo.scripts.main_drive_to_goal:main",
        ],
    },
)
