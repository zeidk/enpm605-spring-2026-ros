from setuptools import find_packages, setup

package_name = "bag_demo"

setup(
    name=package_name,
    version="0.0.1",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        (
            f"share/{package_name}/bags/nav_bag_cli",
            [
                "bags/nav_bag_cli/metadata.yaml",
                "bags/nav_bag_cli/nav_bag_cli_0.mcap",
            ],
        ),
        (
            f"share/{package_name}/bags/nav_bag_api",
            [
                "bags/nav_bag_api/metadata.yaml",
                "bags/nav_bag_api/nav_bag_api_0.mcap",
            ],
        ),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="Z. Kootbally",
    maintainer_email="zeidk@umd.edu",
    description="rosbag2_py demos: reading a bag, filtering by topic and time window, writing a bag, and extracting a robot trajectory from recorded odometry.",
    license="Apache-2.0",
    entry_points={
        "console_scripts": [
            "read_bag_exe = bag_demo.scripts.main_read_bag:main",
            "filter_write_bag_exe = bag_demo.scripts.main_filter_write_bag:main",
            "extract_trajectory_exe = bag_demo.scripts.main_extract_trajectory:main",
        ],
    },
)
