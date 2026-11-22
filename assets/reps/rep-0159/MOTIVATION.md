# REP 159 Motivation: full use cases

The full use cases behind the Motivation section of REP 159 (`_posts/rep-0159:2026.md`), which summarizes them.
The wording comes from the earlier draft of that section, except the paragraph on Gazebo vendor packages under Use Case 1, which describes how ROS gets Gazebo today.

## Use Case 1 - Public Project Coordination

The first is to enable better collaboration between our existing open source projects.
Two major projects that can be represented as distros are the ROS and Gazebo projects.
ROS is already managed explicitly as a distro.
Gazebo is also effectively managed as a distro, but is not formalized in the same way.
And when ROS imports Gazebo as a dependency it is done manually.
The goal of this proposal is to enable this dependency to be explicitly modelled and to automate that import and coordination process.
Furthermore we can also reduce the need for very similar test and build infrastructure.

The result is that we can:

* Formalize the Gazebo Rotary release as a distro.
* Create and build releases using the rosdistro tooling and infrastructure.
* Make ROS Rolling depend on Gazebo Rotary, automatically importing the built binaries from the latest (explicitly imported) sync release.
  * As it is explicitly imported it can also be rolled back if there is an issue.
  * The binaries will be the same.
  * Queries for Gazebo Rotary packages in ROS Rolling will alias transparently, so that the user does not need to know which layer a package came from.
  * This brings both rolling releases together conveniently.
* When Gazebo creates Gazebo M and ROS M is created, ROS M can be pointed at Gazebo M while Rolling continues to point at Rotary.

Today, since ROS 2 Jazzy, ROS gets Gazebo through vendor packages, 18 per ROS distribution, which fetch the Gazebo sources at a pinned version and rebuild them on the ROS buildfarm ([docs](https://gazebosim.org/docs/latest/ros2_gz_vendor_pkgs/)).
Each Gazebo library is built and shipped twice, by packages.osrfoundation.org and by packages.ros.org, and each vendor package keeps a branch, version and bloom track per ROS distribution.
Every stable Gazebo release needs a vendor pull request, its CI, a bloom release and a rosdistro review before ROS users get it at the next sync; until then the two repositories ship different versions of the same library.
A `binary_import` extension removes the second build, but the CMake shims the vendor packages provide (unversioned `find_package(gz-math)`) would still need a home.

## Use Case 2 - Externally Managed Distro Extension

The above use case covers the coordination of major projects between each other.
A closely related use case is an external maintainer who wants to maintain packages that are compatible with the public distribution but keep them in a separate source.
The intent is for these packages to be used with the upstream repositories, but the extension repository is maintained by the third party.
There are several reasons why it might make sense to do this separately:

* The packages need to follow a different release cadence.
* The packages need a different trust level.
* The packages do not comply with the upstream distro's policies or governance.
  For example, a license that is not OSI approved.
  Or the packages are too large for standard releases, or need special hardware to be built.

To use these externally managed distros, users have to explicitly add and enable the additional source repositories on their system, because they need to be explicitly trusted by the system administrator.

Community members that might fall into this case include:

* A vendor releasing a custom hardware driver that contains a binary blob, which they redistribute to their customers.

## Use Case 3 - Private Distro Extension

There are also many cases where someone may want to extend a ROS distro in a binary compatible way but keep the results private.
Common use cases for this include:

* Commercial software companies, for example with the results available behind a paywall or subscription mechanism.
* Internal customer use only, for example hosted on an intranet or VPN.
* A set of packages for customized support of a robot, for internal usage or private coordinated development.
* If we do this well enough, a lab manager or TA could create an example scenario for a project, and each student could create their own extended rosdistro for their projects.
  The students rely on binary builds of all the core elements and of the shared packages, and only need to build their own packages.

To enable this, the private distro maintainer sets up their distro to extend a public one and produces the extra private packages, which are compatible with the upstream ones.
As in the previous use case, the user has to enable the extra source repository, and get access through whatever mechanism the maintainer implements.
Access control is not prescribed or provided by rosdistro; the distro maintainer sets it up as best fits their application.

## Use Case 4 - Private Distro Rebuild + Extend

Instead of using the `binary_import` mechanism and only building new packages on top of the binary builds, a maintainer could select the `source_rebuild` extension mechanism.
This might be chosen for improved trust in the binaries produced, at the cost of additional computation.
With appropriate caching it can also reproduce the builds in case an upstream resource disappears.

This does not preclude extending, so additional packages could also be included in the distro.
The rebuilt packages would be expected to be generally compatible with the upstream packages.
However, the rebuilt packages would be named with the extension distro's name, not the upstream distro's name, because they could end up binary incompatible.
This also unlocks the ability to override a specific package in the upstream distro.
Doing so would potentially break compatibility (ABI, but now also API), but with the new name the maintainer is free to set their own expectations for compatibility and stability.
