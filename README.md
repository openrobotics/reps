# Robotics Enhancement Proposals Official Source

This repository is the offical source of the Robotics Enhancement Proposals (REP) of the Open Source Robotics Alliance Technical Governance Committee.

# REP Submission Process

On October 23rd, 2025 the [Open Source Robotics Alliance (OSRA)](https://osralliance.org/) Technical Governance Comittee (TGC) launched our new REP process. Details on how to submit new REPs can be found in [REP-0001-2025](https://reps.openrobotics.org/rep-0001-2025/). Additional details can be found in our [announcement on ROS Discourse](https://discourse.openrobotics.org/t/launch-of-the-osras-new-robotics-enhancement-proposal-rep-process/50668). The REP review process is significantly different from most conventional source code repositoires **we recommend you read REP-0001-2025 in its entirety before [submitting your pull request.]((https://reps.openrobotics.org/rep-0001-2025/))**

The full list of REPS in markdown format can be found in the [_posts subdirectory](https://github.com/openrobotics/reps/tree/main/_posts)
This website is hosted at [reps.openrobotics.org](https://reps.openrobotics.org/)
REP Discussions should take place on [Open Robotics Discourse](https://discourse.openrobotics.org/) or the [Open Robotics Zulip Server](https://openrobotics.zulipchat.com/).

# REP Numbering Scheme

A specification of the REP numbering system can be [found in REP-0001-2025](https://reps.openrobotics.org/rep-0001-2025/#rep-naming-and-numbering-system). 

# REP Template

A template REP sumbission can be found in [REP-0004-2025 Sample Markdown REP Template.](https://github.com/openrobotics/reps/blob/main/_posts/rep-0004%3A2025.md)

# Building Locally

The REP website is built using [Jekyll](https://jekyllrb.com/) and the [Chirpy theme](https://github.com/cotes2020/chirpy-starter). 

To build the website locally:

* Install Ruby:
```sh
sudo apt install ruby-dev
```
* Make Ruby GEMs available in your your path by adding the following to your shell configuration file (e.g. `.bashrc`):
```sh
export GEM_HOME="$(ruby -e 'puts Gem.user_dir')"
export PATH="$PATH:$GEM_HOME/bin"
```
* Install the required Gems

```sh
gem install bundler jekyll jekyll-theme-chirpy html-proofer

```
* Build and serve the site
```
bundle exec jekyll serve
```
* The REP website should now be available at `http:/localhost:4000`

# Using a Dev Container

A dev container is available for this repository. To use the dev container [follow the instructions outlined by Visual Studio](https://code.visualstudio.com/docs/devcontainers/tutorial) or use GitHub's built-in codespace.
