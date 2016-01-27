from flaskbb.utils.markup import collect_emojis, EMOJIS, markdown


def test_collect_emojis():
    assert collect_emojis() == EMOJIS


def test_custom_renderer():
    # custom paragraph
    p_expected = "<p><a href='/user/sh4nks'>@sh4nks</a> is :developing: <img class='emoji' alt='flaskbb' src='http://localhost:5000/static/emoji/flaskbb.png' />.</p>\n"
    p_plain = "@sh4nks is :developing: :flaskbb:."
    assert markdown.render(p_plain) == p_expected

    # custom block code with pygments highlighting
    b_expected = """\n<pre><code>print("Hello World")</code></pre>\n"""
    b_expected_lang = """<div class="highlight"><pre><span class="k">print</span><span class="p">(</span><span class="s2">&quot;Hello World&quot;</span><span class="p">)</span>\n</pre></div>\n"""
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
    assert markdown.render(b_plain) == b_expected
    assert markdown.render(b_plain_lang) == b_expected_lang
