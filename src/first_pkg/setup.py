from setuptools import find_packages, setup

package_name = 'first_pkg'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='zeid',
    maintainer_email='zeidk@umd.edu',
    description='Introduction to ROS 2: simple nodes, publishers, subscribers, and timers.',
    license='Apache-2.0',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'minimal_node = first_pkg.minimal_node:main',
            'advanced_node = first_pkg.scripts.main_advanced_node:main',
            'interface_demo = first_pkg.scripts.main_interface_demo:main',
            'publisher_demo_node = first_pkg.scripts.main_publisher_demo_node:main',
            'subscriber_demo_node = first_pkg.scripts.main_subscriber_demo_node:main',
            'qos_demo_node = first_pkg.scripts.main_qos_demo_node:main',
        ],
    },
)
