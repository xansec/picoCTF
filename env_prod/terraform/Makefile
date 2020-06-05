
.PHONY: show build taint-machines

show:
	terraform show

build:
	terraform init
	terraform apply

taint-web:
	terraform taint aws_instance.web

taint-shell:
	terraform taint aws_instance.shell

taint-machines: taint-web taint-shell
	terraform apply
