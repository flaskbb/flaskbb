from flaskbb.markup import FlaskBBRenderer, make_renderer

markdown = make_renderer([FlaskBBRenderer])


def test_custom_renderer():
    # custom paragraph
    p_plain = "@sh4nks is developing flaskbb."
    assert "/user/sh4nks" in markdown(p_plain)

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
