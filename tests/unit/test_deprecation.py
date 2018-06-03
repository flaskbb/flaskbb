import warnings

import pytest

from flaskbb.deprecation import RemovedInNextVersion, deprecated

NEXT_VERSION_STRING = ".".join([str(x) for x in RemovedInNextVersion.version])


@deprecated("This is only a drill")
def only_a_drill():
    pass


# TODO(anr): Make the parens optional
@deprecated()
def default_deprecation():
    pass


class TestDeprecation(object):

    def test_emits_default_deprecation_warning(self, recwarn):
        warnings.simplefilter("default", RemovedInNextVersion)
        default_deprecation()

        assert len(recwarn) == 1
        assert "default_deprecation is deprecated" in str(recwarn[0].message)
        assert recwarn[0].category == RemovedInNextVersion
        assert recwarn[0].filename == __file__
        # assert on the next line is conditional on the position of the call
        # to default_deprecation please don't jiggle it around too much
        assert recwarn[0].lineno == 25

    def tests_emits_specialized_message(self, recwarn):
        warnings.simplefilter("default", RemovedInNextVersion)
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
        warnings.simplefilter("default", RemovedInNextVersion)
        self.deprecated_instance_method()

        assert len(recwarn) == 1

    @deprecated()
    def deprecated_instance_method(self):
        pass
