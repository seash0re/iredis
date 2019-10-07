from prompt_toolkit.formatted_text import FormattedText
from iredis import renders
from iredis.config import config


def strip_formatted_text(formatted_text):
    return "".join(text[1] for text in formatted_text)


def test_render_list_index():
    from iredis.config import config

    config.raw = False
    raw = ["hello", "world", "foo"]
    out = renders._render_list([item.encode() for item in raw], raw)
    out = strip_formatted_text(out)
    assert isinstance(out, str)
    assert "3)" in out
    assert "1)" in out
    assert "4)" not in out


def test_render_list_index_const_width():
    from iredis.config import config

    config.raw = False
    raw = ["hello"] * 100
    out = renders._render_list([item.encode() for item in raw], raw)
    out = strip_formatted_text(out)
    assert isinstance(out, str)
    assert "  1)" in out
    assert "\n100)" in out

    raw = ["hello"] * 1000
    out = renders._render_list([item.encode() for item in raw], raw)
    out = strip_formatted_text(out)
    assert "   1)" in out
    assert "\n 999)" in out
    assert "\n1000)" in out

    raw = ["hello"] * 10
    out = renders._render_list([item.encode() for item in raw], raw)
    out = strip_formatted_text(out)
    assert " 1)" in out
    assert "\n 9)" in out
    assert "\n10)" in out


def test_render_list_while_config_raw():
    from iredis.config import config

    config.raw = True
    raw = ["hello", "world", "foo"]
    out = renders._render_list([item.encode() for item in raw], raw)
    assert b"hello\nworld\nfoo" == out


def test_render_list_with_nil_init():
    from iredis.config import config

    config.raw = False
    raw = [b"hello", None, b"world"]
    out = renders.render_list(raw, None)
    out = strip_formatted_text(out)
    assert out == '1) "hello"\n2) (nil)\n3) "world"'


def test_render_list_with_nil_init_while_config_raw():
    from iredis.config import config

    config.raw = True
    raw = [b"hello", None, b"world"]
    out = renders.render_list(raw, None)
    assert out == b"hello\n\nworld"


def test_render_list_with_empty_list_raw():
    from iredis.config import config

    config.raw = True
    raw = []
    out = renders.render_list(raw, None)
    assert out == b""


def test_render_list_with_empty_list():
    from iredis.config import config

    config.raw = False
    raw = []
    out = renders.render_list(raw, None)
    out = strip_formatted_text(out)
    assert out == "(empty list or set)"


def test_ensure_str_bytes():
    assert renders._ensure_str(b"hello world") == r"hello world"
    assert renders._ensure_str(b"hello'world") == r"hello'world"
    assert renders._ensure_str("你好".encode()) == r"\xe4\xbd\xa0\xe5\xa5\xbd"


def test_double_quotes():
    assert renders._double_quotes('hello"world') == r'"hello\"world"'
    assert renders._double_quotes('"hello\\world"') == '"\\"hello\\world\\""'

    assert renders._double_quotes("'") == '"\'"'
    assert renders._double_quotes("\\") == '"\\"'
    assert renders._double_quotes('"') == '"\\""'


def test_simple_string_reply():
    config.raw = False
    assert renders.render_bulk_string(b"'\"") == '''"'\\""'''


def test_simple_string_reply_raw():
    config.raw = True
    assert renders.render_bulk_string(b"hello") == b"hello"


def test_render_int():
    config.raw = False
    assert renders.render_int(12) == FormattedText(
        [("class:type", "(integer) "), ("", "12")]
    )


def test_render_int_raw():
    config.raw = True
    assert renders.render_int(12) == b"12"


def test_make_sure_all_callback_functions_exists(iredis_client):
    from iredis.commands_csv_loader import command2callback

    for callback in command2callback.values():
        if callback == "":
            continue
        assert callable(iredis_client.callbacks[callback])


def test_render_list_or_string():
    config.raw = False
    assert renders.render_list_or_string("") == '""'
    assert renders.render_list_or_string("foo") == '"foo"'
    assert renders.render_list_or_string([b"foo", b"bar"]) == FormattedText(
        [
            ("", "1)"),
            ("", " "),
            ("class:string", '"foo"'),
            ("", "\n"),
            ("", "2)"),
            ("", " "),
            ("class:string", '"bar"'),
        ]
    )


