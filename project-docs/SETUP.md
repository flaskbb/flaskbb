\# Team setup notes (Windows)



\## Installing FlaskBB

1\. Install Git and uv.

2\. Clone: `git clone https://github.com/Nikhil3265888/flaskbb.git`

3\. Use Python 3.13, because Python 3.15 fails to build pyyaml on Windows:

&#x20;  `uv python pin 3.13`

4\. `uv sync`

5\. `uv run flaskbb makeconfig -d`

&#x20;  Then add `DEBUG\_TB\_INTERCEPT\_REDIRECTS = False` to the bottom of `flaskbb.cfg`

6\. `uv run flaskbb install`

7\. `uv run flaskbb run --debug --reload` and open http://127.0.0.1:5000

8\. New users must be activated by an admin in Management -> Users (email is not set up).



\## Running the tests

```

uv run pytest

```



\## Measuring coverage (use this exact method for all before/after measurements)

pytest-cov reported a wrong figure (49%), so we run coverage as the outer process:

```

uv run coverage erase

uv run coverage run -m pytest -n0

uv run coverage report

uv run coverage html

```



\## Measuring complexity and size

```

uvx radon cc flaskbb -a -s -e "flaskbb/migrations/\*"

uvx radon mi flaskbb -s -e "flaskbb/migrations/\*"

uvx radon raw flaskbb -s -e "flaskbb/migrations/\*"

```

