import os
from glob import glob
from setuptools import find_packages, setup

package_name = "namespace_demo"

setup(
    name=package_name,
    version="0.0.1",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        (
            os.path.join("share", package_name, "launch"),
            glob(os.path.join("launch", "*launch.[pxy][yma]*")),
        ),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="Z. Kootbally",
    maintainer_email="zeidk@umd.edu",
    description="Demo package for ROS 2 namespaces",
    license="Apache-2.0",
    entry_points={
        "console_scripts": [
            "camera_demo = namespace_demo.scripts.main_camera_node:main",
        ],
    },
)
