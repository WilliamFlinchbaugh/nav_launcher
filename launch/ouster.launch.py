import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    # Arguments
    sensor_hostname_arg = DeclareLaunchArgument(
        'sensor_hostname',
        default_value='192.168.1.100',
        description='The hostname or IP address for the Ouster sensor'
    )
    sensor_hostname = LaunchConfiguration('sensor_hostname')
    
    # Dummy Static Transforms
    tf_map_odom = Node(
        package='tf2_ros', 
        executable='static_transform_publisher', 
        arguments=['0', '0', '0', '0', '0', '0', 'map', 'odom']
    )
    tf_odom_base = Node(
        package='tf2_ros', 
        executable='static_transform_publisher', 
        arguments=['0', '0', '0', '0', '0', '0', 'odom', 'base_link']
    )
    tf_base_os = Node(
        package='tf2_ros', 
        executable='static_transform_publisher', 
        arguments=['0', '0', '0', '0', '0', '0', 'base_link', 'os_sensor']
    )
    tf_base_footprint = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        arguments=['0', '0', '0', '0', '0', '0', 'base_link', 'base_footprint']
    )
    
    # PointCloud to LaserScan Converter
    pc_to_laserscan_node = Node(
        package='pointcloud_to_laserscan',
        executable='pointcloud_to_laserscan_node',
        name='pointcloud_to_laserscan',
        remappings=[
            ('cloud_in', '/ouster/points'),
            ('scan', '/scan')
        ],
        parameters=[{
            'target_frame': 'os_sensor',
            'transform_tolerance': 0.01,
            'min_height': 0.0,
            'max_height': 2.0,
            'angle_min': -3.14159,
            'angle_max': 3.14159,
            'angle_increment': 0.0087,  # Roughly 0.5 degrees
            'scan_time': 0.1,
            'range_min': 0.2,
            'range_max': 100.0,
            'use_inf': True,
            'inf_epsilon': 1.0
        }]
    )

    # Nav2 Stack
    nav2_params_path = os.path.join(get_package_share_directory('nav_launcher'), 'config', 'nav2_params.yaml')
    nav2_launch_dir = os.path.join(get_package_share_directory('nav2_bringup'), 'launch')
    nav2_node = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(nav2_launch_dir, 'navigation_launch.py')),
        launch_arguments={
            'use_sim_time': 'false',
            'params_file': nav2_params_path
        }.items()
    )
    
    # Rviz
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', os.path.join(get_package_share_directory('nav2_bringup'), 'rviz', 'nav2_default_view.rviz')]
    )

    # Ouster Sensor
    ouster_launch_dir = os.path.join(get_package_share_directory('ouster_ros'), 'launch')
    ouster_node = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(ouster_launch_dir, 'sensor.launch.py')),
        launch_arguments={'sensor_hostname': sensor_hostname}.items()
    )

    return LaunchDescription([
        sensor_hostname_arg,
        tf_map_odom,
        tf_odom_base,
        tf_base_os,
        tf_base_footprint,
        pc_to_laserscan_node,
        rviz_node,
        nav2_node,
        ouster_node
    ])