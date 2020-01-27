# python-terraform-plugin
PoC terraform provider library for Python

To run example provider demonstrating capabilities:

1. Install direnv https://direnv.net/
2. Install Terraform v0.12+ https://www.terraform.io/downloads.html
3. Install Python 3.7+ https://realpython.com/installing-python/

4. Checkout and execute example code:

        git clone https://github.com/nazarewk/python-terraform-provider.git
        cd python-terraform-provider
        python3.7 -m dev_init
        cd terraform-provider-example
        terraform init
        terraform apply

# Slow performance
Note this code is very slow (in order of magnitude of 10 seconds per real Terraform operation), because of this i didn't put much more work into it than a simple proof of concept.

# TODO

- [x] `terraform provider schemas -json`
- [x] `terraform apply` with Python `data_source`
- [x] `terraform apply` with Python `resource`
- [ ] create Pythonic interface to `data_sources` and `resources`:
    - [ ] `Schema` generation from Python class
    - [ ] mapping of GRPC methods to Python class
- [ ] provisioner implementation in Python, currently out of scope
- [ ] determine whether faster execution time is possible at all (Terraform
    spawns a new process multiple times during execution),
