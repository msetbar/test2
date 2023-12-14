# Introduction 
TODO: Give a short introduction of your project. Let this section explain the objectives or the motivation behind this project. 

# Getting Started
TODO: Guide users through getting your code up and running on their own system. In this section you can talk about:
1.	Installation process
2.	Software dependencies
3.	Latest releases
4.	API references

# Build and Test
TODO: Describe and show how to build your code and run the tests. 

# Contribute
TODO: Explain how other users and developers can contribute to make your code better. 

If you want to learn more about creating good readme files then refer the following [guidelines](https://docs.microsoft.com/en-us/azure/devops/repos/git/create-a-readme?view=azure-devops). You can also seek inspiration from the below readme files:
- [ASP.NET Core](https://github.com/aspnet/Home)
- [Visual Studio Code](https://github.com/Microsoft/vscode)
- [Chakra Core](https://github.com/Microsoft/ChakraCore)


### Installation


#### Installing Poetry
Poetry supports multiple installation methods, including a simple script found at [install.python-poetry.org]. For full
installation instructions, including advanced usage of the script, alternate install methods, and CI best practices, see
the full [installation documentation].

Easiest way is to use the the official installer (Minimum version of Python 3.7 required):

```
$ curl -sSL https://install.python-poetry.org | python3 -
```

Another option to install poetry is to utilize pip. To install poetry using pip, run the following command:

```bash
pip install --index-url https://pypi.it.att.com poetry
```

#### Project Installation

Once Poetry is installed and your environment is configured, you need to install the project dependencies.
Before installing the dependencies, developers will need to uncomment the lines that pertain to the package source from the [pyproject.toml file](./pyproject.toml).
The lines to uncomment should start with `[[too.poetry.source]]` and end with `priority = "default"`.
The snippet below is an example of what the uncommented package source lines should look like.

```
...
[[tool.poetry.source]]
name = "attrepo"
url = "https://pypi.it.att.com"
priority = "default"
...
```

**NOTE:** When creating the PR into the develop branch, make sure to add comments to the lines for the package source.

To install the packages, we can run the following command:

```
$ poetry install
```

To install additional packages just run:
```
$ poetry add <pip package name>
```

To enable the poetry interpreter with all dependencies:
```
$ poetry shell
```

It will automatically find a suitable version constraint and install the package and sub-dependencies. Poetry supports a rich dependency specification syntax, including caret, tilde, wildcard, inequality and multiple constraints requirements. Adding packages this way will automatically add them to your Poetry file which ensures that you don't have to update a requirements.txt file manually.

**NOTE:** Running `poetry shell` may not automatically initialize your virtual environment. If your virtual environment is not automatically initialized, run the following:
 
Initializing on Bash:

```bash
poetry shell
# expected output: Spawning shell within <path-to-python-venv>

# activating on bash
source activate <path-to-python-venv>
```

Initializing on Powershell:

```powershell
poetry shell
# expected output: Spawning shell within <path-to-python-venv>

# activating on powershell
<path-to-python-venv>\Scripts\activate.ps1
```

#### Installing with Poetry.lock file

If there is already a poetry.lock file as well as a pyproject.toml file when you run poetry install, it means either you ran the install command before, or someone else on the project ran the install command and committed the poetry.lock file to the project (which is good).

Either way, running install when a poetry.lock file is present resolves and installs all dependencies that the team listed in pyproject.toml, but Poetry uses the exact versions listed in poetry.lock to ensure that the package versions are consistent for everyone working on your project. As a result you will have all dependencies requested by the pyproject.toml file, but they may not all be at the very latest available versions (some dependencies listed in the poetry.lock file may have released newer versions since the file was created). This is by design, it ensures that the project does not break because of unexpected changes in dependencies.
