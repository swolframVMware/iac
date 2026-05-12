# Day 1: Deployment Prerequisites

The following is a list of prerequisites that are expected for the Day 1 deployment
conditions.

## Planning and Preparation

Most of the following items are necessary, but some are optional configurations (such as
any custom user roles and permissions).

- Design and plan for the VCF instance, both logical and physical designs.
- Create and document the IPs and hostnames for VCF Installer A/PTR DNS records.
- Create and document the IPs and hostnames for ESX hosts A/PTR DNS records
- Create and document the IPs and hostnames for vCenter instances A/PTR DNS records
- Create and document the IPs and hostnames for SDDC Manager A/PTR DNS records
- Create and document the IPs and hostnames for VCF Operations A/PTR DNS records
- Create and document the IPs and hostnames for VCF Automation A/PTR DNS records
- Create and document the an IP range for the vMotion IP Pool.
- Create and document the an IP range for the vSAN IP Pool.
- Create and document the an IP range for the Host TEP Pool.
- Create and document the VLANs to use.
- Create and document the MTU size to use.
- Document the NTP servers to use.
- Document the DNS servers to use.
- Document the DNS search domains to use.
- Document vCenter Single Sign-on identity sources(s) - ex: AD, ADFS
- Document vCenter Single Sign-on custom roles and permissions
- Document vCenter, NSX, and SDDC Manager user RBAC assignments

### Define System Configuration

Normally at this point a VCF deployment you would download and complete the VCF
parameter workbook with documented infrastructure data from above. 

However, since we're using the automation, at this point, you configure the
infrastructure-as-code settings for the specific VCF Instance to contain the planning 
and preparation,

## Host Imaging

- Use a supported version of ESX included in the VMware Cloud Foundation BoM.
- Image each host with the supported ESX version, including any vendors specific 
  add-ons.

## VCF Installer Availability

The VCF Installer version in the VMware Cloud Foundation BoM must be deployed and
available for the automation to use. 

It must be in a state where it can take on new requests for a build out, meaning if it 
was used before to initiate a new build out then it must be reset.
