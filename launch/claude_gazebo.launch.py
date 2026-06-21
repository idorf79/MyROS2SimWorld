#!/usr/bin/env python3
import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, GroupAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution, Command
from launch.actions import AppendEnvironmentVariable
from launch_ros.actions import Node, PushRosNamespace
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    use_sim_time = LaunchConfiguration("use_sim_time")
    pkg_ros_gz_sim = get_package_share_directory("ros_gz_sim")


    # add to your LaunchDescription, before the gz_sim include:
    AppendEnvironmentVariable(
        "GZ_SIM_RESOURCE_PATH",
        os.path.join(get_package_share_directory("open_manipulator_description"), "..")
    ),


    # --- Start Gazebo Sim (server + GUI) ---
    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_ros_gz_sim, "launch", "gz_sim.launch.py")
        ),
        # -r runs immediately; swap empty.sdf for your world
        launch_arguments={"gz_args": "-r -v4 empty.sdf"}.items(),
    )

    # --- /clock bridge (required for controllers / use_sim_time) ---
    clock_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        arguments=["/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock"],
        output="screen",
    )

    # ===================================================================
    # ROBOT 1: Linorobot2
    # ===================================================================
    lino_ns = "linorobot2"
    pkg_lino = get_package_share_directory("linorobot2_description")
    lino_xacro = os.path.join(pkg_lino, "urdf", "robots", "2wd.urdf.xacro")
    lino_description = Command([
        "xacro ", lino_xacro,
        " robot_name:=", lino_ns,
        " namespace:=", lino_ns,
    ])

    linorobot2 = GroupAction([
        PushRosNamespace(lino_ns),
        Node(
            package="robot_state_publisher",
            executable="robot_state_publisher",
            output="screen",
            parameters=[{
                "use_sim_time": use_sim_time,
                "robot_description": lino_description,
                "frame_prefix": lino_ns + "/",
            }],
        ),
        Node(
            package="ros_gz_sim",
            executable="create",
            output="screen",
            arguments=[
                "-topic", "robot_description",   # namespaced -> /linorobot2/robot_description
                "-name", lino_ns,
                "-x", "0.0", "-y", "0.0", "-z", "0.1",
            ],
        ),
    ])

    # ===================================================================
    # ROBOT 2: OpenManipulator-X
    # ===================================================================
    om_ns = "open_manipulator"
    pkg_om = get_package_share_directory("open_manipulator_description")
    om_xacro = os.path.join(
        pkg_om, "urdf", "open_manipulator_x", "open_manipulator_x.urdf.xacro"
    )
    om_description = Command([
        "xacro ", om_xacro,
        " use_sim:=true",
    ])

    open_manipulator = GroupAction([
        PushRosNamespace(om_ns),
        Node(
            package="robot_state_publisher",
            executable="robot_state_publisher",
            output="screen",
            parameters=[{
                "use_sim_time": use_sim_time,
                "robot_description": om_description,
                "frame_prefix": om_ns + "/",
            }],
        ),
        Node(
            package="ros_gz_sim",
            executable="create",
            output="screen",
            arguments=[
                "-topic", "robot_description",
                "-name", om_ns,
                "-x", "1.0", "-y", "0.0", "-z", "0.0",
            ],
        ),
    ])

    return LaunchDescription([
        DeclareLaunchArgument("use_sim_time", default_value="true"),
        gz_sim,
        clock_bridge,
        linorobot2,
        open_manipulator,
    ])