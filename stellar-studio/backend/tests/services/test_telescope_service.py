# tests/services/test_telescope_service.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.telescope_service import TelescopeService
from app.domain.models.telescope import Telescope
from app.infrastructure.repositories.models.user import User, UserRole
from fastapi import HTTPException
from app.schemas.telescope import TelescopeCreate, TelescopeUpdate

@pytest.mark.asyncio
class TestTelescopeService:
    @pytest.fixture(autouse=True)
    def setup(self):
        """Configuration initiale synchrone"""
        self.db_session = MagicMock()
        self.telescope_service = TelescopeService(self.db_session)
        self.telescope_service.telescope_repository = AsyncMock()
        self.telescope_service.target_repository = AsyncMock()
        
        self.admin_user = User(
            id="admin1",
            email="admin@test.com",
            username="admin",
            role=UserRole.ADMIN,
            is_active=True
        )
        
        self.normal_user = User(
            id="user1",
            email="user@test.com",
            username="user",
            role=UserRole.USER,
            is_active=True
        )
        
        self.test_telescope_create = TelescopeCreate(
            name="Hubble",
            description="NASA Telescope",
            aperture=2.4,
            focal_length=57.6,
            location="LEO",
            instruments={"WFC3": "Wide Field Camera 3"}
        )
        
        self.test_telescope_update = TelescopeUpdate(
            name="Hubble Updated",
            description="Updated NASA Telescope",
            aperture=2.5,
            focal_length=None,
            location=None,
            instruments=None
        )

        
        self.db_telescope = Telescope(
            id="hst",
            name="Hubble",
            description="NASA Telescope",
            aperture=2.4,
            focal_length=57.6,
            location="LEO",
            instruments={"WFC3": "Wide Field Camera 3"},
            api_endpoint="/api/v1/telescopes/hst"
        )

    async def test_get_all_telescopes(self):
        """Test de récupération de tous les télescopes"""
        self.telescope_service.telescope_repository.list.return_value = [self.db_telescope]
        telescopes = await self.telescope_service.get_all_telescopes()
        assert len(telescopes) == 1
        assert telescopes[0].name == "Hubble"

    async def test_get_telescope_by_id(self):
        """Test de récupération d'un télescope par son ID"""
        self.telescope_service.telescope_repository.get_by_id.return_value = self.db_telescope
        telescope = await self.telescope_service.get_telescope("hst")
        assert telescope.id == "hst"
        assert telescope.name == "Hubble"

    async def test_get_telescope_not_found(self):
        """Test de récupération d'un télescope inexistant"""
        self.telescope_service.telescope_repository.get_by_id.return_value = None
        with pytest.raises(HTTPException) as exc:
            await self.telescope_service.get_telescope("invalid_id")
        assert exc.value.status_code == 404

    async def test_create_telescope_as_admin(self):
        """Test de création d'un télescope par un admin"""
        self.telescope_service.telescope_repository.create.return_value = self.db_telescope
        telescope = await self.telescope_service.create_telescope(self.test_telescope_create, self.admin_user)
        assert telescope.name == "Hubble"
        assert telescope.api_endpoint == "/api/v1/telescopes/hst"

    async def test_create_telescope_as_user(self):
        """Test de création d'un télescope par un utilisateur normal (doit échouer)"""
        with pytest.raises(HTTPException) as exc:
            await self.telescope_service.create_telescope(self.test_telescope_create, self.normal_user)
        assert exc.value.status_code == 403

    async def test_update_telescope_as_admin(self):
        """Test de mise à jour d'un télescope par un admin"""
        self.telescope_service.telescope_repository.get_by_id.return_value = self.db_telescope
        self.telescope_service.telescope_repository.update.return_value = self.db_telescope
        updated_telescope = await self.telescope_service.update_telescope("hst", self.test_telescope_update, self.admin_user)
        assert updated_telescope.name == "Hubble Updated"
        assert updated_telescope.aperture == 2.5

    async def test_update_telescope_not_found(self):
        """Test de mise à jour d'un télescope inexistant"""
        self.telescope_service.telescope_repository.get_by_id.return_value = None
        with pytest.raises(HTTPException) as exc:
            await self.telescope_service.update_telescope("invalid_id", self.test_telescope_update, self.admin_user)
        assert exc.value.status_code == 404

    async def test_update_telescope_as_user(self):
        """Test de mise à jour d'un télescope par un utilisateur normal (doit échouer)"""
        with pytest.raises(HTTPException) as exc:
            await self.telescope_service.update_telescope("hst", self.test_telescope_update, self.normal_user)
        assert exc.value.status_code == 403

    async def test_delete_telescope_as_admin(self):
        """Test de suppression d'un télescope par un admin"""
        self.telescope_service.telescope_repository.delete.return_value = True
        result = await self.telescope_service.delete_telescope("hst", self.admin_user)
        assert result is True

    async def test_delete_telescope_as_user(self):
        """Test de suppression d'un télescope par un utilisateur normal (doit échouer)"""
        with pytest.raises(HTTPException) as exc:
            await self.telescope_service.delete_telescope("hst", self.normal_user)
        assert exc.value.status_code == 403

    async def test_get_telescope_targets(self):
        """Test de récupération des cibles d'un télescope"""
        self.telescope_service.telescope_repository.get_by_id.return_value = self.db_telescope
        self.telescope_service.target_repository.get_by_telescope.return_value = []
        targets = await self.telescope_service.get_telescope_targets("hst")
        assert isinstance(targets, list)
