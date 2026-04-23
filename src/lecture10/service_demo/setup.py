from setuptools import find_packages, setup

package_name = 'service_demo'

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
    description='Service demo: synchronous and asynchronous service clients with custom request/response interfaces.',
    license='Apache-2.0',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'trajectory_server = service_demo.scripts.main_trajectory_server:main',
            'trajectory_client_async = service_demo.scripts.main_trajectory_client_async:main',
            'trajectory_client_sync = service_demo.scripts.main_trajectory_client_sync:main',
        ],
    },
)
