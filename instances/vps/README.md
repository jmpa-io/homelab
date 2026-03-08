# VPS Instance Configuration

This directory contains Ansible roles for configuring VPS (Virtual Private Server) instances.

## Available Roles

### tailscale
Installs and configures Tailscale VPN on the VPS instance.

**Tasks:**
- Installs Tailscale from official repository
- Enables and starts tailscaled service
- Authenticates with Tailscale using OAuth key

**Variables Required:**
- `tailscale.oauth_private_key`: OAuth token for Tailscale authentication

## Usage

VPS instances are defined in the inventory and automatically configured with the specified services.
