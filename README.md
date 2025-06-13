# Home Assistant AirControlBase Integration

This is a custom integration for Home Assistant to control AirControlBase air conditioning devices.

## Features

- Control your AirControlBase AC devices through Home Assistant
- Support for temperature control
- Multiple operation modes (Cool, Heat, Dry, Fan)
- Fan speed control
- Swing mode control
- Automatic device discovery
- Real-time status updates

## Installation

1. Download this repository
2. Copy the `custom_components/aircontrolbase` directory to your Home Assistant's `custom_components` directory
3. Restart Home Assistant
4. Go to Configuration > Integrations
5. Click the "+ Add Integration" button
6. Search for "AirControlBase"
7. Enter your AirControlBase email and password

## Configuration

The integration requires the following configuration:

- Email: Your AirControlBase account email
- Password: Your AirControlBase account password

## Support

If you encounter any issues or have questions, please open an issue in this repository.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Running Tests

To run the test suite, first install the dependencies:

```
pip install -r requirements.txt
```

Set your AirControlBase credentials as environment variables:

```
export AIRCONTROLBASE_EMAIL="email@email.com"
export AIRCONTROLBASE_PASSWORD="password"
```

Then run the tests with:

```
pytest -s tests/test_aircontrolbase.py
```

The `-s` flag ensures you see all print output from the tests. # homeassistant-aircontrolbase
# homeassistant-aircontrolbase
