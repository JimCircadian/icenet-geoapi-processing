#SHELL := bash
#.ONESHELL:
#.SHELLFLAGS := -eu -o pipefail

ICENET_ENV?=dev
ICENET_AZ_APPLICATION?=web-icenet$(ICENET_ENV)-application
ICENET_GH_APPLICATION?=https://github.com/icenet-ai/icenet-application
ICENET_RG?=rg-icenet$(ICENET_ENV)-processing

.PHONY: clean deploy-azure run

clean:

deploy-azure:
	func azure functionapp publish app-icenet$(ICENET_ENV)-processing --python
