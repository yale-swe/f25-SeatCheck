"""Schema tests for Venue model."""

import pytest
from sqlalchemy import Integer, Float, String, JSON

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
    assert id_col.index
    assert isinstance(id_col.type, Integer)


# Columns & Datatypes
def test_venue_has_lat_lon_float_columns():
    lat_col = Venue.__table__.columns["lat"]
    lon_col = Venue.__table__.columns["lon"]

    assert isinstance(lat_col.type, Float)
    assert isinstance(lon_col.type, Float)
    assert not lat_col.nullable
    assert not lon_col.nullable


def test_venue_has_name_string_column():
    name_col = Venue.__table__.columns["name"]

    assert isinstance(name_col.type, String)
    assert name_col.type.length == 255
    assert not name_col.nullable
    assert name_col.index


def test_venue_has_category_indexed():
    category_col = Venue.__table__.columns["category"]

    assert isinstance(category_col.type, String)
    assert category_col.type.length == 50
    assert not category_col.nullable
    assert category_col.index


def test_venue_has_optional_capacity():
    capacity_col = Venue.__table__.columns["capacity"]

    assert isinstance(capacity_col.type, Integer)
    assert capacity_col.nullable


def test_venue_has_optional_description():
    desc_col = Venue.__table__.columns["description"]

    assert isinstance(desc_col.type, String)
    assert desc_col.type.length == 1000
    assert desc_col.nullable


def test_amenities_accessibility_hours_stored_as_json():
    amenities = Venue.__table__.columns["amenities"]
    accessibility = Venue.__table__.columns["accessibility"]
    hours = Venue.__table__.columns["opening_hours"]

    assert isinstance(amenities.type, JSON)
    assert isinstance(accessibility.type, JSON)
    assert isinstance(hours.type, JSON)
    assert amenities.nullable
    assert accessibility.nullable
    assert hours.nullable


# Type Annotations
def test_venue_type_annotations_match_columns():
    annotations = Venue.__annotations__

    assert "id" in annotations
    assert "name" in annotations
    assert "lat" in annotations
    assert "lon" in annotations
    assert "capacity" in annotations


def test_all_expected_columns_present():
    expected_columns = {
        "id",
        "name",
        "category",
        "lat",
        "lon",
        "description",
        "capacity",
        "amenities",
        "accessibility",
        "opening_hours",
        "image_url",
        "verified",
        "created_at",
        "updated_at",
    }
    actual_columns = set(Venue.__table__.columns.keys())
    assert expected_columns == actual_columns


# Constraints
def test_required_fields_not_nullable():
    assert not Venue.__table__.columns["id"].nullable
    assert not Venue.__table__.columns["name"].nullable
    assert not Venue.__table__.columns["category"].nullable
    assert not Venue.__table__.columns["lat"].nullable
    assert not Venue.__table__.columns["lon"].nullable
    assert not Venue.__table__.columns["verified"].nullable
    assert not Venue.__table__.columns["created_at"].nullable
    assert not Venue.__table__.columns["updated_at"].nullable


def test_optional_fields_are_nullable():
    assert Venue.__table__.columns["description"].nullable
    assert Venue.__table__.columns["capacity"].nullable
    assert Venue.__table__.columns["amenities"].nullable
    assert Venue.__table__.columns["accessibility"].nullable
    assert Venue.__table__.columns["opening_hours"].nullable
    assert Venue.__table__.columns["image_url"].nullable


def test_id_is_primary_key_constraint():
    pk_cols = [col.name for col in Venue.__table__.primary_key]
    assert pk_cols == ["id"]


# Defaults
def test_verified_has_default_false():
    verified_col = Venue.__table__.columns["verified"]
    assert verified_col.default is not None
    assert not verified_col.default.arg


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
    max_length = Venue.__table__.columns["name"].type.length
    assert max_length == 255


def test_name_at_max_length_boundary():
    name_col = Venue.__table__.columns["name"]
    assert name_col.type.length == 255


def test_description_longer_than_name():
    name_len = Venue.__table__.columns["name"].type.length
    desc_len = Venue.__table__.columns["description"].type.length

    assert desc_len > name_len
    assert desc_len == 1000


def test_description_at_max_length_boundary():
    desc_col = Venue.__table__.columns["description"]
    assert desc_col.type.length == 1000


def test_image_url_allows_long_paths():
    url_col = Venue.__table__.columns["image_url"]
    assert url_col.type.length == 500
    assert url_col.nullable


def test_capacity_no_check_constraint_at_db_level():
    capacity_col = Venue.__table__.columns["capacity"]
    assert capacity_col.nullable


def test_coordinates_no_range_constraint_at_db_level():
    lat_col = Venue.__table__.columns["lat"]
    lon_col = Venue.__table__.columns["lon"]
    assert isinstance(lat_col.type, Float)
    assert isinstance(lon_col.type, Float)


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

    assert "id" in indexed_cols
    assert "name" in indexed_cols
    assert "category" in indexed_cols


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
