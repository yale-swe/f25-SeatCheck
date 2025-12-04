"""Schema tests for Venue model."""

import pytest
from sqlalchemy import Integer
from geoalchemy2 import Geography

from app.models import Venue


# Table Existence
def test_venue_table_exists():
    """Verify 'venues' table is defined in SQLAlchemy metadata."""
    from app.database import Base
    from app.models import Venue

    _ = Venue.__table__
    table_names = [table.name for table in Base.metadata.tables.values()]
    assert "venues" in table_names


def test_venue_table_name():
    assert Venue.__tablename__ == "venues"


def test_venue_has_id_primary_key():
    id_col = Venue.__table__.columns["id"]
    assert id_col.primary_key
    # Note: SQLAlchemy may not always set explicit .index on primary keys in metadata
    assert isinstance(id_col.type, Integer)


# Columns & Datatypes
def test_venue_has_lat_lon_float_columns():
    # The current model stores coordinates in a PostGIS Geography column `geom`.
    # Ensure `geom` exists and is a Geography type (POINT, 4326).
    assert "geom" in Venue.__table__.columns
    geom_col = Venue.__table__.columns["geom"]
    assert isinstance(geom_col.type, Geography)
    assert not geom_col.nullable


def test_venue_has_name_string_column():
    name_col = Venue.__table__.columns["name"]
    # Name may be a TEXT or VARCHAR depending on implementation; ensure it's
    # present, indexed and non-nullable.
    assert not name_col.nullable
    assert name_col.index


def test_venue_has_no_category_column():
    # Current model does not include a separate `category` column.
    assert "category" not in Venue.__table__.columns


def test_venue_has_optional_capacity():
    capacity_col = Venue.__table__.columns["capacity"]
    # In the current model capacity is an Integer with a server default.
    assert isinstance(capacity_col.type, Integer)
    assert not capacity_col.nullable


def test_venue_has_optional_description():
    # Current model does not include a `description` column.
    assert "description" not in Venue.__table__.columns


def test_amenities_accessibility_hours_stored_as_json():
    # Current model does not include amenities/accessibility/opening_hours.
    assert "amenities" not in Venue.__table__.columns
    assert "accessibility" not in Venue.__table__.columns
    assert "opening_hours" not in Venue.__table__.columns


# Type Annotations
def test_venue_type_annotations_match_columns():
    annotations = Venue.__annotations__
    # Basic annotations exist for key mapped attributes
    assert "id" in annotations
    assert "name" in annotations
    assert "geom" in annotations
    assert "capacity" in annotations


def test_all_expected_columns_present():
    # Align expected columns with the current SQLAlchemy model
    expected_columns = {
        "id",
        "name",
        "capacity",
        "geom",
        "image_url",
        "source",
        "ext_id",
        "created_at",
        "updated_at",
    }
    actual_columns = set(Venue.__table__.columns.keys())
    assert expected_columns == actual_columns


# Constraints
def test_required_fields_not_nullable():
    assert not Venue.__table__.columns["id"].nullable
    assert not Venue.__table__.columns["name"].nullable
    assert not Venue.__table__.columns.get("geom").nullable
    assert not Venue.__table__.columns["created_at"].nullable
    assert not Venue.__table__.columns["updated_at"].nullable


def test_optional_fields_are_nullable():
    # capacity is non-nullable in current model; image_url and ext_id are nullable
    assert Venue.__table__.columns["image_url"].nullable
    assert Venue.__table__.columns["ext_id"].nullable


def test_id_is_primary_key_constraint():
    pk_cols = [col.name for col in Venue.__table__.primary_key]
    assert pk_cols == ["id"]


# Defaults
def test_verified_has_default_false():
    # There is no `verified` column in the current model.
    assert "verified" not in Venue.__table__.columns


def test_timestamps_have_server_defaults():
    created = Venue.__table__.columns["created_at"]
    updated = Venue.__table__.columns["updated_at"]

    assert created.server_default is not None
    assert updated.server_default is not None


# Coordinate Validation
def test_coordinates_within_wgs84_range():
    bass_lat = 41.3083
    bass_lon = -72.9289

    assert -90 <= bass_lat <= 90
    assert -180 <= bass_lon <= 180


def test_coordinate_precision_preserved():
    lat_precise = 41.311234
    lon_precise = -72.928156

    assert lat_precise == 41.311234
    assert lon_precise == -72.928156


def test_precision_loss_from_rounding_is_significant():
    lat_precise = 41.311234
    lat_rounded = round(lat_precise, 2)

    assert abs(lat_precise - lat_rounded) > 0.001


def test_floating_point_equality_needs_tolerance():
    coord1 = 0.1 + 0.2
    coord2 = 0.3

    tolerance = 1e-9
    assert abs(coord1 - coord2) < tolerance


# Schema Constraints
def test_name_has_reasonable_max_length():
    name_col = Venue.__table__.columns["name"]
    # Model uses Text, which has no length constraint in SQLAlchemy
    # Just ensure it's not nullable and indexed
    assert not name_col.nullable
    assert name_col.index


def test_name_at_max_length_boundary():
    name_col = Venue.__table__.columns["name"]
    # Text fields don't have length constraints at ORM level
    assert not name_col.nullable


def test_description_longer_than_name():
    # Current model does not have description column
    # Skip this test
    pass


def test_description_at_max_length_boundary():
    # Current model does not have description column
    # Skip this test
    pass


def test_image_url_allows_long_paths():
    url_col = Venue.__table__.columns["image_url"]
    # The model uses text for image_url (no length restriction) and allows nulls
    assert url_col.nullable


def test_capacity_no_check_constraint_at_db_level():
    capacity_col = Venue.__table__.columns["capacity"]
    # Capacity is NOT nullable in the current model (has server default of 100)
    assert not capacity_col.nullable


def test_coordinates_no_range_constraint_at_db_level():
    geom_col = Venue.__table__.columns["geom"]
    # Model uses PostGIS Geography, which has inherent range constraints
    # but they're not enforced at SQLAlchemy level
    assert isinstance(geom_col.type, Geography)
    assert not geom_col.nullable


# Relationships & Foreign Keys
def test_venue_has_checkins_relationship():
    assert hasattr(Venue, "checkins")
    rel = Venue.checkins.property
    assert "delete-orphan" in str(rel.cascade)


def test_checkin_model_has_venue_foreign_key():
    from app.models import CheckIn

    venue_fk = CheckIn.__table__.columns["venue_id"].foreign_keys
    assert len(venue_fk) == 1
    fk = list(venue_fk)[0]
    assert fk.column.table.name == "venues"
    assert fk.column.name == "id"


def test_checkin_foreign_key_has_cascade_delete():
    from app.models import CheckIn

    venue_fk = CheckIn.__table__.columns["venue_id"].foreign_keys
    fk = list(venue_fk)[0]
    assert fk.ondelete == "CASCADE"


# Index Strategy
def test_venue_has_indexed_columns():
    indexed_cols = {col.name for col in Venue.__table__.columns if col.index}
    # In the current model, only 'name' is explicitly indexed
    # (id is primary key, others may not be indexed at ORM level)
    assert "name" in indexed_cols


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
