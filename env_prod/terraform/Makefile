
.PHONY: show build taint-machines

show:
	terraform show

build:
	terraform init
	terraform apply

taint-machines:
	terraform taint aws_instance.web
	terraform taint aws_instance.shell
	terraform apply
