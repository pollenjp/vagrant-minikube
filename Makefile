
.PHONY: run
run:
	vagrant up
	poetry run ansible-playbook -i inventory/vagrant.py minikube.yml

.PHONY: re-run
re-run:
	${MAKE} clean
	${MAKE} run


.PHONY: halt
halt:
	vagrant halt

.PHONY: clean
clean:
	${MAKE} halt
	vagrant destroy -f
