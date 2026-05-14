# Labelmaker

A local web app that generates 3D-printable label models for a physical sorting system. Labels are designed for two-color FDM printing and exported as 3MF files compatible with Bambu Studio / OrcaSlicer.

## Deploy to Proxmox LXC

Run this on your Proxmox host:

```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/sophof/Labelmaker/main/deploy/create-lxc.sh)"
```

This creates a Debian 13 LXC container, installs all dependencies, and starts the service. You will be prompted to select a storage pool. Once complete, the UI is accessible at `http://<container-ip>`. The port defaults to 80 and can be changed in `config.yaml`.

## Update an existing installation

From inside the LXC:

```bash
update
```

## Configuration

Default colors and other settings are in `config.yaml` inside the container at `/opt/labelmaker/config.yaml`.
