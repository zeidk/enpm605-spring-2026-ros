from setuptools import find_packages, setup

package_name = "bt_demo"

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
    description="Demo package for behavior trees with py_trees and py_trees_ros",
    license="Apache-2.0",
    entry_points={
        "console_scripts": [
            "drive_to_goal = bt_demo.scripts.main_drive_to_goal:main",
            "drive_to_goal_with_recovery = bt_demo.scripts.main_drive_to_goal_with_recovery:main",
        ],
    },
)
