PY?=python
TAR?=0

BINDIR=bin
POFILESEXEC=$(BINDIR)/pofiles.py
FRONTENDEXEC=$(BINDIR)/frontend.py

REMOTEDATADIR=remote_data
MACSDIR=$(REMOTEDATADIR)/macs
CERTSSDIR=$(REMOTEDATADIR)/certs
DNSDIR=$(REMOTEDATADIR)/dns

ifeq ($(TAR), 0)
	POFILES_TAR_ARGS=to_tar
else
	POFILES_TAR_ARGS=from_tar
	POFILES_TAR_ARGS+=$(TAR)
endif

.PHONY: translations translations_tar frontend update_padded_macs update_cert_fingerprints update_root_key_file

help:
	@echo 'Makefile for internet.nl'
	@echo ''
	@echo 'Usage:'
	@echo '   make translations                          combine the translation files to Django PO files'
	@echo '   make translations_tar                      create a tar from the translations'
	@echo '   make translations_tar TAR=<tar.gz file>    read the tar and update the translations'
	@echo '   make frontend                              (re)generate CSS and Javascript'
	@echo '   make update_padded_macs                    update padded MAC information'
	@echo '   make update_cert_fingerprints              update certificate fingerpint information'
	@echo '   make update_root_key_file                  update DNS root key file'

translations:
	@$(PY) $(POFILESEXEC) to_django
	@echo "Make sure to run 'compilemessages' on the server to update the actual content"

translations_tar:
	@$(PY) $(POFILESEXEC) $(POFILES_TAR_ARGS)

frontend:
	@$(PY) $(FRONTENDEXEC) js
	@$(PY) $(FRONTENDEXEC) css

update_padded_macs:
	cd $(MACSDIR); ./update-macs.sh

update_cert_fingerprints:
	cd $(CERTSSDIR); ./update-certs.sh

update_root_key_file:
	unbound-anchor -a $(DNSDIR)/root.key
