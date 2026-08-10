# Contribute to hipCIM

If you are interested in contributing to hipCIM, your contributions will fall
into three categories:
1. You want to report a bug, feature request, or documentation issue
    - File an [issue](https://github.com/ROCm-LS/hipCIM/issues/new/choose)
    describing what you encountered or what you want to see changed.
    - The hipCIM team will evaluate the issues and triage them, scheduling
    them for a release. If you believe the issue needs priority attention
    comment on the issue to notify the team.
2. You want to propose a new Feature and implement it
    - Post about your intended feature, and we shall discuss the design and
    implementation.
    - Once we agree that the plan looks good, go ahead and implement it, using
    the [code contributions](#code-contributions) guide below.
3. You want to implement a feature or bug-fix for an outstanding issue
    - Follow the [code contributions](#code-contributions) guide below.
    - If you need more context on a particular issue, please ask and we shall
    provide.

## Code contributions

### Your first issue

1. Read the project's [README.md](https://github.com/ROCm-LS/hipCIM/README.md#build-hipcim-from-source)
    to learn how to setup the development environment
2. Find an issue to work on.
3. Comment on the issue saying you are going to work on it
4. Code! Make sure to update unit tests!
5. When done, [create your pull request](https://github.com/ROCm-LS/hipCIM/compare)
6. Verify that CI passes all [status checks](https://help.github.com/articles/about-status-checks/). Fix if needed
7. Wait for other developers to review your code and update code as needed
8. Once reviewed and approved, a hipCIM developer will merge your pull request

Remember, if you are unsure about anything, don't hesitate to comment on issues
and ask for clarifications!

### Seasoned developers

Once you have gotten your feet wet and are more comfortable with the code, you
can look at the prioritized issues of our next release in our [project boards](https://github.com/ROCm-LS/hipCIM/projects).

> **Pro Tip:** Always look at the release board with the highest number for
issues to work on. This is where hipCIM developers also focus their efforts.

Look at the unassigned issues, and find an issue you are comfortable with
contributing to. Start with _Step 3_ from above, commenting on the issue to let
others know you are working on it. If you have any questions related to the
implementation of the issue, ask them in the issue instead of the PR.


## Setting Up Your Build Environment

The following instructions are for developers and contributors to hipCIM development. These instructions are tested on Linux. Use these instructions to build hipCIM from source and contribute to its development.

### Code Formatting

#### Python


hipCIM uses [ruff](https://docs.astral.sh/ruff/) and [black](https://black.readthedocs.io/en/stable/) to ensure a consistent code format
throughout the project. `ruff`, and `black` can be installed with
`conda` or `pip`:

```bash
conda install black ruff
```

```bash
pip install black ruff
```

These tools are used to auto-format the Python code in the repository. Additionally, there is a CI check in place to enforce that the committed code follows our standards. To run only for the python/cucim folder, change to that folder and run

```bash
black .
ruff .
```

To also check formatting in top-level folders like `benchmarks`, `examples` and `experiments`, these tools can also be run from the top level of the repository as follows:

```bash
black --config python/cucim/pyproject.toml .
ruff --config python/cucim/pyproject.toml .
```

In addition to these tools, [codespell](https://github.com/codespell-project/codespell) can be used to help diagnose and interactively fix spelling errors in both Python and C++ code. It can also be run from the top level of the repository in interactive mode using:

```bash
codespell --toml python/cucim/pyproject.toml . -i 3 -w
```

If codespell is finding false positives in newly added code, the `ignore-words-list` entry of the `tool.codespell` section in `pyproject.toml` can be updated as needed.

### Get libhipCIM Dependencies

Compiler requirements:

* `gcc`     version 13.0+
* `hipcc`   (ROCm 10.0+)
* `cmake`   version 4.0+

GPU requirements:

* ROCm 10.0+
* AMD GPU with supported architecture (gfx90a, gfx942, gfx950, etc.)

You can obtain ROCm from [https://rocm.docs.amd.com/projects/install-on-linux/en/latest/](https://rocm.docs.amd.com/projects/install-on-linux/en/latest/).


# Building and Testing hipCIM from Source

First, please clone hipCIM's repository

```bash
HIPCIM_HOME=$(pwd)/hipCIM
git clone https://github.com/ROCm-LS/hipCIM.git $HIPCIM_HOME
cd $HIPCIM_HOME
```
## Local Development using Conda Environment

Conda can be used to setup an environment which includes all of the necessary dependencies (as shown in `./conda/environments/rocm.yaml`) for building hipCIM.

Otherwise, you may need to install dependencies (such as yasm) through your OS's package manager (`apt`, `yum`, and so on).

### Creating the Conda Development Environment

```bash
conda env create -n hipcim -f ./conda/environments/rocm.yaml
# activate the environment
conda activate hipcim
```

### Building `libhipcim` and install `hipcim` (python bindings):

**Building `libhipcim`**

```bash
# build all with `release` binaries (you can change it to `debug` or `rel-debug`)
./run_amd build_local all release $CONDA_PREFIX
```

The build command will create the following files:
- `./install/lib/libhipcim*`
- `./python/install/lib/_cucim.cpython-*-x86_64-linux-gnu.so`
- `./cpp/plugins/cucim.kit.cuslide/install/lib/hipcim.kit.hipslide@*.so`
- `./cpp/plugins/cucim.kit.cumed/install/lib/hipcim.kit.hipmed@*.so`

And, it will copy the built library files to `python/cucim/src/cucim/clara/` folder:
- `libhipcim.so.*`
- `_cucim.cpython-*-x86_64-linux-gnu.so`
- `hipcim.kit.hipslide@*.so`
- `hipcim.kit.hipmed@*.so`


**Building `hipcim` (python bindings)**

```bash
python -m pip install python/cucim
```

For contributors interested in working on the Python code from an in-place
(editable) installation, replace the last line above with
```bash
python -m pip install --editable python/cucim
```

**Cleaning build files**

You can execute the following command whenever C++ code is changed during the development:
```bash
./run_amd build_local all release $CONDA_PREFIX
```
Once it is built, the subsequent build doesn't take much time.

However, if a build option or dependent packages are updated, the build can fail (due to CMakeCache.txt or existing build files). In that case, you can use the following commands to remove CMakeCache.txt or build folder, then build it again.

1) Remove CMakeCache.txt for libhipcim, hipslide/hipmed plugin, and the python wrapper (pybind11).

```bash
# this command wouldn't remove already downloaded dependency so faster than `clean` subcommand
./run_amd build_local clean_cache
```

2) Remove `build-*` and `install` folder for libhipcim, hipslide/hipmed plugin, and the python wrapper (pybind11).

```bash
# this command is for clean build
./run_amd build_local clean
```

## Building a package (for distribution. Including a wheel package for pip)

**Wheel Build**

The wheel can then be built using:

```bash
python -m pip wheel python/cucim/ -w dist -vvv --no-deps --disable-pip-version-check
```

**Note:** It is possible to build the wheel in this way even without compiling the C++ library first, but in that case the `cucim.clara` module will not be importable.

**Install**

```bash
python -m pip install dist/cucim*.whl
```

## Running Tests

Once hipCIM is installed, you can test the module through the `./run_amd test` command.

```bash
# Arguments:
#   $1 - subcommand [all|python|cpp] (default: all)
#   $2 - test_type [all|unit|integration|system|performance] (default: all)
#   $3 - test_component [all|clara|skimage] (default: all)

./run_amd test                      # execute all tests
./run_amd test python               # execute all python tests
./run_amd test python unit          # execute all python unit tests
./run_amd test python unit skimage  # execute all python unit tests in `skimage` module
./run_amd test python unit clara    # execute all python unit tests in `clara` module
./run_amd test python performance   # execute all python performance tests
```
