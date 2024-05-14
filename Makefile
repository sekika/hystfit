all:

install:
	python3 -m pip install .

test:
	cd dev; ./test.sh

deb:
	python3 setup.py --command-packages=stdeb.command bdist_deb
	cd deb_dist; rm -f ${debfile}; cp `ls *.deb | tail -n 1` $(debfile)
