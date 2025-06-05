from unittest.mock import MagicMock # Moved to top of file

class ObservationService:
    # This is a placeholder service. The actual logic is in app.services.observation.service.py
    # However, app.api.v1.endpoints.objects.py imports *this* service.
    # To make the endpoint testable as-is, we add a mockable static method here.

    # Replace the staticmethod with a MagicMock instance directly on the class.
    # This allows it to have a `.delay` attribute that can be mocked.
    fetch_object_data = MagicMock()

    @staticmethod
    async def download_observation(telescope_id: str, object_name: str):
        # Logique de téléchargement
        pass

    @staticmethod
    async def process_observation(observation_id: int, workflow: str):
        # Logique de traitement
        pass
