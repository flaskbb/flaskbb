import warnings

import pytest
from flaskbb.deprecation import deprecated, RemovedInFlaskBB4

NEXT_VERSION_STRING = ".".join([str(x) for x in RemovedInFlaskBB4.version])


@deprecated("This is only a drill")
def only_a_drill():
    pass


@deprecated
def default_deprecation():
    """
    Existing docstring
    """
    pass


class TestDeprecation:
    def test_emits_default_deprecation_warning(self, recwarn):
        warnings.simplefilter("default", RemovedInFlaskBB4)
        default_deprecation()

        assert len(recwarn) == 1
        assert "default_deprecation is deprecated" in str(recwarn[0].message)
        assert recwarn[0].category == RemovedInFlaskBB4
        assert recwarn[0].filename == __file__
        # assert on the next line is conditional on the position of the call
        # to default_deprecation please don't jiggle it around too much
        assert recwarn[0].lineno == 25
        assert "only_a_drill is deprecated" in only_a_drill.__doc__

    def tests_emits_specialized_message(self, recwarn):
        warnings.simplefilter("default", RemovedInFlaskBB4)
        only_a_drill()

        expected = "only_a_drill is deprecated and will be removed in version {}. This is only a drill".format(  # noqa
            NEXT_VERSION_STRING
        )
        assert len(recwarn) == 1
        assert expected in str(recwarn[0].message)

    def tests_only_accepts_FlaskBBDeprecationWarnings(self):
        with pytest.raises(ValueError) as excinfo:
            # DeprecationWarning is ignored by default
            @deprecated("This is also a drill", category=UserWarning)
            def also_a_drill():
                pass

        assert "Expected subclass of FlaskBBDeprecation" in str(excinfo.value)

    def tests_deprecated_decorator_work_with_method(self, recwarn):
        warnings.simplefilter("default", RemovedInFlaskBB4)
        self.deprecated_instance_method()

        assert len(recwarn) == 1

    def test_adds_to_existing_docstring(self, recwarn):
        docstring = default_deprecation.__doc__

        assert "Existing docstring" in docstring
        assert "default_deprecation is deprecated" in docstring

    @pytest.mark.parametrize("decorator", [deprecated, deprecated()])
    def test_preserves_function_arguments_return_value_and_metadata(
        self, decorator, recwarn, default_settings
    ):
        def add(left, *, right):
            return left + right

        decorated = decorator(add)

        warnings.simplefilter("default", RemovedInFlaskBB4)
        assert decorated(2, right=3) == 5

        assert len(recwarn) == 1
        assert recwarn[0].category == RemovedInFlaskBB4
        assert recwarn[0].filename == __file__
        assert "add is deprecated" in str(recwarn[0].message)
        assert decorated.__name__ == add.__name__
        assert decorated.__wrapped__ is add
        assert "add is deprecated" in decorated.__doc__

    def test_decorator_without_parentheses_works_with_method(self, recwarn, default_settings):
        class Example:
            @deprecated
            def add(self, value):
                return value + 1

        warnings.simplefilter("default", RemovedInFlaskBB4)
        assert Example().add(2) == 3

        assert len(recwarn) == 1
        assert recwarn[0].category == RemovedInFlaskBB4
        assert "add is deprecated" in str(recwarn[0].message)

    @deprecated()
    def deprecated_instance_method(self):
        pass
