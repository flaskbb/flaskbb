from flaskbb.markup import DEFAULT_PLUGINS, FlaskBBRenderer, make_renderer

markdown = make_renderer([FlaskBBRenderer], DEFAULT_PLUGINS)


def test_userify():
    # user link rendering plugin
    result = markdown("@sh4nks is developing flaskbb.")
    assert all(substring in result for substring in ("/user/sh4nks", "<a href="))


def test_highlighting():
    # custom block code with pygments highlighting (jus)
    b_plain = """
```
print("Hello World")
```
"""
    b_plain_lang = """
```python
print("Hello World")
```
"""

    assert "<pre>" in markdown(b_plain)
    assert "highlight" in markdown(b_plain_lang)

    # typo in language
    bad_language = """
```notpython
print("Hello World")
```
"""

    bad_language_render = markdown(bad_language)
    assert "<pre>" in bad_language_render
    assert "highlight" not in bad_language_render
