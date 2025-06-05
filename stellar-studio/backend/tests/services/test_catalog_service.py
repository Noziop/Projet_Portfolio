import pytest
from typing import List, Optional, Dict

from app.services.catalog_service import CatalogService
from app.domain.models.target import Target # Changed
from app.domain.value_objects.coordinates import Coordinates # Changed

# Predefined data from CatalogService for easier reference in tests
# (Considered copying them directly, but decided against it to keep tests cleaner
# and less coupled to exact data if it changes for non-structural reasons.
# Tests will rely on the service's own data.)

class TestCatalogService:

    def test_get_targets_no_filters(self):
        """Test retrieving all targets without any filters."""
        targets = CatalogService.get_targets()
        assert isinstance(targets, list)
        assert len(targets) > 0 # Based on the service's predefined data
        # Check if all items are Target instances
        for target in targets:
            assert isinstance(target, Target)
            assert isinstance(target.coordinates, Coordinates) # Changed

    def test_get_targets_filter_by_telescope_hst(self):
        """Test filtering targets by telescope 'HST'."""
        targets = CatalogService.get_targets(telescope="HST")
        assert isinstance(targets, list)
        assert len(targets) > 0
        for target in targets:
            assert target.telescope_id == "HST" # Changed
            assert isinstance(target, Target)

    def test_get_targets_filter_by_telescope_jwst(self):
        """Test filtering targets by telescope 'JWST'."""
        targets = CatalogService.get_targets(telescope="JWST")
        assert isinstance(targets, list)
        assert len(targets) > 0
        for target in targets:
            assert target.telescope_id == "JWST" # Changed
            assert isinstance(target, Target)

    def test_get_targets_filter_by_object_type_nebula(self):
        """Test filtering targets by object_type 'nebula'."""
        targets = CatalogService.get_targets(object_type="nebula")
        assert isinstance(targets, list)
        assert len(targets) > 0
        for target in targets:
            assert target.object_type == "nebula"
            assert isinstance(target, Target)

    def test_get_targets_filter_by_object_type_cluster(self):
        """Test filtering targets by object_type 'cluster'."""
        targets = CatalogService.get_targets(object_type="cluster")
        assert isinstance(targets, list)
        assert len(targets) > 0
        for target in targets:
            assert target.object_type == "cluster"
            assert isinstance(target, Target)

    def test_get_targets_filter_by_object_type_galaxy(self):
        """Test filtering targets by object_type 'galaxy'."""
        targets = CatalogService.get_targets(object_type="galaxy")
        assert isinstance(targets, list)
        assert len(targets) > 0
        for target in targets:
            assert target.object_type == "galaxy"
            assert isinstance(target, Target)

    def test_get_targets_filter_by_telescope_and_object_type(self):
        """Test filtering targets by both telescope and object_type."""
        targets = CatalogService.get_targets(telescope="HST", object_type="nebula")
        assert isinstance(targets, list)
        assert len(targets) > 0
        for target in targets:
            assert target.telescope_id == "HST" # Changed
            assert target.object_type == "nebula"
            assert isinstance(target, Target)

    def test_get_targets_filter_no_results(self):
        """Test filtering that results in no targets (e.g., invalid combination or type)."""
        # Assuming there's no 'planet' object_type for HST in the predefined data
        targets = CatalogService.get_targets(telescope="HST", object_type="planet")
        assert isinstance(targets, list)
        assert len(targets) == 0

    def test_get_target_by_id_existing(self):
        """Test retrieving an existing target by its ID."""
        # Using a known ID from the predefined data
        known_hst_target_id = "M42_HST"
        target = CatalogService.get_target_by_id(known_hst_target_id)
        assert target is not None
        assert isinstance(target, Target)
        assert target.id == known_hst_target_id
        assert target.name == "Orion Nebula" # Verify some known data
        assert target.telescope_id == "HST" # Changed

        known_jwst_target_id = "M16_JWST"
        target = CatalogService.get_target_by_id(known_jwst_target_id)
        assert target is not None
        assert isinstance(target, Target)
        assert target.id == known_jwst_target_id
        assert target.name == "Eagle Nebula"
        assert target.telescope_id == "JWST" # Changed


    def test_get_target_by_id_non_existing(self):
        """Test retrieving a non-existing target by ID."""
        target = CatalogService.get_target_by_id("NON_EXISTING_ID")
        assert target is None

    def test_get_available_processes_existing_target_nebula(self):
        """Test getting available processes for an existing nebula target."""
        # Using a known nebula ID
        target_id = "M42_HST"
        processes = CatalogService.get_available_processes(target_id)
        assert processes is not None
        assert isinstance(processes, dict)
        assert processes["target"] == "Orion Nebula"
        assert isinstance(processes["available_processes"], list)
        assert "abe" in processes["available_processes"] # Based on _available_processes
        assert "hoo" in processes["available_processes"]
        assert "sho" in processes["available_processes"]

    def test_get_available_processes_existing_target_galaxy(self):
        """Test getting available processes for an existing galaxy target."""
        target_id = "M31_HST"
        processes = CatalogService.get_available_processes(target_id)
        assert processes is not None
        assert processes["target"] == "Andromeda Galaxy"
        assert "abe" in processes["available_processes"]
        assert "contrast" in processes["available_processes"]
        assert "luminance" in processes["available_processes"]

    def test_get_available_processes_existing_target_cluster(self):
        """Test getting available processes for an existing cluster target."""
        target_id = "M45_HST"
        processes = CatalogService.get_available_processes(target_id)
        assert processes is not None
        assert processes["target"] == "Pleiades"
        assert "abe" in processes["available_processes"]
        assert "align" in processes["available_processes"]
        assert "contrast" in processes["available_processes"]

    def test_get_available_processes_non_existing_target(self):
        """Test getting available processes for a non-existing target."""
        processes = CatalogService.get_available_processes("NON_EXISTING_ID")
        assert processes is None

    def test_get_targets_telescope_invalid_type(self):
        """Test get_targets with an invalid telescope type (should be Literal)."""
        # This test primarily checks if the type hints (Literal) are conceptually working,
        # though pytest won't enforce Literal at runtime without type checking tools.
        # The behavior should be an empty list as no targets match.
        targets = CatalogService.get_targets(telescope="INVALID_SCOPE")
        assert isinstance(targets, list)
        assert len(targets) == 0

    def test_get_targets_object_type_invalid_type(self):
        """Test get_targets with an invalid object_type (should be Literal)."""
        targets = CatalogService.get_targets(object_type="INVALID_TYPE")
        assert isinstance(targets, list)
        assert len(targets) == 0

    # Example of a more specific check if data integrity is paramount for a particular target
    def test_specific_target_data_integrity_m16_hst(self):
        """Test specific data fields of a known target M16_HST."""
        target = CatalogService.get_target_by_id("M16_HST")
        assert target is not None
        assert target.name == "Eagle Nebula"
        assert target.telescope_id == "HST" # Changed
        assert target.object_type == "nebula"
        assert target.description == "Famous for the Pillars of Creation"
        assert target.coordinates.ra == "18 18 48"
        assert target.coordinates.dec == "-13 49 00"

    def test_specific_target_data_integrity_hcg92_jwst(self):
        """Test specific data fields of a known target HCG92_JWST."""
        target = CatalogService.get_target_by_id("HCG92_JWST")
        assert target is not None
        assert target.name == "Stephan's Quintet"
        assert target.telescope_id == "JWST" # Changed
        assert target.object_type == "galaxy"
        assert target.description == "Compact group of five interacting galaxies"
        assert target.coordinates.ra == "22 35 58"
        assert target.coordinates.dec == "+33 57 36"

    def test_available_processes_consistency(self):
        """Check that all object types in _targets have corresponding entries in _available_processes."""
        all_target_object_types = set()
        for _, targets_list in CatalogService._targets.items():
            for target in targets_list:
                all_target_object_types.add(target.object_type)

        for obj_type in all_target_object_types:
            assert obj_type in CatalogService._available_processes, f"Object type '{obj_type}' found in targets but not in available_processes."

    def test_target_ids_are_unique_across_telescopes(self):
        """Verify that target IDs are unique even if names are similar across different telescopes."""
        all_ids = []
        for _, targets_list in CatalogService._targets.items():
            for target in targets_list:
                all_ids.append(target.id)

        assert len(all_ids) == len(set(all_ids)), "Target IDs are not unique across all telescopes."

    # Test for a target that exists for one telescope but not another (e.g. M42 only for HST)
    def test_get_target_by_id_hst_specific(self):
        m42_hst = CatalogService.get_target_by_id("M42_HST")
        assert m42_hst is not None
        assert m42_hst.telescope_id == "HST" # Changed

        # There is no M42_JWST in the predefined data.
        m42_jwst = CatalogService.get_target_by_id("M42_JWST")
        assert m42_jwst is None
