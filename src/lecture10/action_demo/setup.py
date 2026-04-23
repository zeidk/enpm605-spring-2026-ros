from setuptools import find_packages, setup

package_name = 'action_demo'

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
    description='Action demo: action server with execute/cancel callbacks, action client with feedback and result handling.',
    license='Apache-2.0',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'navigate_server = action_demo.scripts.main_navigate_server:main',
            'navigate_client = action_demo.scripts.main_navigate_client:main',
        ],
    },
)
