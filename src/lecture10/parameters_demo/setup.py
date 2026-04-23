import os
from glob import glob
from setuptools import find_packages, setup

package_name = 'parameters_demo'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'config'),
            glob('config/*.yaml')),
        (os.path.join('share', package_name, 'launch'),
            glob('launch/*.launch.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='zeid',
    maintainer_email='zeidk@umd.edu',
    description='Parameter demo: declaration, retrieval, YAML loading, runtime callbacks, and launch argument forwarding.',
    license='Apache-2.0',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'camera_demo = parameters_demo.scripts.main_camera_demo:main',
            'lidar_demo = parameters_demo.scripts.main_lidar_demo:main',
        ],
    },
)