def test_list_or_string():
    config.raw = False
    assert renders.render_string_or_int(b"10.1") == '"10.1"'
    assert renders.render_string_or_int(3) == FormattedText(
        [("class:type", "(integer) "), ("", "3")]
    )


def test_command_keys(completer):
    completer.completers["key"].words = []
    config.raw = False
    rendered = renders.command_keys([b"cat", b"dog", b"banana"], completer)

    assert rendered == FormattedText(
        [
            ("", "1)"),
            ("", " "),
            ("class:key", '"cat"'),
            ("", "\n"),
            ("", "2)"),
            ("", " "),
            ("class:key", '"dog"'),
            ("", "\n"),
            ("", "3)"),
            ("", " "),
            ("class:key", '"banana"'),
        ]
    )
    assert completer.completers["keys"].words == ["banana", "dog", "cat"]


def test_command_scan(completer):
    completer.completers["key"].words = []
    config.raw = False
    rendered = renders.command_scan(
        [b"44", [b"a", b"key:__rand_int__", b"dest", b" a"]], completer
    )

    assert rendered == FormattedText(
        [
            ("class:type", "(cursor) "),
            ("class:integer", "44"),
            ("", "\n"),
            ("", "1)"),
            ("", " "),
            ("class:key", '"a"'),
            ("", "\n"),
            ("", "2)"),
            ("", " "),
            ("class:key", '"key:__rand_int__"'),
            ("", "\n"),
            ("", "3)"),
            ("", " "),
            ("class:key", '"dest"'),
            ("", "\n"),
            ("", "4)"),
            ("", " "),
            ("class:key", '" a"'),
        ]
    )
    assert completer.completers["keys"].words == [" a", "dest", "key:__rand_int__", "a"]


def test_command_sscan(completer):
    completer.completers["member"].words = []
    config.raw = False
    rendered = renders.command_sscan(
        [b"44", [b"a", b"member:__rand_int__", b"dest", b" a"]], completer
    )

    assert rendered == FormattedText(
        [
            ("class:type", "(cursor) "),
            ("class:integer", "44"),
            ("", "\n"),
            ("", "1)"),
            ("", " "),
            ("class:member", '"a"'),
            ("", "\n"),
            ("", "2)"),
            ("", " "),
            ("class:member", '"member:__rand_int__"'),
            ("", "\n"),
            ("", "3)"),
            ("", " "),
            ("class:member", '"dest"'),
            ("", "\n"),
            ("", "4)"),
            ("", " "),
            ("class:member", '" a"'),
        ]
    )
    assert completer.completers["members"].words == [
        " a",
        "dest",
        "member:__rand_int__",
        "a",
    ]


def test_command_sscan_config_raw(completer):
    completer.completers["member"].words = []
    config.raw = True
    rendered = renders.command_sscan(
        [b"44", [b"a", b"member:__rand_int__", b"dest", b" a"]], completer
    )

    assert rendered == b"44\na\nmember:__rand_int__\ndest\n a"
    assert completer.completers["members"].words == [
        " a",
        "dest",
        "member:__rand_int__",
        "a",
    ]


def test_render_members(completer):
    completer.completers["members"].words = []
    config.raw = False
    config.withscores = True
    rendered = renders.render_members([b"duck", b"667", b"camel", b"708"], completer)

    assert rendered == FormattedText(
        [
            ("", "1)"),
            ("", " "),
            ("class:integer", "667 "),
            ("class:member", '"duck"'),
            ("", "\n"),
            ("", "2)"),
            ("", " "),
            ("class:integer", "708 "),
            ("class:member", '"camel"'),
        ]
    )
    assert completer.completers["member"].words == ["camel", "duck"]


def test_render_members_config_raw(completer):
    completer.completers["members"].words = []
    config.raw = True
    config.withscores = True
    rendered = renders.render_members([b"duck", b"667", b"camel", b"708"], completer)

    assert rendered == b"duck\n667\ncamel\n708"
    assert completer.completers["member"].words == ["camel", "duck"]


def test_render_unixtime_config_raw(completer):
    config.raw = False
    rendered = renders.render_unixtime(1570469891)

    assert rendered == FormattedText(
        [
            ("class:type", "(integer) "),
            ("", "1570469891"),
            ("", "\n"),
            ("class:type", "(local time)"),
            ("", " "),
            ("", "2019-10-08 01:38:11"),
        ]
    )


def test_render_unixtime(completer):
    config.raw = True
    rendered = renders.render_unixtime(1570469891)

    assert rendered == b"1570469891"
