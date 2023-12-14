# MinecraftServerManager

python script that helps to manage Minecraft server files.

---

## Usage

### Downloading server files

To get the newest release server files use:  
`python msm.py download latest_release`

or for snapshots:  
`python msm.py download latest_snapshot`

If you need a specific version:  
`python msm.py download <version>`  
`python msm.py download 1.20.4`  

The download command creates a "server_versions" folder  
if you want to specify another download folder add  
`--folder="/path/to/folder"`  
to your command.  
`python msm.py --folder="versions" download 1.8.2`  

---
