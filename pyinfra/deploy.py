from pyinfra import local

local.include("deploy/common.py")
local.include("deploy/docker.py")
local.include("deploy/infra.py")
local.include("deploy/komodo.py")
local.include("deploy/sure.py")
local.include("deploy/gitea.py")
local.include("deploy/nocodb.py")
local.include("deploy/databasus.py")
local.include("deploy/caddy.py")
