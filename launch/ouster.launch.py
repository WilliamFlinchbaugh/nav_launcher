import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch.launch_description_sources import PythonLaunchDescriptionSource, AnyLaunchDescriptionSource
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
        arguments=['0', '0', '0.6', '0', '0', '0', 'base_link', 'os_sensor']
    )
    tf_base_footprint = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        arguments=['0', '0', '0', '0', '0', '0', 'base_link', 'base_footprint']
    )
    
    # CropBox Filter
    crop_box_filter = Node(
        package='pcl_ros',
        executable='filter_crop_box_node',
        name='crop_box',
        remappings=[
            ('input', '/ouster/points'),
            ('output', '/ouster/points_filtered')
        ],
        parameters=[{
            'min_x': -0.5,
            'max_x': 0.5,
            'min_y': -0.5,
            'max_y': 0.5,
            'min_z': -2.0,
            'max_z': 2.0,
            'negative': True,
            'input_frame': 'os_sensor',
            'output_frame': 'os_sensor'
        }]
    )
    
    # Traversability Map
    traversability_node = Node(
        package='traversability_gridmap',
        executable='traversability_node',
        remappings=[('/point_cloud', '/ouster/points_filtered')],
        parameters=[{
            'global_mapping': False,
            'resolution': 0.05
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
        AnyLaunchDescriptionSource(os.path.join(ouster_launch_dir, 'sensor.launch.xml')),
        launch_arguments={
            'sensor_hostname': sensor_hostname,
            'timestamp_mode': 'TIME_FROM_ROS_TIME'
        }.items()
    )

    return LaunchDescription([
        sensor_hostname_arg,
        tf_map_odom,
        tf_odom_base,
        tf_base_os,
        tf_base_footprint,
        crop_box_filter,
        traversability_node,
        rviz_node,
        nav2_node,
        ouster_node
    ])