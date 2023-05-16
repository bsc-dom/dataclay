--------------
-- Information
--------------
whatis("Version: DevelMarc")
whatis("Keywords: Storage, dataClay, data distribution")
whatis("Description: dataClay active objects across the network")

------------
-- lua setup
------------
local name = "DATACLAY"
local version = "DevelMarc"
local home = pathJoin("/apps", name, version)

---------------
-- Dependencies
---------------
DEFAULT_PYTHON_VERSION = "3.10.2"
-- GCC_VERSION = "8.1.0"

-- Module dependencies
-- load("gcc/" .. GCC_VERSION)
if (not isloaded("python")) then load("python/" .. DEFAULT_PYTHON_VERSION) end
prereq(atleast("python","3.10.2"))


----------------------------
-- Get python version & path
----------------------------
-- NOTE: cannot make it work with capture()
execute {cmd="export PYTHON_VERSION=$(python -V 2>&1 | awk '{print $2}')", modeA={"load"}}
PYTHON_VERSION=os.getenv("PYTHON_VERSION") or DEFAULT_PYTHON_VERSION

VENV_PATH = pathJoin(home, "venv" .. PYTHON_VERSION)
setenv("VENV_PATH", VENV_PATH)

--------------------
-- Update PYTHONPATH
--------------------
-- NOTE: With capture it fails when trying to load DATACLAY/DevelMarc if python/3.10.2 is already loaded. Weird...
-- prepend_path("PYTHONPATH", capture("find " .. VENV_PATH .. " -name site-packages"))
-- prepend_path("PYTHONPATH", capture("find $VENV_PATH -name site-packages"))
execute {cmd="export PYTHONPATH=$(find $VENV_PATH -name site-packages):$PYTHONPATH", modeA={"load"}}

--------------
-- Update PATH
--------------
append_path("PATH", home .. "/bin")
append_path("PATH", VENV_PATH .. "/bin") -- for opentelemetry-instrument

------------------
-- COMPSs bindings
------------------
-- append_path("PATH", home .. "/scripts")
setenv("COMPSS_STORAGE_HOME", home)
setenv("DATACLAY_HOME", home)


