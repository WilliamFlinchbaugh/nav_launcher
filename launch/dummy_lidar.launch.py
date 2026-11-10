import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    # Arguments
    pcd_path_arg = DeclareLaunchArgument(
        'pcd_path',
        default_value='/home/willi/nav_test_ws/resources/pcd_out_000004.pcd',
        description='Path to .pcd pointcloud to publish'
    )
    pcd_path = LaunchConfiguration('pcd_path')
    
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
    
    # Dummy Lidar
    dummy_lidar_node = Node(
        package='pcl_ros',
        executable='pcd_to_pointcloud',
        remappings=[('/cloud_pcd', '/ouster/points')],
        parameters=[{
            'file_name': pcd_path,
            'tf_frame': 'os_sensor',
            'publishing_period_ms': 100
        }]
    )

    return LaunchDescription([
        pcd_path_arg,
        tf_map_odom,
        tf_odom_base,
        tf_base_os,
        tf_base_footprint,
        crop_box_filter,
        traversability_node,
        rviz_node,
        nav2_node,
        dummy_lidar_node
    ])