# python-terraform-provider
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