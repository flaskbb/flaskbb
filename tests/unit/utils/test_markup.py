from flaskbb.utils.markup import collect_emojis, EMOJIS, markdown


def test_collect_emojis():
    assert collect_emojis() == EMOJIS


def test_custom_renderer():
    # custom paragraph
    p_plain = "@sh4nks is :developing: :flaskbb:."
    assert "/user/sh4nks" in markdown.render(p_plain)
    assert "emoji/flaskbb.png" in markdown.render(p_plain)

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

    assert "<pre>" in markdown.render(b_plain)
    assert "highlight" in markdown.render(b_plain_lang)

    # typo in language
    bad_language = """
```notpython
print("Hello World")
```
"""

    bad_language_render = markdown.render(bad_language)
    assert "<pre>" in bad_language_render
    assert "highlight" not in bad_language_render
