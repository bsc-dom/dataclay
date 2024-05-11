-- Author: Distributed Object Management @ BSC (support-dataclay@bsc.es)

local name = "DATACLAY"
local version = "edge"
local home = pathJoin("/apps/GPP", name, version)

help([[
dataClay version ]]..version..[[ 

More information about dataClay at:
    - Homepage: https://dataclay.bsc.es/
    - Documentation: https://dataclay.readthedocs.io/en/latest/
    - Source: https://github.com/bsc-dom/dataclay]])

whatis("dataClay " .. version)

-- This module cannot be loaded if another $name modulefile was previously loaded
conflict(name:lower())

-- Depend modules
if (not isloaded("python")) then
  if string.find(myFileName(), "/ACC/") then
    depends_on("mkl", "intel")
  elseif string.find(myFileName(), "/GPP/") then
    depends_on("hdf5")
  end
  depends_on(between("python", "3.9", "<3.13"))
end
prereq(between("python", "3.9", "<3.13"))

-- This shows info about loaded/unloaded module
if (mode() ~= "whatis") then
    LmodMessage(mode() .. " " .. name .. "/" .. version .. 
    " (PATH, PYTHONPATH, COMPSS_STORAGE_HOME, DATACLAY_PYTHONPATH, DATACLAY_HOME)")
  end

-- Get python library path
local py_version = subprocess("python -V 2>&1 | awk '{print $2}' | cut -d. -f1-2"):gsub("\n$","")
local py_lib = pathJoin(home, "lib", "python" .. py_version)

-- Set environment
prepend_path("PYTHONPATH", py_lib .. "/site-packages")
prepend_path("PATH", home .. "/bin")
prepend_path("PATH", py_lib .. "/bin")

-- For COMPSs bindings
setenv("COMPSS_STORAGE_HOME", home)
setenv("DATACLAY_PYTHONPATH", py_lib .. "/site-packages")
setenv("DATACLAY_HOME", home)
