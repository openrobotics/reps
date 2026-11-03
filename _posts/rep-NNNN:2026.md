---
REP: 149
title: Package Manifest Format Three Specification
author: Dirk Thomas
tag: Final
category: Standards Track
date: '2017-10-11'
---

## Outline

1.  [Abstract](#abstract)
2.  [Motivation](#motivation)
3.  [Rationale](#rationale)
4.  [Data Representation](#data-representation)
5.  [Compatibility](#compatibility)
6.  [Schema](#schema)
7.  [References](#references)
8.  [Copyright](#copyright)

Significant changes compared to REP-0140 [2]_ are highlighted in <font color="red">red</font>.
Trivial changes appear in <font color="blue">blue</font>.

## Abstract

This REP specifies the third `package.xml` format, which is an update to
the previous versions specified in REP-0127[^1] and REP-0140[^2].
{: style="color:blue"}

## Motivation

This REP covers three separate topics which are described in the
following subsections.
{: style="color:red"}

### Dependency groups

Several ROS packages aggregate dependencies of a specific type, e.g.
_message_generation_ in ROS 1 or
_rmw_implementation_ in ROS 2. They explicitly list the
dependencies which are being used during the release process. But when
building from source they need to be updated to add custom message
generators or rmw implementations.
{: style="color:red"}

The goal is to allow specifying this kind of group dependency in a way
that a from-source build can process the custom packages accordingly to
make them available to the package even though the package doesn\'t list
an explicit dependency on the custom package.
{: style="color:red"}

### ABI version on the package level

When building binary packages on the ROS buildfarm there is no
assumption about ABI compatibility. When a new Debian package has been
built all downstream packages are being rebuilt too in order to ensure
they still work together. This makes e.g. releasing a core package like
_catkin_ or _roscpp_ particularly costly. Due to
that overhead changes which should be released rather sooner than later,
e.g. a documentation fix or simple bugfix in a _.cpp_ file,
are being held back to group them with other changes to make the rebuild
effort worthwhile.
{: style="color:red"}

In order to allow package releases without enforcing a rebuild of all
downstream packages a package should be able to declare if such a
rebuild is necessary or not.
{: style="color:red"}

### Packages across ROS 1 and ROS 2

In order for a ROS package to work with ROS 1 and ROS 2 from a single
source the dependencies listed in the package manifest are a problem.
E.g. in ROS 1 a package needs to depend on _roscpp_ where as
in ROS 2 it needs to depend on _rclcpp_. This amends the
manifest to support this use case.
{: style="color:red"}

The necessary part outside of the manifest to make a package compatible
with ROS 1 as well as ROS 2 is explicitly not part of this document. In
general it is possible to conditionally handle those cases in
programming languages like CMake, C++, Python, etc.
{: style="color:red"}

See [Alternatives for Universal
Packages](#alternatives-for-universal-packages) for options not chosen.
{: style="color:red"}

## Rationale

REP-0127[^3] and REP-0140[^4] provide the `package.xml` design rationale
for format one and two, which is not repeated here.
{: style="color:blue"}

### Group dependencies
<!-- <font color="red"> -->

Packages can already express direct dependencies on other individual
packages, but this is not sufficient for cases where a package needs to
be built after all instances of a particular kind of package. Instead
packages need to be able to declare a dependency on packages without
using their name directly.
{: style="color:red"}

One alternative is to \"reverse\" the dependency declaration so that a
package states that it \"wants\" to be a dependency of another package.
But that approach does not work in the case where the other package gets
forked under a different name since the \"reverse\" dependency would
still only reference the original package name.
{: style="color:red"}

Therefore the dependency declaration is being decoupled into two parts:
{: style="color:red"}

> - *(A)* packages declaring a dependency on a \"group dependency
>   name\", e.g. _ros1_bridge_ can depend on the group
>   \"message_packages\"
> - *(B)* packages declaring to be part of a group dependency identified
>   by its name, e.g. _sensor_msgs_ can declare itself part
>   of the \"message_packages\" group
{: style="color:red"}

During a from-source build the build tool can use the information from
all package manifests in the workspace to identify group dependencies.
It can use this information to process group members before the packages
declaring the group dependency as if the dependency was declared
explicitly using the existing _depend_ tags.
{: style="color:red"}

The group dependency (A) is declared with a [group_depend](#group_depend-multiple)
tag. The content of the group dependency tag is the name of the group.
Leading and trailing whitespace is being ignored from the name and for
consistency it is required to follow the naming rules for packages.
{: style="color:red"}

The membership of a group (B) is declared with a
[member_of_group](#member_of_group-multiple) tag.
{: style="color:red"}

### ABI version attribute

The early draft of REP 127 (\"package.xml format 1\") proposed an
attribute (_abi_version_) to identify the package version
which is considered \"compatible\".
{: style="color:red"}

Since at the time no consensus could be reached about specifying ABI
compatibility in general (for packages as well as libraries) the
proposed attribute was removed from the draft (see related
discussions[^5],[^6], [^7]).
{: style="color:red"}

Since then the number of packages in a ROS distributions has increased
(e.g. Indigo has more than 2500 packages) as well as the number of
platforms ROS provides binary packages for. Therefore the need to avoid
unnecessary rebuilds has increased. It is also desired to be able to
encourage more frequent releases if they don\'t require downstream
packages to be rebuilt.
{: style="color:red"}

### Packages across ROS 1 and ROS 2

In order for a ROS package to work with ROS 1 and ROS 2 from a single
source the manifest must describe the package\'s requirements for both
cases. This means describing different dependencies
(_rclcpp_ vs _roscpp_), and possibly a different
build type (_catkin_ vs _ament_cmake_).
{: style="color:red"}

The `condition` attribute as defined for [\<build_depend\>
(multiple)](#build_depend-multiple) is intended to satisfy this use case.
A package may define one manifest where all tags supporting the _condition_
attribute are conditioned on the environment variable _ROS_VERSION_. The
value is a string with an integer: **1** or **2**.
{: style="color:red"}

Various tools will need to be aware of the condition responsible for
choosing which dependencies should be used:
{: style="color:red"}

> - _bloom_
> - _rosdep_
> - _rosinstall_generator_
> - the build tool
{: style="color:red"}

A new field must be added to the distribution file specified in REP 143
[^8] so that a ROS distribution \"knows\" which ROS version it
represents.
{: style="color:red"}

The build tool does not have access to the ROS distribution metadata. It
could either use information provided by an environment variable or fall
back to consider *all* dependencies (independent of their annotation)
and work on the assumption that the workspace contains a set of
consistent packages and additional dependencies from other ROS versions
are not available in the workspace.
{: style="color:red"}

## Data Representation

The package manifest is an XML file, with restricted syntax.

The only top-level element allowed is `<package>`. Immediately
subordinate to that are several required or optional elements, defined
here. No other tags are permitted directly under the `<package>`
element.

### \<package format=\"3\"\>

The `<package>` tag is the unique top-level tag in a `package.xml` file.
All other tags are nested under it.
{: style="color:blue"}

#### Attributes

> `format="NUMBER"`
>
> Specifying the `package.xml` format being used. If not set,
> `format="1"` would be assumed, which is *not* the format described
> here. For this interface, you *must* specify `format="3"`. If you are
> using a different format, please refer to the relevant specification.
> REP-0127[^9] described format one, REP-0140[^10] format two.

### Required Tags

The required tags in a `package.xml` file provide package meta-data:

> - [\<name\>](#name)
> - [\<version\>](#version)
> - [\<description\>](#description)
> - [\<maintainer\> (multiple, but at least one)](#maintainer-multiple-but-at-least-one)
> - [\<license\> (multiple, but at least one)](#license-multiple-but-at-least-one)

### Optional Tags

#### Meta-information

Optional, but recommended, meta-data include the names of the original
authors and links to support documentation.

> - [\<url\> (multiple)](#url-multiple)
> - [\<author\> (multiple)](#author-multiple)

#### Dependencies

The dependencies and relations to other packages and system packages
have been discussed in[^11]. They are described using:

> - [\<build_depend\> (multiple)](#build_depend-multiple)
> - [\<build_export_depend\> (multiple)](#build_export_depend-multiple)
> - [\<buildtool_depend\> (multiple)](#buildtool_depend-multiple)
> - [\<buildtool_export_depend\> (multiple)](#buildtool_export_depend-multiple)
> - [\<exec_depend\> (multiple)](#exec_depend-multiple)
> - [\<depend\> (multiple)](#depend-multiple)
> - [\<doc_depend\> (multiple)](#doc_depend-multiple)
> - [\<test_depend\> (multiple)](#test_depend-multiple)
> - [\<conflict\> (multiple)](#conflict-multiple)
> - [\<replace\> (multiple)](#replace-multiple)

These dependency tags are used with both system packages and ROS
packages. For system dependencies specify the rosdep key name, for ROS
dependencies use the package name.

The dependency graph must be acyclic. No package may directly or
indirectly depend on itself.

#### Group dependencies and memberships

> The group dependencies and membership of groups are described using:
>
> > - [\<group_depend\> (multiple)](#group_depend-multiple)
> > - [\<member_of_group\> (multiple)](#member_of_group-multiple)
>
> These group dependencies are only applied in from-source builds and
> are being ignored in the release process.
>
> The dependency graph must be acyclic even when considering group
> dependencies.
{: style="color:red"}

#### Various

There is a need for additional meta-data in the manifest for other tools
that work with packages, like message generators and plugin discovery.
Tags for that kind of information are wrapped within this tag:

> - [\<export\>](#export)

Some `<export>` tags used by catkin are defined below. Others are
defined by various tools, which must specify their own specific tag
structures.

### Example

```xml
<package format="2">
  <name>my_package</name>
  <version>1.2.3</version>
  <description>
    This is my package's description.
  </description>
  <maintainer email="someone@example.com">Someone</maintainer>

  <license>BSD</license>
  <license file="LICENSE">LGPL</license>

  <url type="website">http://wiki.ros.org/my_package</url>
  <url type="repository">http://www.github.com/my_org/my_package</url>
  <url type="bugtracker">http://www.github.com/my_org/my_package/issues</url>
  <author>John Doe</author>
  <author email="jane.doe@example.com">Jane Doe</author>

  <buildtool_depend>catkin</buildtool_depend>
  <build_depend version_gte="1.1" version_lt="2.0">genmsg</build_depend>

  <depend>roscpp</depend>

  <build_depend>libgstreamer0.10-dev</build_depend>
  <build_export_depend>libgstreamer0.10-dev</build_export_depend>
  <exec_depend>libgstreamer0.10-0</exec_depend>

  <test_depend>gtest</test_depend>

  <doc_depend>doxygen</doc_depend>

  <conflict>alternative_implementation</conflict>

  <replace>my_old_package</replace>

  <export>
    ...
  </export>
</package>
```

### \<name\>

The package name must start with a letter and contain only lowercase
alphabetic, numeric or underscore characters[^12]. The package name
should be unique within the ROS community. It may differ from the folder
name into which it is checked out, but that is *not* recommended.

The following recommended exemptions apply, which are optional for
implementations:

- Dashes may be permitted in package names. This is to support
  maintaining a consistent dependency name when transitioning back and
  forth between a system dependency and in-workspace package, since many
  rosdep keys contain dashes (inherited from the Debian/Ubuntu name).
- In support of some legacy packages, capital letters may also be
  accepted in the package name, with a validation warning.

### \<version\>

The version number of the package in the format `MAJOR.MINOR.PATCH`
where each part is numeric only.

#### Attributes

> `compatibility="MAJOR.MINOR.PATCH"`
>
> Specifying the version up to which the package is compatible with,
> i.e. always pick the oldest compatible version. If not set, the same
> value as specified in the `version` tag is assumed.
>
> \"Compatibility\" in this context guarantees that downstream packages
> built against the older version will continue to work with a newer
> version without the need to be rebuilt. This includes but is not
> limited to ABI compatibility. Changes in other parts of a package
> (CMake, Python, etc.) could also require downstream packages to be
> rebuilt and therefore not qualify as \"compatible\".
{: style="color:red"}

### \<description\>

The description of the package. It can consist of multiple lines and may
contain XHTML. But depending on where the description is used XML tags
and multiple whitespaces might be stripped.

### \<maintainer\> (multiple, but at least one)

The name of the person maintaining the package. All packages require a
maintainer. For orphaned packages see below.

#### Attributes

> `email="name@domain.tld"` *(required)*
>
> > Email address of the maintainer.

An orphaned package is one with no current maintainer. Orphaned packages
should use the following maintainer information to guide volunteers how
they can claim maintainership:

#### Example

```xml
<maintainer email="ros-orphaned-packages@googlegroups.com">Unmaintained see http://wiki.ros.org/MaintenanceGuide#Claiming_Maintainership</maintainer>
```

### \<license\> (multiple, but at least one)

Name of license for this package, e.g. BSD, GPL, LGPL. In order to
assist machine readability, only include the license name in this tag.
For multiple licenses multiple separate tags must be used. A package
will have multiple licenses if different source files have different
licenses. Every license occurring in the source files should have a
corresponding `<license>` tag. For any explanatory text about licensing
caveats, please use the `<description>` tag.

Most common open-source licenses are described on the [OSI
website](http://www.opensource.org/licenses/alphabetical).

Commonly used license strings:

> - Apache-2.0
> - BSD
> - Boost Software License
> - GPLv2
> - GPLv3
> - LGPLv2.1
> - LGPLv3
> - MIT
> - Mozilla Public License Version 1.1

#### Attributes

> `file="FILE"` *(optional)*
>
> A path relative to the `package.xml` file containing the full license
> text.
>
> Many licenses require including the license text when redistributing
> the software. E.g. the `Apache License, Version 2.0` states in
> paragraph 4.1:
>
> > \"You must give any other recipients of the Work or Derivative Works
> > a copy of this License\"
> {: style="color:blue"}
{: style="color:blue"}

### \<url\> (multiple)

A Uniform Resource Locator for the package\'s website, bug tracker or
source repository.

It is a good idea to include `<url>` tags pointing users to these
resources. The website is commonly a wiki page on `ros.org` where users
can find and update information about the package.

#### Attributes

> `type="TYPE"` *(optional)*
>
> The type should be one of the following identifiers: `website`
> (default), `bugtracker` or `repository`.

### \<author\> (multiple)

The name of a person who is an author of the package, as acknowledgement
of their work and for questions.

#### Attributes

> `email="name@domain.tld"` *(optional)*
>
> > Email address of author.

### Dependency tags

#### \<build_depend\> (multiple)

Declares a rosdep key or ROS package name that this package requires at
build-time. For system packages, the rosdep key will normally specify
the \"development\" package, which frequently ends in `"-dev"`.

The `build` and `buildtool` dependencies are used to determine the build
order of multiple packages.

##### Attributes

> All dependencies and relationships may restrict their applicability to
> particular versions. For each comparison operator an attribute can be
> used. Two of these attributes can be used together to describe a
> version range.
>
> `version_lt="VERSION"` *(optional)*
>
> The dependency to the package is restricted to versions less than the
> stated version number.
>
> `version_lte="VERSION"` *(optional)*
>
> The dependency to the package is restricted to versions less or equal
> than the stated version number.
>
> `version_eq="VERSION"` *(optional)*
>
> The dependency to the package is restricted to a version equal than
> the stated version number.
>
> `version_gte="VERSION"` *(optional)*
>
> The dependency to the package is restricted to versions greater or
> equal than the stated version number.
>
> `version_gt="VERSION"` *(optional)*
>
> The dependency to the package is restricted to versions greater than
> the stated version number.
>
> `condition="CONDITION_EXPRESSION"`
> {: style="--highlighter-rouge-color:red;"}
>
> Every dependency can be conditional on a condition expression. If the
> condition expression evaluate to \"true\" the dependency is being used
> and considered as if it doesn\'t have a condition attribute. If the
> condition expression evaluate to \"false\" the dependency is being
> ignored and considered as if it doesn\'t exist.
> {: style="color:red"}
>
> The condition expression can consist of:
> {: style="color:red"}
>
> > - parenthesis (which must be balanced)
> > - logical operators _and_ and _or_
> > - comparison operators: _==_, _!=_, _\<_, _\<=_, _\>_, _\>=_
> > - variable names which start with a _\$_ sign and are
> >   followed by alphanumerics and underscores
> > - literals which can only contain alphanumerics, underscores and
> >   dashes
> > - quoted literals (single or double quotes) which can contain any
> >   characters except the used quote character
> > - arbitrary whitespaces between these tokens
> {: style="color:red"}
>
> An expression syntactically correct by the previous definition will be
> evaluated as follows:
> {: style="color:red"}
>
> > - All variables are substituted by their values and treated as
> >   strings.
> > - All literals are also treated as strings.
> > - The resulting expression is evaluated as a Python interpreter
> >   would evaluate it. Please note that the comparison operators only
> >   do a *string* comparison and don\'t attempt to interpret the
> >   string as a numerical value.
> {: style="color:red"}
>
> Tools may populate the values for the variables starting with a
> _\$_ sign in different ways, but typically they are
> evaluated as environment variables.
> {: style="color:red"}
>
> As an example, a dependency might only be needed in a ROS 1
> environment. Such dependency could be described as follows where the
> value of _\$ROS_VERSION_ is coming from an environment variable:
> {: style="color:red"}
>
> `<depend condition="$ROS_VERSION == 1">roscpp</depend>`
> {: style="--highlighter-rouge-color:red;"}

#### \<build_export_depend\> (multiple)

Declares a rosdep key or ROS package name that this package needs as
part of some build interface it exports. For system packages, the rosdep
key will normally specify the \"development\" package, which frequently
ends in `"-dev"`.

The `<build_export_depend>` declares a transitive build dependency. A
common example is when one of your dependencies provides a header file
included in some header exported by your package. Even if your package
does not use that header when building itself, other packages depending
on your header *will* require those transitive dependencies when they
are built.

##### Attributes

> The same attributes as for [\<build_depend\> (multiple)](#build_depend-multiple).

#### \<buildtool_depend\> (multiple)

Declares a rosdep key or ROS package name for a tool that is executed
during the build process. For cross-compilation, one must distinguish
these from normal build dependencies, which may be linked with your
package and must be compiled for the target architecture, not the build
system. For system packages, the rosdep key will normally specify the
\"development\" package, which frequently ends in `"-dev"`.

##### Attributes

> The same attributes as for [\<build_depend\> (multiple)](#build_depend-multiple).

#### \<buildtool_export_depend\> (multiple)

Declares a rosdep key or ROS package name that this package exports
which must be compiled and run on the build system, not the target
system. For cross-compilation, one must distinguish these from target
build dependencies, which may be linked with your package and must be
compiled for the target architecture.

##### Attributes

> The same attributes as for [\<build_depend\> (multiple)](#build_depend-multiple).

#### \<exec_depend\> (multiple)

Declares a rosdep key or ROS package name that this package needs at
execution-time. For system packages, the rosdep key will normally *not*
specify the \"development\" package, so it will generally lack the
`"-dev"` suffix.

The `<exec_depend>` is needed for packages providing shared libraries,
executable commands, Python modules, launch scripts or any other files
required for running your package. It is also used by metapackages for
grouping packages.

##### Attributes

> The same attributes as for [\<build_depend\> (multiple)](#build_depend-multiple).

#### \<depend\> (multiple)

Declares a rosdep key or ROS package name that this package needs for
multiple reasons. A `<depend>` tag is equivalent to specifying
`<build_depend>`, `<build_export_depend>` and `<exec_depend>`, all on
the same package or key. The `<depend>` tag cannot be used in
combination with any of the three equivalent tags for the same package
or key name.

##### Attributes

> The same attributes as for [\<build_depend\> (multiple)](#build_depend-multiple).

#### \<doc_depend\> (multiple)

Declares a rosdep key or ROS package name that your package needs for
building its documentation. A `<doc_depend>` *may* reference a package
also declared as some other type of dependency.

The current version of the buildsystem does not provide any
documentation specific functionality or targets but may do so in the
future, similar to how the unit tests are integrated into the configure
and make steps. Other infrastructure (like the documentation jobs on the
buildfarm) will utilize these additional doc dependencies.

Generated Debian packages are built without the documentation or the
documentation dependencies.

##### Attributes

> The same attributes as for [\<build_depend\> (multiple)](#build_depend-multiple).

#### \<test_depend\> (multiple)

Declares a rosdep key or ROS package name that your package needs for
running its unit tests. A `<test_depend>` *may* reference a package also
declared as some other type of dependency.

All tests and their dependencies will be built if the CMake variables
`CATKIN_ENABLE_TESTING=1` and `CATKIN_SKIP_TESTING=0`, the default
settings. `CMakeLists.txt` should only define its test targets when
`CATKIN_ENABLE_TESTING=1`[^13].

When building with testing enabled, the `<test_depend>` packages are
available for configuring and building the tests as well as running
them. Generated Debian packages are built without the unit tests or
their dependencies.

##### Attributes

> The same attributes as for [\<build_depend\> (multiple)](#build_depend-multiple).

#### \<conflict\> (multiple)

Declares a rosdep key or ROS package name with which your package
conflicts. This package and the conflicting package should not be
installed at the same time. This has no effect on source builds, but
maps to `Conflicts` when creating Debian or RPM packages.

For a detailed explanation how these relationships are used see [^14]
and[^15].

##### Attributes

> The same attributes as for [\<build_depend\> (multiple)](#build_depend-multiple).

#### \<replace\> (multiple)

Declares a rosdep key or ROS package name that your package replaces.
This has no effect on source builds, but maps to `Replaces` when
creating Debian packages and `Obsoletes` for RPM packages.

##### Attributes

> The same attributes as for [\<build_depend\> (multiple)](#build_depend-multiple).

### Group dependency tags
{: style="color:red"}

#### \<group_depend\> (multiple)
{: style="color:red"}

The content is the name of a dependency group on which the package
depends. The group name should follow the same rules as the
[\<name\>](#name) tag.
{: style="color:red"}

##### Attributes
{: style="color:red"}

> The _condition_ attribute as defined for [\<build_depend\> (multiple)](#build_depend-multiple).
{: style="color:red"}

#### \<member_of_group\> (multiple)
{: style="color:red"}

The content is the name of a dependency group of which the package is a
member.
{: style="color:red"}

##### Attributes
{: style="color:red"}

> The _condition_ attribute as defined for
> [\<build_depend\> (multiple)](#build_depend-multiple).
{: style="color:red"}

### \<export\>

This tag serves as a container for additional information various
packages and subsystems need to embed. To avoid potential collisions, an
export tag should have the same name as the package which is meant to
process it. The content of that tag is up to the package to define and
use.

Existing rosbuild export tags for tools using `pluginlib` remain
unchanged. For example, a package which implements an rviz plugin might
include this:

```xml
<export>
  <rviz plugin="${prefix}/plugin_description.xml"/>
</export>
```

The following are some tags used within an `<export>` for various
package and message generation tasks.

#### \<architecture_independent/\>

This empty tag indicates that your package produces no
architecture-specific files once built. That information is intended for
allowing optimization of packaging.

Specifying `<architecture_independent/>` is recommended for metapackages
and for packages defining only ROS messages and services. Python-only
packages are reasonable candidates, too. It is not appropriate for any
package which compiles C or C++ code.

Be sure to remove this tag if some subsequent update adds
architecture-dependent targets to a formerly independent package.

#### \<build_type\> (multiple)

Various tools use this tag to determine how to handle a package. It was
defined in REP-0134[^16], which currently specifies only two valid
values:

```xml
<build_type>catkin</build_type>
<build_type>cmake</build_type>
```

If no `<build_type>` is provided, `catkin` is assumed.

When the build type is `cmake`, the package is handled as a non-catkin
CMake project. It cannot be included in a normal catkin workspace, but
can instead use `catkin_make_isolated`, which configures and builds a
different kind of workspace in which `cmake`, `make`, and `make install`
are invoked separately for each package. See REP-0134 for details.

Only one build type should be active after conditions are evaluated. If
multiple are active then the last build type is to be used.

Further build types may eventually be defined, such as: \"make\",
\"autotools\", \"rosbuild\", or \"custom\".

##### Attributes
{: style="color:red"}

> The _condition_ attribute as defined for [\<build_depend\> (multiple)](#build_depend-multiple).
{: style="color:red"}

#### \<deprecated\>

This tag indicates that your package is deprecated, enabling tools to
notify users about that fact. The tag may be empty or may optionally
contain an arbitrary text providing user more information about the
deprecation:

```xml
<export>
  <deprecated>
    This package will be removed in ROS Hydro. Instead, use package
    FOO, which provides similar features with a different API.
  </deprecated>
</export>
```

#### \<message_generator\>

The content defines the *identifier* for the language bindings generated
by this package, i.e. in `gencpp` this is set to `cpp`:

```xml
<export>
  <message_generator>cpp</message_generator>
</export>
```

#### \<metapackage/\>

This empty tag declares a special kind of catkin package used for
grouping other packages. Metapackages only provide execution-time
dependencies. They cannot be used for catkin builds and compile nothing
themselves. Metapackages may not install any code or other files,
although `package.xml` does get installed automatically. They can depend
on other metapackages, but regular catkin packages cannot.

A good use for metapackages is to group the major components of your
robot and then provide a comprehensive grouping for your whole system.
Package installation tools like `apt-get` or `yum` can automatically
install all the packages on which a metapackage directly or indirectly
depends. Metapackages can also be used to resolve dependencies declared
by legacy rosbuild stacks not yet converted to catkin.

Every metapackage must have a `CMakeLists.txt` containing these
commands:

```cmake
cmake_minimum_required(VERSION 2.8.3)
project(PACKAGE_NAME)
find_package(catkin REQUIRED)
catkin_metapackage()
```

Because the metapackage `CMakeLists.txt` contains a catkin macro, its
`package.xml` must declare a buildtool dependency on catkin:

```xml
<buildtool_depend>catkin</buildtool_depend>
```

Additional buildtool, build or test dependencies are not permitted.

Because metapackages only supply execution-time dependencies, they use
`<exec_depend>` to list the packages in their group:

```xml
    <exec_depend>your_custom_msgs</exec_depend>
    <exec_depend>your_server_node</exec_depend>
    <exec_depend>your_utils</exec_depend>
    <exec_depend>another_metapackage</exec_depend>
```

## Related Changes

### Environment variables

In order to identify the ROS distribution ROS 1 already defines an
environment variable _ROS_DISTRO_ ([^17]). ROS 2 should
expose the same environment variable. The package exporting the
necessary environment should be a dependency of almost all ROS 2
packages to ensure that the information is available even when only some
packages are installed. The package _rcl_ seems to be a good
place for this.
{: style="color:red"}

Additionally for the condition expressions to allow distinguishing ROS 1
and ROS 2 an environment variable identifying the major version is
necessary. Therefore the environment variable _ROS_VERSION_
is used with the value being either _1_ or _2_.
This new environment variable can be defined beside the
_ROS_DISTRO_ one.
{: style="color:red"}

An additional environment variable _ROS_PYTHON_VERSION_ to
choose the Python version in use (either _2_ or
_3_) is also provided. In ROS 1, this allows users to test
out packages on Python 3 before the distribution is officially switched
to Python 3. ROS 2 only supports Python 3, so changing this environment
variable there will cause tools like rosdep to stop working.
{: style="color:red"}

Once a specific ROS environment has been sourced all tools can determine
the ROS major version as well as the distribution name and therefore
evaluate conditions which use those to limit the scope of dependencies.
{: style="color:red"}

If no environment has been sourced some tools might require that the
necessary information is being specified explicitly when being invoked.
{: style="color:red"}

#### New ROS package

In ROS 1 the environment variable _ROS_DISTRO_ is being set
in the _roslib_ package which also defines other environment
variables like _ROS_PACKAGE_PATH_. In ROS 2 the environment
variable _ROS_DISTRO_ doesn\'t exist at the moment. Also
neither ROS version has an environment variable
_ROS_VERSION_ at the moment.
{: style="color:red"}

A new ROS package named _ros_environment_ which has minimal
dependencies will be available in both ROS versions and providing the
new environment variables as well as some of the existing environment
variables.
{: style="color:red"}

## Compatibility

### Support for format three

Existing tools supporting up to format two will need to be updated to
honor the new information provided by format three. If they are not
checking that the format is two or lower they will simply ignore the
format three specific information when processing a package with a
format three manifest.
{: style="color:red"}

In order to enable packages to declare different dependencies for ROS 1
and ROS 2 in a single manifest the tools in ROS 1
(_catkin_pkg_, _rosdep_, _bloom_, etc.) should be updated to support format 3.
{: style="color:red"}

#### catkin_prepare_release

As long as a manifest doesn\'t specify a _compatibility_
version the tools doesn\'t need to change. For packages which do specify
a _compatibility_ version the tool should probably by
default remove the attribute and only after confirmation from the user
offer to keep it.
{: style="color:red"}

#### ros_buildfarm

The dependencies between packages is directly mapped to upstream /
downstream jobs in Jenkins. In order to consider the
_compatibility_ attribute the downstream job dependencies
must be changed to be conditional which are only triggered when the new
package version is not compatible to the previous version.
{: style="color:red"}

### Backward compatibility

Format one or two packages following REP-0127[^18] or REP-0140[^19] are
not affected unless they are updated to declare `<package format="3">`.
{: style="color:red"}

Since format three only adds new functionality and doesn\'t modify any
existing markup a migration to format three only makes sense when the
package wants to use any of the new features.
{: style="color:red"}

## Schema

A schema defining the structure specified in this document is available
at[^20]. To specify the schema within a manifest you can reference a
self contained schema file like this:
{: style="color:blue"}

> \<?xml version=\"1.0\"?\> \<?xml-model
> href=\"http://download.ros.org/schema/package_format3.xsd\"
> schematypens=\"http://www.w3.org/2001/XMLSchema\"?\> \<package
> format=\"3\"\>
{: style="color:blue"}

## References

## Copyright

This document has been placed in the public domain.

## Appendix

### Alternatives for Universal Packages

One option is to not allow different dependencies depending on the ROS
version. For example, a package that depends on _roscpp_ in ROS 1 and
_rclcpp_ in ROS 2 would depend on _roscpp_. ROS 2 would have a dummy
packcage called _roscpp_ that depended on _rclcpp_. That would allow all
downstream packages to use a single name as their dependency.
{: style="color:red"}

This option was not chosen because it would be burdensome to create
dummy packages for every naming difference between ROS 1 and ROS 2. It
is even more cumbersome if a package needs to declare a dependency only
in one of the ROS versions. There would be a dummy package in both ROS
version where one is empty and the other declares a dependency.
{: style="color:red"}

[^1]: REP-0127 (<https://ros.org/reps/rep-0127.html>)

[^2]: ROS naming conventions
    (<http://www.ros.org/wiki/ROS/Patterns/Conventions#Naming_ROS_Resources>)

[^3]: REP-0127 (<https://ros.org/reps/rep-0127.html>)

[^4]: REP-0127 (<https://ros.org/reps/rep-0127.html>)

[^5]: Discussion on REP-0127
    (<https://groups.google.com/forum/#!topic/ros-sig-buildsystem/_jRvhXFfsVk>)

[^6]: Related topic of versioning ROS libraries
    (<https://groups.google.com/forum/#!topic/ros-sig-buildsystem/Q9BK3MGFY_U>)

[^7]: SO versioning from a package perspective
    (<https://groups.google.com/forum/#!topic/ros-sig-buildsystem/jTB9r3zu580>)

[^8]: REP-0143 (<https://ros.org/reps/rep-0143.html>)

[^9]: REP-0127 (<https://ros.org/reps/rep-0127.html>)

[^10]: REP-0140 (<https://ros.org/reps/rep-0140.html>)

[^11]: Buildsystem mailing list discussion: [\"Dependency tag types for
    REP
    127\"](https://groups.google.com/forum/?fromgroups=#!topic/ros-sig-buildsystem/fXGSZG0SC08)

[^12]: ROS naming conventions
    (<http://www.ros.org/wiki/ROS/Patterns/Conventions#Naming_ROS_Resources>)

[^13]: Buildsystem mailing list discussion: [\"REP-0140: internal
    review\"](https://groups.google.com/forum/?fromgroups=#!topic/ros-sig-buildsystem/_QVFLQi-6wk)

[^14]: Declaring relationships between packages (Debian Policy Manual)
    (<http://www.debian.org/doc/debian-policy/ch-relationships.html>)

[^15]: Advanced RPM Packaging (Fedora Documentation)
    (<http://docs.fedoraproject.org/en-US/Fedora_Draft_Documentation/0.1/html/RPM_Guide/ch-advanced-packaging.html>)

[^16]: REP-0134 (<https://ros.org/reps/rep-0134.html>)

[^17]: ROS_DISTRO environment variable
    (<https://github.com/ros/ros/blob/b202645dc6bea6d4b9ca408dc703c8c7cc8204d9/core/roslib/env-hooks/10.ros.sh.em#L16>)

[^18]: REP-0127 (<https://ros.org/reps/rep-0127.html>)

[^19]: REP-0140 (<https://ros.org/reps/rep-0140.html>)

[^20]: Schema file
    (<https://github.com/ros-infrastructure/rep/blob/master/xsd/package_format3.xsd>)
