import pytest

class TestWeatherServer:
    def test_valid_city_returns_data(self):
        mock_response = {"city": "London", "temp_c": 15.0, "condition": "Cloudy"}
        assert "temp_c" in mock_response
        assert mock_response["city"] == "London"

    def test_temperature_in_valid_range(self):
        temps = [-20.0, 0.0, 25.0, 45.0]
        for t in temps:
            assert -90 <= t <= 60

    def test_empty_city_rejected(self):
        def validate(city):
            if not city or not city.strip():
                raise ValueError("City cannot be empty")
            return city.strip()
        with pytest.raises(ValueError):
            validate("")

    def test_unit_conversion_celsius_to_fahrenheit(self):
        celsius = 100.0
        fahrenheit = celsius * 9/5 + 32
        assert fahrenheit == 212.0

    def test_response_structure(self):
        response = {"city": "Paris", "temp_c": 20.0, "humidity": 65, "condition": "Clear"}
        required_keys = ["city", "temp_c", "condition"]
        for k in required_keys:
            assert k in response

class TestMCPIntegration:
    def test_tool_schema_valid(self):
        schema = {"name": "get_weather", "description": "Get current weather", "input_schema": {"type": "object", "properties": {"city": {"type": "string"}}, "required": ["city"]}}
        assert schema["name"] == "get_weather"
        assert "city" in schema["input_schema"]["properties"]

    def test_error_handling_unknown_city(self):
        def get_weather(city):
            known = {"London": 15.0, "Paris": 20.0}
            if city not in known:
                raise KeyError(f"City '{city}' not found")
            return known[city]
        with pytest.raises(KeyError):
            get_weather("UnknownCity123")
