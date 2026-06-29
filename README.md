# My ROS2 Sim World

This package can be used to create a virtual fleet of REnS robots.

Commands used:

## Start a Gazebo world with one Open Manipulator

```bash
ros2 launch myros2_sim_world gazebo_with_openmanipulator.launch.py
```

## Add the first REnS robot to the world

```bash
ros2 launch myros2_sim_world rens_in_gazebo.launch.py robot_name:=rens01 namespace:=/rens01
```

## Add a second REnS robot to the world

```bash
ros2 launch myros2_sim_world rens_in_gazebo.launch.py robot_name:=rens02 namespace:=/rens02 spawn_y:=-2.0
```

You can add more robots, but make sure to spawn them using different 'spawn_x', 'spawn_y' and/or 'spawn_z' arguments