.PHONY: update-lock bundle-deps

bundle-deps: requirements.txt
	sed -i /@/d requirements.txt
	python -m pip install -t ./bundled/libs --no-cache-dir --implementation py --no-deps --upgrade -r ./requirements.txt
	#python -m pip install -t ./bundled/libs --no-cache-dir --implementation py --no-deps --upgrade git+https://github.com/openlawlibrary/pygls.git#egg=pygls
	python -m pip install -t ./bundled/libs --no-cache-dir --implementation py --no-deps --upgrade ../../pygls
	python -m pip install -t ./bundled/libs --no-cache-dir --implementation py --no-deps --upgrade ../../esbonio/lib/esbonio

requirements.txt: requirements.in
	pip-compile --resolver=backtracking --generate-hashes --upgrade ./requirements.in

update-lock: requirements.txt
