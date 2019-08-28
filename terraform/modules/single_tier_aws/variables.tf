# Varaibles used by the single_tier_aws module

###
# Input Variables:
# These are sane defaults that can be overloaded in an environment specific 
# configuration (eg: production, testing).
###

# SSH
variable "key_name" {
    description = "SSH key used to insert as authorized on the machines"
    default = "pico_production"
}
variable "public_key_path" {
    description = "Local path to SSH public key"
    default = "~/.ssh/picoCTF_production_rsa.pub"
}

# AWS Configuration
variable "region" {
    description = "AWS Region to launch resources in"
    default = "us-east-1"
}
variable "availability_zone" {
    description = "AWS Availability zone to launch resources in"
    default = "us-east-1b"
}
variable "user" {
    description = "User to connect to machines with"
    default = "admin"
}

# Network
variable "vpc_cidr" {
    description = "CIDR Block for Virtual Private Cloud"
    default = "10.0.0.0/16"
}
variable "public_subnet_cidr" {
    description = "CIDR Block for public subnet"
    default = "10.0.1.0/24"
}
variable "web_private_ip" {
    description = "Internal IP address for web server"
    default = "10.0.1.10"
}
variable "shell_private_ip" {
    description = "Internal IP address for shell server"
    default = "10.0.1.11"
}

# Instances
variable "web_instance_type" {
    description = "AWS instance type for web server"
    default = "t2.micro"
}
variable "shell_instance_type" {
    description = "AWS instance type for shell server"
    default = "t2.micro"
}

# EBS Volumes
variable "db_ebs_data_size" {
    description = "Size for database persistent store"
    default = "10"
}
variable "db_ebs_data_device_name" {
    description = "Device to map database persistent store to"
    default = "/dev/xvdf"
}

# Tags
variable "competition_tag" {
    default = "picoCTF"
}
variable "env_tag" {
    default = "production"
}
variable "web_name" {
    description = "Name tag for web server"
    default = "picoCTF-web"
}
variable "shell_name" {
    description = "Name tag for shell server"
    default = "picoCTF-shell"
}
variable "db_ebs_name" {
    description = "Name tag of database Elastic Block Storage"
    default = "picoCTF-db-ebs"
}

# Default AMI mapping
# should replace with dynamic AMI mapping
# https://github.com/cloudposse/terraform-aws-ec2-instance/blob/master/main.tf
# https://aws.amazon.com/marketplace/pp/B07J5RRYGN
# http://cloud-images.ubuntu.com/locator/ec2/

variable "amis" {
    description = "Ubuntu bionic 18.04 LTS AMI to use"
    default = {
    us-west-2   = "ami-04aac3d7ea7609469"
    us-west-1   = "ami-03c9dad75296f9e90"
    us-east-2   = "ami-02fd7546f0f6effb6"
    us-east-1   = "ami-095192256fe1477ad"
    sa-east-1   = "ami-0fcd3565c065e9238"
    eu-west-3   = "ami-074f4c146d4f5d466"
    eu-west-2   = "ami-0ee246e709782b1be"
    eu-west-1 = "ami-08b1cea5487c762b3"
    eu-north-1 = "ami-1b33bb65"
    eu-central-1 = "ami-05b5a98cd34853d29"
    ca-central-1 = "ami-0b08c6831ffd5ea84"
    ap-southeast-2 = "ami-035c8e816223729a6"
    ap-southeast-1 = "ami-0c2e7524d47186df7"
    ap-south-1 = "ami-027d1dd332103051b"
    ap-northeast-3 = "ami-0dd67b62d9f8adc65"
    ap-northeast-2 = "ami-06d2ca2471c251818"
    ap-northeast-1 = "ami-032cf5e284518543d"
    }
}
