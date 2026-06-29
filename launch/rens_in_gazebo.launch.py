# Copyright (c) 2021 Juan Miguel Jimeno
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http:#www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    use_sim_time = True

    ekf_config_path = PathJoinSubstitution(
        [FindPackageShare("linorobot2_base"), "config", "ekf.yaml"]
    )

    robot_base = os.getenv('LINOROBOT2_BASE')
    urdf_path = PathJoinSubstitution(
        [FindPackageShare("linorobot2_description"), "urdf/robots", f"{robot_base}.urdf.xacro"]
    )
    
    description_launch_path = PathJoinSubstitution(
        [FindPackageShare('linorobot2_description'), 'launch', 'description.launch.py']
    )

    lidar_filter_file = PathJoinSubstitution(
        [FindPackageShare('linorobot2_bringup'),
        'config',
        'lidar_filters.yaml']
    )

    return LaunchDescription([    
        DeclareLaunchArgument(
            name='namespace', 
            default_value='',
            description='namespace'
        ),
        
        DeclareLaunchArgument(
            name='urdf', 
            default_value=urdf_path,
            description='URDF path'
        ),

        DeclareLaunchArgument(
            name='odom_topic', 
            default_value='/odom',
            description='EKF out odometry topic'
        ),

        DeclareLaunchArgument(
            name='spawn_x', 
            default_value='0.5',
            description='Robot spawn position in X axis'
        ),

        DeclareLaunchArgument(
            name='spawn_y', 
            default_value='0.0',
            description='Robot spawn position in Y axis'
        ),

        DeclareLaunchArgument(
            name='spawn_z', 
            default_value='0.0',
            description='Robot spawn position in Z axis'
        ),
            
        DeclareLaunchArgument(
            name='spawn_yaw', 
            default_value='0.0',
            description='Robot spawn heading'
        ),

        Node(
            package='ros_gz_sim',
            executable='create',
            output='screen',
            namespace=LaunchConfiguration('namespace'),
            arguments=[
                '-topic',  [ LaunchConfiguration('namespace'), '/' , 'robot_description'], 
                '-entity', 'linorobot2', 
                '-x', LaunchConfiguration('spawn_x'),
                '-y', LaunchConfiguration('spawn_y'),
                '-z', LaunchConfiguration('spawn_z'),
                '-Y', LaunchConfiguration('spawn_yaw'),
            ]
        ),

        Node(
            package="ros_gz_bridge",
            executable="parameter_bridge",
            namespace=LaunchConfiguration('namespace'),
            arguments=[
                [ LaunchConfiguration('namespace'),"/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock"],
                [ LaunchConfiguration('namespace'),"/cmd_vel@geometry_msgs/msg/Twist@gz.msgs.Twist"],
                [ LaunchConfiguration('namespace'),"/odom/unfiltered@nav_msgs/msg/Odometry[gz.msgs.Odometry"],
                [ LaunchConfiguration('namespace'),"/imu/data@sensor_msgs/msg/Imu[gz.msgs.IMU"],
                [ LaunchConfiguration('namespace'),"/joint_states@sensor_msgs/msg/JointState[gz.msgs.Model"],
                [ LaunchConfiguration('namespace'),"/scan_unfiltered@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan"],
                # [ LaunchConfiguration('namespace'),"/scan_gz@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan"],
                [ LaunchConfiguration('namespace'),"/camera/camera_info@sensor_msgs/msg/CameraInfo[gz.msgs.CameraInfo"],
                [ LaunchConfiguration('namespace'),"/camera/image@sensor_msgs/msg/Image[gz.msgs.Image"],
                [ LaunchConfiguration('namespace'),"/camera/depth_image@sensor_msgs/msg/Image[gz.msgs.Image"],
                [ LaunchConfiguration('namespace'),"/camera/points@sensor_msgs/msg/PointCloud2[gz.msgs.PointCloudPacked"],
            ],
            remappings=[
                ('/camera/camera_info', '/camera/color/camera_info'),
                ('/camera/image', '/camera/color/image_raw'),
                ('/camera/depth_image', '/camera/depth/image_rect_raw'),
                ('/camera/points', '/camera/depth/color/points'),
            ]
        ),

        Node(
            package='laser_filters',
            executable='scan_to_scan_filter_chain',
            namespace=LaunchConfiguration('namespace'),
            output='screen',
            parameters=[lidar_filter_file],
            # Remap input from '/scan_unfiltered' to '/scan' and output from '/scan_filtered' to '/scan'
            remappings=[
                ('/scan', '/scan_unfiltered'),
                ('/scan_filtered', '/scan'),
            ]
        ),

        Node(
            package='linorobot2_gazebo',
            executable='command_timeout',
            namespace=LaunchConfiguration('namespace'),
            name='command_timeout'
        ),

        Node(
            package='robot_localization',
            executable='ekf_node',
            namespace=LaunchConfiguration('namespace'),
            name='ekf_filter_node',
            output='screen',
            parameters=[
                {'use_sim_time': use_sim_time}, 
                ekf_config_path
            ],
            remappings=[
                ([ LaunchConfiguration('namespace'),"odometry/filtered" ], LaunchConfiguration("odom_topic")),
                ([ LaunchConfiguration('namespace'),"/tf" ], "tf"),
                ([ LaunchConfiguration('namespace'),"/tf_static" ], "tf_static"),
                ]
        ),

        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(description_launch_path),
            launch_arguments={
                'use_sim_time': str(use_sim_time),
                'publish_joints': 'false',
                'urdf': LaunchConfiguration('urdf'),
                'namespace': LaunchConfiguration('namespace'),
            }.items()
        )
    ])

#sources: 
#https://navigation.ros.org/setup_guides/index.html#
#https://answers.ros.org/question/374976/ros2-launch-gazebolaunchpy-from-my-own-launch-file/
#https://github.com/ros2/rclcpp/issues/940
