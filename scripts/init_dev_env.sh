#!/bin/bash

cd $(dirname $0)
cd ../

# Setting up virtual environment
if [ ! -d "env" ]; then
	python3 -m venv env
fi
source env/bin/activate
python3 -m pip install \
    -r requirements/base.txt \
    -r requirements/dev.txt \
    -r requirements/types.txt

# setting up pre-commit hook
cat << EOF > .git/hooks/pre-commit
#!/bin/bash
cd \$(dirname "\$0")
cd ../../

files_to_blacken=\$(git diff --name-only --cached --diff-filter=d | grep "\.py$")
if [[ "\$files_to_blacken" != "" ]]; then
	echo "Running black..."
	echo ""
	env/bin/python3 -m black \$files_to_blacken
	git add \$files_to_blacken
	echo ""
fi

echo "Running mypy..."
mypy_output=\$(env/bin/python3 -m mypy .)

if [[ "\$mypy_output" != Success* ]]; then
	echo "mypy detected errors:"
	echo ""
	echo "\$mypy_output"
	echo ""
	exit 1
else
	echo "mypy checks passed"
	echo ""
fi
EOF
chmod 700 .git/hooks/pre-commit
