cmake_minimum_required(VERSION 3.5)
project(myros2_sim_world)

find_package(ament_cmake REQUIRED)

install(
  DIRECTORY launch urdf
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
