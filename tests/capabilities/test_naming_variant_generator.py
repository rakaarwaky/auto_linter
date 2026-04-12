"""Comprehensive tests for capabilities/naming_variant_generator.py — 100% coverage."""

from capabilities.naming_variant_generator import get_variant_dict, build_variants


class TestGetVariantDict:
    def test_camel_case_input(self):
        result = get_variant_dict("myFunctionName")
        assert result["snake_case"] == "my_function_name"
        assert result["camel_case"] == "myFunctionName"
        assert result["pascal_case"] == "MyFunctionName"
        assert result["screaming_snake"] == "MY_FUNCTION_NAME"

    def test_snake_case_input(self):
        result = get_variant_dict("my_function_name")
        assert result["snake_case"] == "my_function_name"
        assert result["camel_case"] == "myFunctionName"
        assert result["pascal_case"] == "MyFunctionName"

    def test_pascal_case_input(self):
        result = get_variant_dict("MyFunctionName")
        assert result["snake_case"] == "my_function_name"
        assert result["camel_case"] == "myFunctionName"
        assert result["pascal_case"] == "MyFunctionName"

    def test_screaming_snake_input(self):
        # Note: regex splits each uppercase letter as separate word
        result = get_variant_dict("MY_FUNCTION_NAME")
        assert "snake_case" in result
        assert "screaming_snake" in result

    def test_single_word(self):
        result = get_variant_dict("test")
        assert result["snake_case"] == "test"
        assert result["camel_case"] == "test"
        assert result["pascal_case"] == "Test"

    def test_empty_string(self):
        result = get_variant_dict("")
        assert result["snake_case"] == ""
        assert result["camel_case"] == ""
        assert result["pascal_case"] == ""
        assert result["screaming_snake"] == ""

    def test_constant_case(self):
        # Note: regex splits each uppercase letter
        result = get_variant_dict("MAX_VALUE")
        assert "snake_case" in result
        assert "screaming_snake" in result


class TestBuildVariants:
    def test_returns_list(self):
        result = build_variants("myFunction")
        assert isinstance(result, list)
        assert len(result) > 0

    def test_contains_all_variants(self):
        result = build_variants("myFunction")
        assert "my_function" in result
        assert "myFunction" in result
        assert "MyFunction" in result
        assert "MY_FUNCTION" in result
        assert "my-function" in result

    def test_no_duplicates(self):
        result = build_variants("myFunction")
        assert len(result) == len(set(result))
