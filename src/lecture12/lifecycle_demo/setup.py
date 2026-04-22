from setuptools import find_packages, setup

package_name = "lifecycle_demo"

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
    description="Demo package for ROS 2 lifecycle nodes",
    license="Apache-2.0",
    entry_points={
        "console_scripts": [
            "sensor_pub_exe = lifecycle_demo.scripts.main_sensor_publisher_node:main",
            "self_cycling_exe = lifecycle_demo.scripts.main_self_cycling_node:main",
        ],
    },
)
