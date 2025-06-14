import json
import logging

_LOGGER = logging.getLogger(__name__)

class YourClassName:
    # ... your other methods ...

    async def control_device(self, control):
        # Fetch the latest device details
        device_details = await self.getDetails()

        # Filter the device details by allowed fields
        allowed_fields = [
            "power", "mode", "setTemp", "wind", "swing", "lock", "factTemp",
            "modeLockValue", "coolLockValue", "heatLockValue", "windLockValue", "unlock", "id"
        ]
        filtered_device = {key: device_details.get(key) for key in allowed_fields if key in device_details}

        # Store the filtered device details for future comparisons
        self._last_device_state = filtered_device

        # Ensure power is 'y' if mode is changed to 'auto', 'heat', or 'cool'
        if "mode" in control and control["mode"] in ["auto", "heat", "cool"]:
            control["power"] = "y"

        # Calculate the diff for the operation (changes compared to the last state)
        operation_diff = {key: value for key, value in control.items() if self._last_device_state.get(key) != value}

        # Convert control and operation to JSON strings for form encoding
        form_data = {
            "userId": self._user_id,
            "control": json.dumps(self._last_device_state),  # Send all fields from the last state
            "operation": json.dumps(operation_diff),
        }

        _LOGGER.debug("Sending control request with data: %s", form_data)

        # Validate the mode field in the filtered control data
        if "mode" in control and control["mode"] not in ["auto", "heat", "cool"]:
            raise ValueError(f"Invalid mode: {control['mode']}. Allowed values are 'auto', 'heat', 'cool'.")

        # ... the rest of your method ...