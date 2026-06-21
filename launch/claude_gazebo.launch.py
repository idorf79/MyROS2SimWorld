#!/usr/bin/env python3
import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    GroupAction,
    AppendEnvironmentVariable,
    RegisterEventHandler,
)
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, Command
from launch_ros.actions import Node, PushRosNamespace


def generate_launch_description():
    use_sim_time = LaunchConfiguration("use_sim_time")
    pkg_ros_gz_sim = get_package_share_directory("ros_gz_sim")
    pkg_om_desc = get_package_share_directory("open_manipulator_description")
    pkg_rens = get_package_share_directory("myros2_sim_world")

    # Make model:// mesh URIs resolvable by Gazebo
    set_resource_path = AppendEnvironmentVariable(
        "GZ_SIM_RESOURCE_PATH",
        os.path.join(pkg_om_desc, ".."),
    )

    # Start Gazebo Sim
    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_ros_gz_sim, "launch", "gz_sim.launch.py")
        ),
        launch_arguments={"gz_args": "-r -v4 empty.sdf"}.items(),
    )

    # /clock bridge (sim time for controllers)
    clock_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        arguments=["/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock"],
        output="screen",
    )

    # ---------- OpenManipulator-X (namespace: open_manipulator) ----------
    om_ns = "open_manipulator"
    om_xacro = os.path.join(pkg_rens, "urdf", "open_manipulator_x.urdf.xacro")
    om_description = Command(["xacro ", om_xacro, " use_sim:=true"])

    om_rsp = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        namespace=om_ns,
        output="screen",
        parameters=[{
            "use_sim_time": use_sim_time,
            "robot_description": om_description,
            "frame_prefix": om_ns + "/",
        }],
    )

    om_spawn = Node(
        package="ros_gz_sim",
        executable="create",
        output="screen",
        arguments=[
            "-topic", "/open_manipulator/robot_description",
            "-name", om_ns,
            "-z", "0.0",
        ],
    )

    # Spawn controllers only after the entity is created
    om_cm = "/open_manipulator/controller_manager"
    om_controllers = [
        Node(package="controller_manager", executable="spawner", output="screen",
             arguments=[c, "--controller-manager", om_cm])
        for c in ["joint_state_broadcaster", "arm_controller", "gripper_controller"]
    ]
    om_load_controllers = RegisterEventHandler(
        OnProcessExit(target_action=om_spawn, on_exit=om_controllers)
    )

    return LaunchDescription([
        DeclareLaunchArgument("use_sim_time", default_value="true"),
        set_resource_path,
        gz_sim,
        clock_bridge,
        om_rsp,
        om_spawn,
        om_load_controllers,
    ])